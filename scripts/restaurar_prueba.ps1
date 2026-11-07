param(
    [ValidateSet("Academic", "Identity", "Both")]
    [string]$Target = "Both",
    [string]$BackupFile,
    # Por defecto la base restaurada se CONSERVA en la instancia aislada (no se borra nada).
    # -DropRestoredDatabase la elimina tras verificarla; usar sólo con autorización expresa.
    [switch]$DropRestoredDatabase
)

# Continue: Docker escribe progreso en stderr; los fallos se detectan con $LASTEXITCODE y throw explícito.
$ErrorActionPreference = "Continue"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPath = Join-Path $root "local"
$backupPath = Join-Path $localPath "backups"
$evidencePath = Join-Path $root "evidencias\recovery"
$definitions = [ordered]@{
    Academic = @{
        Prefix = "academic"; Tool = "backup-tool"; RestoreService = "restore-db"
        Host = "restore-db"; AdminDb = "restore_admin"; EnvUser = "DB_USER"
        Query = "SELECT count(*) FROM cursos"; Minimum = 3; Metric = "course_count"
    }
    Identity = @{
        Prefix = "identity"; Tool = "identity-backup-tool"; RestoreService = "identity-restore-db"
        Host = "identity-restore-db"; AdminDb = "restore_identity_admin"; EnvUser = "KC_DB_USER"
        Query = "SELECT count(*) FROM user_entity"; Minimum = 4; Metric = "identity_count"
    }
}
$selected = if ($Target -eq "Both") { @("Academic", "Identity") } else { @($Target) }
$envValues = @{}
Get-Content (Join-Path $localPath ".env") | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') { $envValues[$matches[1]] = $matches[2] }
}
$results = [System.Collections.Generic.List[object]]::new()
$failed = $false
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

Push-Location $localPath
try {
    foreach ($name in $selected) {
        $definition = $definitions[$name]
        $candidate = $BackupFile
        if (-not $candidate -or $Target -eq "Both") {
            $latest = Get-ChildItem $backupPath -Filter ($definition.Prefix + "-*.dump.enc") -File |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if (-not $latest) { throw "No existe respaldo cifrado de $name." }
            $candidate = $latest.Name
        }
        $dumpPath = Join-Path $backupPath $candidate
        $hashPath = "$dumpPath.sha256"
        if (-not (Test-Path $dumpPath) -or -not (Test-Path $hashPath)) { throw "Faltan copia/hash de $name." }
        $expected = ((Get-Content $hashPath -Raw).Trim() -split '\s+')[0].ToUpperInvariant()
        $actual = (Get-FileHash -Algorithm SHA256 $dumpPath).Hash
        if ($actual -ne $expected) { throw "Hash inválido de $name." }

        $restoreDatabase = "restore_$($definition.Prefix)_$stamp"
        $timer = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            docker compose -f compose.yaml --profile recovery up -d $definition.RestoreService
            if ($LASTEXITCODE -ne 0) { throw "No se inició restore de $name." }
            $deadline = (Get-Date).AddSeconds(90)
            do {
                $row = docker compose -f compose.yaml --profile recovery ps $definition.RestoreService --format json | ConvertFrom-Json
                if ($row.Health -eq "healthy") { break }
                Start-Sleep -Seconds 2
            } while ((Get-Date) -lt $deadline)
            if ($row.Health -ne "healthy") { throw "Restore de $name no alcanzó healthy." }

            docker compose -f compose.yaml --profile recovery run --rm `
                -e "BACKUP_FILE=$candidate" -e "RESTORE_DB_NAME=$restoreDatabase" `
                -e "PGHOST=$($definition.Host)" -e "PGDATABASE=$($definition.AdminDb)" $definition.Tool sh -ec `
                'openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in "/backups/$BACKUP_FILE" -out /tmp/restore.dump -pass env:BACKUP_ENCRYPTION_PASSWORD; createdb --maintenance-db="$PGDATABASE" "$RESTORE_DB_NAME"; pg_restore --exit-on-error --no-owner --no-acl --dbname="$RESTORE_DB_NAME" /tmp/restore.dump; rm -f /tmp/restore.dump'
            if ($LASTEXITCODE -ne 0) { throw "Falló descifrado/restauración de $name." }

            $count = docker compose -f compose.yaml --profile recovery exec -T $definition.RestoreService `
                psql -U $envValues[$definition.EnvUser] -d $restoreDatabase -Atc $definition.Query
            if ($LASTEXITCODE -ne 0 -or [int]$count -lt $definition.Minimum) { throw "Validación de $name falló." }
            $verifiedSeconds = [math]::Round($timer.Elapsed.TotalSeconds, 3)
            $dropped = $false
            if ($DropRestoredDatabase) {
                docker compose -f compose.yaml --profile recovery exec -T $definition.RestoreService `
                    dropdb -U $envValues[$definition.EnvUser] --if-exists $restoreDatabase
                $dropped = ($LASTEXITCODE -eq 0)
            }
            $results.Add([ordered]@{
                target = $name.ToLowerInvariant(); source_backup = $candidate; sha256_verified = $true
                encrypted = $true; isolated_service = $definition.RestoreService
                isolated_database = $restoreDatabase; verification_metric = $definition.Metric
                verification_count = [int]$count; elapsed_seconds = $verifiedSeconds
                restored_copy_dropped_after_verification = $dropped
                primary_database_modified = $false; result = "success"
            })
            Write-Output "OK: target=$name count=$count encrypted=true isolated=true"
        } catch {
            $results.Add([ordered]@{
                target = $name.ToLowerInvariant(); source_backup = $candidate; isolated_service = $definition.RestoreService
                elapsed_seconds = [math]::Round($timer.Elapsed.TotalSeconds, 3)
                primary_database_modified = $false; result = "failure"; error = $_.Exception.Message
            })
            # La bitácora alimenta la regla SIEM-BACKUP-001.
            Add-Content -Encoding ASCII (Join-Path $backupPath "execution.log") `
                ("{0} target=restore-{1} result=failure" -f (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"), $definition.Prefix)
            $failed = $true
        } finally {
            $timer.Stop()
            docker compose -f compose.yaml --profile recovery stop $definition.RestoreService | Out-Null
        }
    }
} finally { Pop-Location }

$evidence = [ordered]@{
    timestamp = (Get-Date).ToString("o"); requested = $Target.ToLowerInvariant()
    result = $(if ($failed) { "failure" } else { "success" }); results = $results
}
$evidenceFile = Join-Path $evidencePath "restauracion-dual-$stamp.json"
$evidence | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $evidenceFile
Write-Output "evidencia=$evidenceFile"
if ($failed) { throw "Al menos una restauración aislada falló; ver $evidenceFile" }
