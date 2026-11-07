param(
    [ValidateSet("api", "keycloak")]
    [string]$Service = "api"
)

# Continue: Docker escribe progreso en stderr; los fallos se detectan con $LASTEXITCODE y throw explícito.
$ErrorActionPreference = "Continue"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPath = Join-Path $root "local"
$evidencePath = Join-Path $root "evidencias\recovery"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$recovered = $false

$definitions = @{
    api = @{
        Url = "https://localhost:8443/health"; Container = "local-api-1"; Timeout = 60
        Scenario = "api_container_interruption"; IntegrityService = "db"; EnvUser = "DB_USER"; EnvDb = "DB_NAME"
        Query = "SELECT count(*) FROM cursos"; Minimum = 3; Metric = "database_course_count"; Prefix = "continuidad-api"
    }
    keycloak = @{
        Url = "https://localhost:8443/auth/realms/uvcg/.well-known/openid-configuration"; Container = "local-keycloak-1"; Timeout = 240
        Scenario = "iam_keycloak_interruption"; IntegrityService = "identity-db"; EnvUser = "KC_DB_USER"; EnvDb = "KC_DB_NAME"
        Query = "SELECT count(*) FROM user_entity"; Minimum = 4; Metric = "identity_user_count"; Prefix = "continuidad-iam"
    }
}
$definition = $definitions[$Service]

function Get-HealthCode {
    $value = & curl.exe --insecure --silent --max-time 5 --output NUL --write-out "%{http_code}" $definition.Url
    return [int]$value
}

Push-Location $localPath
try {
    $before = Get-HealthCode
    if ($before -ne 200) { throw "La línea base de $Service no respondió 200." }

    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    docker compose -f compose.yaml stop $Service | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "No se pudo detener $Service para la prueba." }
    Start-Sleep -Seconds 2
    $during = Get-HealthCode
    # 0 = sin respuesta en 5 s (curl timeout): Nginx espera al upstream caído; también es interrupción observada.
    if ($during -notin @(0, 502, 503, 504)) {
        throw "La interrupción no fue observada por Nginx; código: $during"
    }

    docker compose -f compose.yaml up -d --no-deps $Service | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "No se pudo iniciar $Service durante la recuperación." }
    $deadline = (Get-Date).AddSeconds($definition.Timeout)
    do {
        $health = (docker inspect $definition.Container | ConvertFrom-Json).State.Health.Status
        if ($health -eq "healthy" -and (Get-HealthCode) -eq 200) { $recovered = $true; break }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $deadline)
    $timer.Stop()
    if (-not $recovered) { throw "$Service no se recuperó dentro de $($definition.Timeout) segundos." }

    $envValues = @{}
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') { $envValues[$matches[1]] = $matches[2] }
    }
    $count = docker compose -f compose.yaml exec -T $definition.IntegrityService psql `
        -U $envValues[$definition.EnvUser] -d $envValues[$definition.EnvDb] -Atc $definition.Query
    if ($LASTEXITCODE -ne 0 -or [int]$count -lt $definition.Minimum) { throw "Falló la integridad posterior." }

    $evidence = [ordered]@{
        timestamp = (Get-Date).ToString("o")
        scenario = $definition.Scenario
        service = $Service
        baseline_http_status = $before
        interruption_http_status = $(if ($during -eq 0) { "timeout_5s" } else { $during })
        recovery_http_status = 200
        recovery_seconds = [math]::Round($timer.Elapsed.TotalSeconds, 3)
        $definition.Metric = [int]$count
        scope_warning = "Medición de laboratorio; no constituye garantía institucional."
        result = "success"
    }
    $evidence | ConvertTo-Json | Set-Content -Encoding UTF8 `
        (Join-Path $evidencePath "$($definition.Prefix)-$stamp.json")
    Write-Output ("OK: service=$Service outage_status=$during recovery_seconds=" + $evidence.recovery_seconds + " integrity_count=$count")
} finally {
    if (-not $recovered) { docker compose -f compose.yaml up -d --no-deps $Service | Out-Null }
    Pop-Location
}
