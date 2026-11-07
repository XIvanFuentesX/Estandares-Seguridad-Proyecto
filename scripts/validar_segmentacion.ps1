$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPath = Join-Path $root "local"
$evidencePath = Join-Path $root "evidencias\network"
New-Item -ItemType Directory -Force -Path $evidencePath | Out-Null

Push-Location $localPath
try {
    $containers = @("local-proxy-1", "local-api-1", "local-db-1", "local-identity-db-1", "local-keycloak-1")
    $inspect = docker inspect $containers | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw "docker inspect falló." }
    $published = @{}
    $networks = @{}
    foreach ($item in $inspect) {
        $portNames = @()
        if ($null -ne $item.HostConfig.PortBindings) {
            $portNames = @($item.HostConfig.PortBindings.PSObject.Properties.Name | Where-Object { $_ })
        }
        $published[$item.Name.TrimStart('/')] = $portNames
        $networks[$item.Name.TrimStart('/')] = @($item.NetworkSettings.Networks.PSObject.Properties.Name)
    }
    if ($published['local-api-1'].Count -ne 0 -or $published['local-db-1'].Count -ne 0 -or
        $published['local-identity-db-1'].Count -ne 0 -or $published['local-keycloak-1'].Count -ne 0) {
        throw "Un servicio interno publica puertos."
    }
    if ($published['local-proxy-1'].Count -ne 2) { throw "El proxy no es el único punto de entrada esperado." }

    docker compose -f compose.yaml exec -T api python -c "import socket; socket.gethostbyname('db'); print('api_to_db_dns=allowed')" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "API no resuelve db." }
    docker compose -f compose.yaml exec -T proxy sh -c "getent hosts db >/dev/null 2>&1"
    $proxyToDbBlocked = $LASTEXITCODE -ne 0
    docker compose -f compose.yaml exec -T db sh -c "getent hosts proxy >/dev/null 2>&1"
    $dbToProxyBlocked = $LASTEXITCODE -ne 0
    if (-not $proxyToDbBlocked -or -not $dbToProxyBlocked) { throw "Segmentación lateral inesperada." }

    $result = [ordered]@{
        timestamp = (Get-Date).ToString("o")
        result = "success"
        only_proxy_publishes = $true
        api_to_database_dns = "allowed"
        proxy_to_database_dns = "blocked"
        database_to_proxy_dns = "blocked"
        networks = $networks
        limitations = "Valida redes/DNS Docker; no sustituye una prueba de firewall físico o captura en vivo."
    }
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $result | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $evidencePath "segmentacion-$stamp.json")
    Write-Output "OK: only_proxy_publishes=true api-db=allowed proxy-db=blocked db-proxy=blocked"
    $global:LASTEXITCODE = 0
} finally { Pop-Location }
