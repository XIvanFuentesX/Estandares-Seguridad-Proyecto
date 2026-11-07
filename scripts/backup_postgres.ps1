param(
    [ValidateSet("Academic", "Identity", "Both")]
    [string]$Target = "Both",
    [int]$RetentionDays = 30,
    [switch]$ApplyRetention
)

# Continue: Docker escribe progreso en stderr; los fallos se detectan con $LASTEXITCODE y throw explícito.
$ErrorActionPreference = "Continue"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPath = Join-Path $root "local"
$backupPath = Join-Path $localPath "backups"
$evidencePath = Join-Path $root "evidencias\backup"
New-Item -ItemType Directory -Force -Path $evidencePath | Out-Null
$started = Get-Date
$results = [System.Collections.Generic.List[object]]::new()

$definitions = [ordered]@{
    Academic = @{ Service = "backup-tool"; Prefix = "academic" }
    Identity = @{ Service = "identity-backup-tool"; Prefix = "identity" }
}
$selected = if ($Target -eq "Both") { @("Academic", "Identity") } else { @($Target) }

Push-Location $localPath
try {
    foreach ($name in $selected) {
        $definition = $definitions[$name]
        $timer = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $output = docker compose -f compose.yaml --profile backup run --rm `
                $definition.Service /usr/local/bin/backup-encrypted.sh --once
            if ($LASTEXITCODE -ne 0) { throw "Falló el respaldo cifrado de $name." }
            $manifest = Get-ChildItem $backupPath -Filter ($definition.Prefix + "-*.json") -File |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if (-not $manifest) { throw "No se generó manifiesto para $name." }
            $data = Get-Content $manifest.FullName -Raw | ConvertFrom-Json
            $encrypted = Join-Path $backupPath $data.file
            $hashFile = "$encrypted.sha256"
            if (-not (Test-Path $encrypted) -or -not (Test-Path $hashFile)) {
                throw "Faltan copia cifrada o hash para $name."
            }
            $expected = ((Get-Content $hashFile -Raw).Trim() -split '\s+')[0].ToUpperInvariant()
            $actual = (Get-FileHash -Algorithm SHA256 $encrypted).Hash
            if ($actual -ne $expected) { throw "Hash inválido para $name." }
            $results.Add([ordered]@{
                target = $name.ToLowerInvariant(); result = "success"; file = $data.file
                encrypted = $true; sha256_verified = $true; bytes = (Get-Item $encrypted).Length
                elapsed_seconds = [math]::Round($timer.Elapsed.TotalSeconds, 3)
            })
            Write-Output "OK: target=$name encrypted=true sha256=true"
        } catch {
            $results.Add([ordered]@{ target = $name.ToLowerInvariant(); result = "failure"; error = $_.Exception.Message })
            throw
        } finally { $timer.Stop() }
    }
} finally { Pop-Location }

$retentionCandidates = @()
if ($RetentionDays -gt 0) {
    $cutoff = (Get-Date).AddDays(-$RetentionDays)
    $retentionCandidates = @(Get-ChildItem $backupPath -Filter "*.dump.enc*" -File |
        Where-Object { $_.LastWriteTime -lt $cutoff })
    if ($ApplyRetention) {
        # Sólo se ejecuta con autorización explícita del operador.
        $retentionCandidates | Remove-Item -Force
    }
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidence = [ordered]@{
    timestamp = (Get-Date).ToString("o")
    target_requested = $Target.ToLowerInvariant()
    results = $results
    retention_days = $RetentionDays
    retention_candidates = $retentionCandidates.Count
    retention_applied = [bool]$ApplyRetention
    encryption = "AES-256-CBC/PBKDF2-200000; secreto separado en .env local ignorado"
    elapsed_seconds = [math]::Round(((Get-Date) - $started).TotalSeconds, 3)
}
$evidenceFile = Join-Path $evidencePath "backup-dual-$stamp.json"
$evidence | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $evidenceFile
Write-Output "evidencia=$evidenceFile"
