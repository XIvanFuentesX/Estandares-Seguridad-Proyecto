param(
    # Huella previa generada por huella_datos_postgres.ps1 -Label pre-upgrade (obligatoria).
    [Parameter(Mandatory = $true)][string]$PreFingerprint,
    # Copia del compose previo (procedimiento de reversión).
    [Parameter(Mandatory = $true)][string]$RollbackCompose
)

# Actualiza db e identity-db a local-postgres-hardened:16 sin borrar volúmenes.
# Ante fallo de salud o integridad revierte automáticamente al compose previo.
# Docker escribe progreso en stderr; los fallos se detectan con $LASTEXITCODE y throw explícito.
$ErrorActionPreference = "Continue"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPath = Join-Path $root "local"
$compose = Join-Path $localPath "compose.yaml"
$evidencePath = Join-Path $root "evidencias\postgres-upgrade"
$volumeBackupPath = Join-Path $localPath "rollback\volumes"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$log = [System.Collections.Generic.List[object]]::new()
$started = Get-Date

function Step([string]$Name, [string]$Result, [string]$Detail = "") {
    $log.Add([ordered]@{ time = (Get-Date).ToString("o"); step = $Name; result = $Result; detail = $Detail })
    Write-Output "[$Result] $Name $Detail"
}

function Wait-Healthy([string[]]$Services, [int]$TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $rows = @(docker compose -f $compose ps $Services --format json | ConvertFrom-Json)
        $healthy = @($rows | Where-Object Health -eq "healthy").Count
        if ($healthy -eq $Services.Count) { return $true }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    return $false
}

function Set-HardenedImage([string]$Text) {
    foreach ($service in @("db", "identity-db")) {
        $pattern = "(?ms)(^  $service`:\r?\n)(.*?)(?=^\S|^  \S)"
        $match = [regex]::Match($Text, $pattern)
        if (-not $match.Success) { throw "No se encontró el servicio $service en compose.yaml." }
        $block = $match.Groups[2].Value
        $new = $block.Replace("    image: postgres:16-alpine`n", "    image: local-postgres-hardened:16`n    build: ./postgres-hardened`n    user: `"70:70`"`n")
        $new = $new.Replace("    cap_add: [CHOWN, DAC_OVERRIDE, FOWNER, SETGID, SETUID]`n", "")
        if ($new -eq $block) { throw "No se pudo modificar $service (¿ya actualizado?)." }
        $Text = $Text.Substring(0, $match.Groups[2].Index) + $new + $Text.Substring($match.Groups[2].Index + $block.Length)
    }
    return $Text
}

$rolledBack = $false
$success = $false
Push-Location $localPath
try {
    # 1. Prerrequisitos
    if (-not (Test-Path $PreFingerprint)) { throw "Falta la huella previa." }
    if (-not (Test-Path $RollbackCompose)) { throw "Falta la copia del compose previo." }
    docker image inspect local-postgres-hardened:16 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "La imagen endurecida no está disponible." }
    $hardVersion = (docker run --rm --network none --entrypoint postgres local-postgres-hardened:16 --version) -join ""
    $curVersion = (docker run --rm --network none --entrypoint postgres postgres:16-alpine --version) -join ""
    if ($hardVersion -ne $curVersion) { throw "Versiones distintas: $hardVersion vs $curVersion" }
    $binHashes = foreach ($image in "postgres:16-alpine", "local-postgres-hardened:16") {
        (docker run --rm --network none --entrypoint sha256sum $image /usr/local/bin/postgres) -split '\s+' | Select-Object -First 1
    }
    if ($binHashes[0] -ne $binHashes[1]) { throw "El binario postgres difiere entre imágenes." }
    Step "prerrequisitos" "success" "$hardVersion; binario postgres idéntico ($($binHashes[0].Substring(0,16))…)"

    # 2. Compose modificado (validado antes de aplicarlo)
    $original = [IO.File]::ReadAllText($compose)
    $updated = Set-HardenedImage ($original -replace "`r`n", "`n")
    $candidate = Join-Path $localPath "compose.candidate.yaml"
    [IO.File]::WriteAllText($candidate, $updated, [Text.UTF8Encoding]::new($false))
    docker compose -f $candidate config --quiet
    if ($LASTEXITCODE -ne 0) { Remove-Item $candidate; throw "El compose candidato no es válido." }

    # 3. Parada controlada: dependientes primero, luego bases
    docker compose -f $compose stop api keycloak | Out-Null
    docker compose -f $compose --profile backup-scheduled stop academic-backup-scheduler identity-backup-scheduler | Out-Null
    docker compose -f $compose stop db identity-db | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron detener las bases de forma ordenada." }
    Step "parada_controlada" "success" "api, keycloak, schedulers, db, identity-db detenidos"

    # 4. Copia en frío de los volúmenes (bases detenidas = copia consistente)
    New-Item -ItemType Directory -Force -Path $volumeBackupPath | Out-Null
    foreach ($volume in "local_pgdata", "local_identity_data") {
        docker run --rm --network none --user 70:70 -v "${volume}:/data:ro" -v "${volumeBackupPath}:/out" `
            --entrypoint tar local-postgres-hardened:16 -czf "/out/$volume-$stamp.tgz" -C /data .
        $archive = Join-Path $volumeBackupPath "$volume-$stamp.tgz"
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $archive) -or (Get-Item $archive).Length -lt 1024) { throw "Falló la copia en frío de $volume." }
        $hash = (Get-FileHash -Algorithm SHA256 $archive).Hash
        [IO.File]::WriteAllText("$archive.sha256", "$($hash.ToLowerInvariant())  $volume-$stamp.tgz`n")
        Step "copia_frio_$volume" "success" "$volume-$stamp.tgz bytes=$((Get-Item $archive).Length) sha256=$hash"
    }

    # 5. Aplicar compose y recrear sólo las bases (sin -v: los volúmenes se conservan)
    Move-Item -Force $candidate $compose
    $timer = [Diagnostics.Stopwatch]::StartNew()
    docker compose -f $compose up -d --no-deps --force-recreate db identity-db | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Wait-Healthy @("db", "identity-db") 120)) { throw "Las bases no alcanzaron healthy con la imagen endurecida." }
    Step "bases_recreadas" "success" "healthy en $([math]::Round($timer.Elapsed.TotalSeconds,1)) s"

    # 6. Dependientes
    docker compose -f $compose up -d --no-deps keycloak api | Out-Null
    if (-not (Wait-Healthy @("keycloak") 240) -or -not (Wait-Healthy @("api") 120)) { throw "Keycloak o API no recuperaron healthy." }
    docker compose -f $compose --profile backup-scheduled up -d --no-deps academic-backup-scheduler identity-backup-scheduler | Out-Null
    if (-not (Wait-Healthy @("proxy", "db", "identity-db", "keycloak", "api") 60)) { throw "No todos los servicios están healthy." }
    $timer.Stop()
    Step "servicios_recuperados" "success" "cinco servicios healthy; interrupción total $([math]::Round($timer.Elapsed.TotalSeconds,1)) s desde la recreación"

    # 7. Usuario efectivo y ausencia de gosu en los contenedores en ejecución
    foreach ($c in "local-db-1", "local-identity-db-1") {
        $info = docker inspect $c | ConvertFrom-Json
        $uid = (docker exec $c id -u) -join ""
        $gosu = (docker exec $c sh -c "command -v gosu || echo absent") -join ""
        if ($info.Config.Image -ne "local-postgres-hardened:16" -or $uid -ne "70" -or $gosu -ne "absent") { throw "$c no cumple imagen/UID/gosu." }
        Step "verificacion_$c" "success" "image=$($info.Config.Image) uid=$uid gosu=$gosu"
    }

    # 8. Integridad de datos frente a la huella previa
    $out = & (Join-Path $PSScriptRoot "huella_datos_postgres.ps1") -Label post-upgrade -CompareTo $PreFingerprint 2>&1 | Out-String
    if ($out -notmatch "OK:") { throw "Integridad no confirmada: $out" }
    Step "integridad_datos" "success" (($out.Trim() -split "`n")[-1])
    $success = $true
} catch {
    Step "error" "failure" $_.Exception.Message
    # Reversión automática no destructiva: compose previo + recreación sin borrar volúmenes.
    if (Test-Path $RollbackCompose) {
        Copy-Item -Force $RollbackCompose $compose
        docker compose -f $compose up -d --no-deps --force-recreate db identity-db | Out-Null
        Wait-Healthy @("db", "identity-db") 120 | Out-Null
        docker compose -f $compose up -d --no-deps keycloak api | Out-Null
        docker compose -f $compose --profile backup-scheduled up -d --no-deps academic-backup-scheduler identity-backup-scheduler | Out-Null
        $rolledBack = $true
        Step "rollback_automatico" "executed" "compose previo restaurado; volúmenes intactos"
    }
} finally {
    $candidate = Join-Path $localPath "compose.candidate.yaml"
    if (Test-Path $candidate) { Remove-Item $candidate }
    Pop-Location
    $report = [ordered]@{
        timestamp = $started.ToString("o"); elapsed_seconds = [math]::Round(((Get-Date) - $started).TotalSeconds, 1)
        result = $(if ($success) { "success" } elseif ($rolledBack) { "rolled_back" } else { "failure" })
        services_updated = @("db", "identity-db"); previous_image = "postgres:16-alpine"; new_image = "local-postgres-hardened:16"
        volumes_preserved = @("local_pgdata", "local_identity_data"); rollback_compose = (Split-Path $RollbackCompose -Leaf)
        steps = $log
    }
    $report | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $evidencePath "actualizacion-$stamp.json")
}
if (-not $success) { throw "Actualización no completada (ver evidencias\postgres-upgrade\actualizacion-$stamp.json)." }
