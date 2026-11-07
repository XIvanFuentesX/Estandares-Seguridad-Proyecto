param(
    # Compose previo a la actualización (local/rollback/compose.yaml.pre-upgrade-*.bak).
    [Parameter(Mandatory = $true)][string]$RollbackCompose,
    # Sin -Execute sólo valida prerrequisitos (modo verificación); con -Execute revierte.
    [switch]$Execute
)

# Reversión NO destructiva de db/identity-db a postgres:16-alpine: no borra volúmenes ni datos.
# El binario postgres y el formato de datos son idénticos entre imágenes, por lo que basta con
# recrear los contenedores con el compose previo. Restaurar las copias en frío de
# local/rollback/volumes/ sobre los volúmenes NO es parte de este script: requiere autorización.
$ErrorActionPreference = "Continue"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPath = Join-Path $root "local"
$compose = Join-Path $localPath "compose.yaml"
$evidencePath = Join-Path $root "evidencias\postgres-upgrade"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$checks = [ordered]@{}

function Wait-Healthy([string[]]$Services, [int]$TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $rows = @(docker compose -f $compose ps $Services --format json | ConvertFrom-Json)
        if (@($rows | Where-Object Health -eq "healthy").Count -eq $Services.Count) { return $true }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    return $false
}

Push-Location $localPath
try {
    $checks.rollback_compose_exists = Test-Path $RollbackCompose
    docker compose --project-directory $localPath -f $RollbackCompose config --quiet
    $checks.rollback_compose_valid = ($LASTEXITCODE -eq 0)
    $checks.rollback_compose_uses_official_image = ((Get-Content $RollbackCompose -Raw) -match "(?m)^  db:\s*\r?\n    image: postgres:16-alpine")
    docker image inspect postgres:16-alpine | Out-Null
    $checks.previous_image_available = ($LASTEXITCODE -eq 0)
    $checks.volumes_present = (@(docker volume ls -q --filter name=local_pgdata --filter name=local_identity_data).Count -ge 2)
    $ready = -not ($checks.Values -contains $false)
    if (-not $Execute) {
        Write-Output "VERIFICACION: rollback_preparado=$ready $($checks | ConvertTo-Json -Compress)"
    } else {
        if (-not $ready) { throw "Prerrequisitos de reversión incompletos; no se ejecuta." }
        Copy-Item $compose (Join-Path $localPath "rollback\compose.yaml.antes-rollback-$stamp.bak")
        Copy-Item -Force $RollbackCompose $compose
        docker compose -f $compose stop api keycloak | Out-Null
        docker compose -f $compose up -d --no-deps --force-recreate db identity-db | Out-Null
        if (-not (Wait-Healthy @("db", "identity-db") 120)) { throw "Las bases no alcanzaron healthy tras la reversión; detener y escalar." }
        docker compose -f $compose up -d --no-deps keycloak api | Out-Null
        docker compose -f $compose --profile backup-scheduled up -d --no-deps academic-backup-scheduler identity-backup-scheduler | Out-Null
        $checks.services_healthy = (Wait-Healthy @("proxy", "db", "identity-db", "keycloak", "api") 300)
        Write-Output "REVERTIDO: servicios_healthy=$($checks.services_healthy). Ejecute huella_datos_postgres.ps1 -CompareTo <huella previa>, pruebas_identidad.py y pruebas_locales.py."
    }
} finally {
    Pop-Location
    [ordered]@{ timestamp = (Get-Date).ToString("o"); mode = $(if ($Execute) { "execute" } else { "verify" }); checks = $checks } |
        ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $evidencePath "rollback-$(if ($Execute) {'ejecucion'} else {'verificacion'})-$stamp.json")
}
