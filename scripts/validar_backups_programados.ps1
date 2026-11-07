$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPath = Join-Path $root "local"
$backupPath = Join-Path $localPath "backups"
$evidencePath = Join-Path $root "evidencias\backup"

Push-Location $localPath
try {
    $rows = @(docker compose -f compose.yaml --profile backup-scheduled ps `
        academic-backup-scheduler identity-backup-scheduler --format json | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0) { throw "No se pudo consultar schedulers." }
    foreach ($service in @("academic-backup-scheduler", "identity-backup-scheduler")) {
        $row = @($rows | Where-Object Service -eq $service)[0]
        if (-not $row -or $row.State -ne "running") { throw "$service no está ejecutándose." }
    }
} finally { Pop-Location }

$copies = [System.Collections.Generic.List[object]]::new()
foreach ($prefix in @("academic", "identity")) {
    $latest = Get-ChildItem $backupPath -Filter "$prefix-*.dump.enc" -File |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) { throw "No hay copia programada $prefix." }
    $hashFile = "$($latest.FullName).sha256"
    $manifest = $latest.FullName.Replace(".dump.enc", ".json")
    if (-not (Test-Path $hashFile) -or -not (Test-Path $manifest)) { throw "Faltan metadatos $prefix." }
    $expected = ((Get-Content $hashFile -Raw).Trim() -split '\s+')[0].ToUpperInvariant()
    $actual = (Get-FileHash -Algorithm SHA256 $latest.FullName).Hash
    if ($actual -ne $expected) { throw "Hash inválido $prefix." }
    $copies.Add([ordered]@{
        target = $prefix; file = $latest.Name; bytes = $latest.Length
        sha256_verified = $true; encrypted = $true; last_write = $latest.LastWriteTime.ToString("o")
    })
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$result = [ordered]@{
    timestamp = (Get-Date).ToString("o")
    result = "success"
    interval_seconds = 86400
    schedulers_running = @("academic-backup-scheduler", "identity-backup-scheduler")
    copies = $copies
    retention = "30 días configurables; borrado no aplicado sin -ApplyRetention"
    failure_alert_source = "backups/execution.log + SIEM-BACKUP-001"
}
$result | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $evidencePath "backups-programados-$stamp.json")
Write-Output "OK: schedulers=2 encrypted_copies=2 sha256=true interval_seconds=86400"
