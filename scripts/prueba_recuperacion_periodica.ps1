param(
    # Intervalo real del scheduler; se usa para evaluar el RPO alcanzable (pérdida máxima entre copias).
    [int]$BackupIntervalSeconds = 86400
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backupLog = Join-Path $root "local\backups\execution.log"
$evidencePath = Join-Path $root "evidencias\recovery"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$started = Get-Date

# Objetivos propuestos (supuestos académicos) tomados del BIA, no valores fijos en el script.
$bia = Import-Csv -Encoding UTF8 (Join-Path $root "governance\bia.csv")
$objectives = @{
    academic = $bia | Where-Object id -eq "PROC-002"
    identity = $bia | Where-Object id -eq "PROC-004"
}

$evidence = [ordered]@{
    timestamp = $started.ToString("o")
    scenario = "prueba_periodica_backup_restore_aislado"
    frequency_proposed = "Trimestral (DRP); puede programarse con el Programador de tareas tras autorización"
    steps = [System.Collections.Generic.List[object]]::new()
    comparison = [System.Collections.Generic.List[object]]::new()
    result = "failure"
}

try {
    $out = & (Join-Path $PSScriptRoot "validar_backups_programados.ps1") | Out-String
    $evidence.steps.Add([ordered]@{ step = "schedulers_y_hash"; result = "success"; detail = $out.Trim() })

    $out = & (Join-Path $PSScriptRoot "restaurar_prueba.ps1") -Target Both | Out-String
    $evidence.steps.Add([ordered]@{ step = "restore_aislado_dual"; result = "success"; detail = ($out.Trim() -split "`n" | Select-Object -Last 3) -join " " })

    $restore = Get-ChildItem $evidencePath -Filter "restauracion-dual-*.json" | Sort-Object LastWriteTime -Descending |
        Select-Object -First 1 | Get-Content -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($item in $restore.results) {
        $objective = $objectives[$item.target]
        $rtoSeconds = [double]$objective.rto_horas * 3600
        $rpoSeconds = [double]$objective.rpo_horas * 3600
        $evidence.comparison.Add([ordered]@{
            target = $item.target
            bia_process = $objective.id
            observed_restore_seconds = [double]$item.elapsed_seconds
            proposed_rto_seconds = $rtoSeconds
            restore_within_rto = ([double]$item.elapsed_seconds -le $rtoSeconds)
            backup_interval_seconds = $BackupIntervalSeconds
            proposed_rpo_seconds = $rpoSeconds
            rpo_achievable_with_current_schedule = ($BackupIntervalSeconds -le $rpoSeconds)
            verification = "$($item.verification_metric)=$($item.verification_count)"
            note = "El tiempo observado sólo cubre la restauración técnica de una base pequeña en laboratorio; no incluye detección, decisión, comunicación ni validación funcional."
        })
    }
    $evidence.result = "success"
} catch {
    $evidence.steps.Add([ordered]@{ step = "error"; result = "failure"; detail = $_.Exception.Message })
    Add-Content -Encoding ASCII $backupLog ("{0} target=recovery-test result=failure" -f (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"))
} finally {
    $evidence.elapsed_seconds = [math]::Round(((Get-Date) - $started).TotalSeconds, 3)
    $file = Join-Path $evidencePath "recuperacion-periodica-$stamp.json"
    $evidence | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $file
}

if ($evidence.result -ne "success") { throw "Prueba periódica de recuperación fallida; ver $file" }
$gaps = @($evidence.comparison | Where-Object { -not $_.rpo_achievable_with_current_schedule }).Count
Write-Output "OK: restore_dual=success dentro_rto=$(@($evidence.comparison | Where-Object restore_within_rto).Count)/2 brechas_rpo=$gaps evidencia=$file"
