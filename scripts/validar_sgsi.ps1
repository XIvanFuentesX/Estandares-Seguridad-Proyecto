param(
    [switch]$IncludeSecurity,
    [switch]$IncludeIds,
    [switch]$IncludeRecovery,
    [switch]$IncludeContinuity
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPath = Join-Path $root "local"
$evidencePath = Join-Path $root "evidencias\automatizacion"
New-Item -ItemType Directory -Force -Path $evidencePath | Out-Null
$results = [System.Collections.Generic.List[object]]::new()

function Add-Result([string]$Id, [string]$State, [string]$Detail) {
    $results.Add([ordered]@{
        control = $Id
        estado = $State
        detalle = $Detail.Trim()
        fecha = (Get-Date -Format "yyyy-MM-dd HH:mm:ss K")
    })
}

function Invoke-Control([string]$Id, [scriptblock]$Action) {
    # Docker escribe progreso en stderr; con Stop, PowerShell 5.1 lo convertiría en excepción.
    $ErrorActionPreference = "Continue"
    try {
        $global:LASTEXITCODE = 0
        $output = (& $Action 2>&1 | ForEach-Object { "$_" } | Out-String)
        if ($LASTEXITCODE -ne 0) { throw "Código de salida $LASTEXITCODE. $output" }
        Add-Result $Id "exitoso" $output
    } catch {
        Add-Result $Id "fallido" $_.Exception.Message
    }
}

Push-Location $localPath
try {
    Invoke-Control "CORE-COMPOSE" { docker compose -f compose.yaml config --quiet; "compose_config=ok" }
    Invoke-Control "APP-HTTPS" { python ..\scripts\pruebas_locales.py }
    Invoke-Control "IAM-RBAC-MFA" { python ..\scripts\pruebas_identidad.py }
    Invoke-Control "NETWORK-SEGMENTATION" { & ..\scripts\validar_segmentacion.ps1 }
    Invoke-Control "SIEM-LIGHT" { python ..\scripts\pruebas_siem.py }
    Invoke-Control "BACKUP-SCHEDULED" { & ..\scripts\validar_backups_programados.ps1 }
    Invoke-Control "CONFIG-INTEGRITY" { python ..\scripts\integridad_configuracion.py --verify }
    Invoke-Control "POSTGRES-HARDENED" {
        foreach ($c in "local-db-1", "local-identity-db-1") {
            $image = (docker inspect $c --format "{{.Config.Image}}") -join ""
            $uid = (docker exec $c id -u) -join ""
            $gosu = (docker exec $c sh -c "command -v gosu || echo absent") -join ""
            if ($image -ne "local-postgres-hardened:16" -or $uid -ne "70" -or $gosu -ne "absent") { throw "$c image=$image uid=$uid gosu=$gosu" }
            "$c image=$image uid=$uid gosu=$gosu"
        }
        $rollback = Get-ChildItem rollback -Filter "compose.yaml.pre-upgrade-*.bak" | Sort-Object LastWriteTime | Select-Object -Last 1
        $check = & ..\scripts\rollback_postgres.ps1 -RollbackCompose $rollback.FullName 2>&1 | Out-String
        if ($check -notmatch "rollback_preparado=True") { throw "Reversión no preparada: $check" }
        "rollback_preparado=True compose=$($rollback.Name)"
    }
    Invoke-Control "SCHEDULED-RECOVERY-TASK" {
        $task = Get-ScheduledTask -TaskName "SGSI-UVCG-Prueba-Recuperacion" -ErrorAction Stop
        $info = Get-ScheduledTaskInfo -TaskName "SGSI-UVCG-Prueba-Recuperacion"
        if ($task.Principal.LogonType -ne "Interactive" -or $task.Principal.RunLevel -ne "Limited" -or $task.Settings.MultipleInstances -ne "IgnoreNew") { throw "Configuración de la tarea no conforme." }
        if ($info.LastTaskResult -ne 0) { throw "Última ejecución con código $($info.LastTaskResult)." }
        "tarea=registrada estado=$($task.State) ultima=$($info.LastRunTime) resultado=$($info.LastTaskResult) proxima=$($info.NextRunTime)"
    }
    Invoke-Control "CONFIG-INTEGRITY-SELFTEST" { python ..\scripts\integridad_configuracion.py --self-test }
    Invoke-Control "CONTAINER-MONITORING" { python ..\scripts\vigilancia_contenedores.py --check --label validacion }
    Invoke-Control "AVAILABILITY-MONITOR" {
        $state = (docker inspect local-uptime-monitor-1 --format "{{.State.Status}}") -join ""
        $log = Join-Path $localPath "monitoring\disponibilidad\disponibilidad.log"
        $last = Get-Content $log -Tail 3
        $age = ((Get-Date).ToUniversalTime() - [datetime]::Parse(($last[-1] -split ' ')[0]).ToUniversalTime()).TotalSeconds
        if ($state -ne "running" -or $age -gt 60) { throw "Monitor no activo o sin datos recientes (estado=$state, antiguedad=$([int]$age)s)." }
        "monitor=running ultima_muestra_hace_s=$([int]$age)"; $last
    }
    Invoke-Control "DLP-GATE" {
        $s = Get-ChildItem dlp\samples -Filter *.txt | ForEach-Object FullName
        python ..\scripts\dlp_compuerta.py @s --canal externo --validacion --esperado "publico.txt=allowed,confidencial-ficticio.txt=blocked,restringido-ficticio.txt=blocked,tarjeta-ficticia.txt=blocked,credencial-ficticia.txt=blocked"
        if ($LASTEXITCODE -eq 0) { python ..\scripts\dlp_compuerta.py @s --canal interno --validacion --esperado "confidencial-ficticio.txt=allowed,restringido-ficticio.txt=blocked,credencial-ficticia.txt=blocked" }
    }
    Invoke-Control "MDM-SIMULATION" { python ..\scripts\mdm_cumplimiento.py }
    Invoke-Control "SGSI-RECORDS" { python ..\scripts\gestion_sgsi.py verificar }
    Invoke-Control "SIEM-INTEGRITY-SEAL" { python ..\scripts\siem_ligero.py seal; if ($LASTEXITCODE -eq 0) { python ..\scripts\siem_ligero.py verify } }
    # Las bases principales no tienen archivado WAL (activarlo requiere autorización): no verificable, no exitoso.
    $walOut = foreach ($t in @(@("local-db-1","DB_USER","DB_NAME","academic-principal"), @("local-identity-db-1","KC_DB_USER","KC_DB_NAME","identity-principal"))) {
        python ..\scripts\monitor_wal.py --container $t[0] --env-user $t[1] --env-db $t[2] --name $t[3]
    }
    if (($walOut -join " ") -match '"archive_mode": "off"') {
        Add-Result "PITR-PRINCIPALES" "no_verificable" "archive_mode=off en db e identity-db; compose.pitr.yaml preparado, activación pendiente de autorización."
    } else { Add-Result "PITR-PRINCIPALES" "exitoso" ($walOut -join " ") }

    Invoke-Control "RETENTION-DRYRUN" {
        $before = @(Get-ChildItem backups -File).Count
        python ..\scripts\simular_retencion.py
        $after = @(Get-ChildItem backups -File).Count
        if ($before -ne $after) { throw "La simulación alteró el número de archivos ($before -> $after)." }
        "archivos_antes=$before archivos_despues=$after (sin borrado)"
    }
    Invoke-Control "GOVERNANCE-DOCS" {
        python ..\scripts\generar_gobernanza_sgsi.py
        if ($LASTEXITCODE -eq 0) { python ..\scripts\validar_trazabilidad.py }
    }
    Invoke-Control "AZURE-STATIC" { python ..\scripts\validar_terraform_estatico.py }
    Invoke-Control "DLP-DEMO" { python ..\scripts\dlp_scan.py --expect-findings }

    if ($IncludeIds) {
        Invoke-Control "IDS-OFFLINE" {
            python ..\scripts\generar_pcap_ids.py
            docker compose -f compose.yaml --profile ids run --rm ids
            if ($LASTEXITCODE -eq 0) { python ..\scripts\validar_alerta_ids.py }
        }
    } else { Add-Result "IDS-OFFLINE" "omitido" "Use -IncludeIds para ejecutar el perfil IDS." }

    # Ciclo SIEM sobre eventos reales: logs Docker de los cinco servicios, backups y Suricata.
    Invoke-Control "SIEM-INTEGRATED" { python ..\scripts\siem_pipeline.py }

    if ($IncludeRecovery) {
        Invoke-Control "BACKUP-RESTORE" {
            & ..\scripts\backup_postgres.ps1 -Target Both
            if ($LASTEXITCODE -eq 0) { & ..\scripts\prueba_recuperacion_periodica.ps1 }
        }
        Invoke-Control "PITR-REPLICAS" { python ..\scripts\pitr_prueba.py }
    } else { Add-Result "BACKUP-RESTORE" "omitido" "Use -IncludeRecovery; nunca altera la base principal." }

    if ($IncludeSecurity) {
        Invoke-Control "DEVSECOPS" { & ..\scripts\ejecutar_seguridad.ps1 }
        Invoke-Control "VULN-IMAGES-IN-USE" {
            & ..\scripts\escanear_imagenes_en_uso.ps1 -Label (Get-Date -Format "yyyyMMdd-HHmmss") | Where-Object { "$_" -match "^OK:|^evidencia" }
        }
    } else { Add-Result "DEVSECOPS" "omitido" "Use -IncludeSecurity; requiere red para bases de vulnerabilidades." }

    if ($IncludeContinuity) {
        Invoke-Control "CONTINUITY-API" { & ..\scripts\prueba_continuidad.ps1 -Service api }
        Invoke-Control "CONTINUITY-IAM" { & ..\scripts\prueba_continuidad.ps1 -Service keycloak }
    } else {
        Add-Result "CONTINUITY-API" "omitido" "Use -IncludeContinuity; interrumpe deliberadamente la API por segundos."
        Add-Result "CONTINUITY-IAM" "omitido" "Use -IncludeContinuity; interrumpe deliberadamente Keycloak por segundos."
    }
} finally {
    Pop-Location
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$report = [ordered]@{
    alcance = "laboratorio SGSI UVCG"
    fecha = (Get-Date -Format "yyyy-MM-dd HH:mm:ss K")
    resultados = $results
    resumen = [ordered]@{
        exitosos = @($results | Where-Object estado -eq "exitoso").Count
        fallidos = @($results | Where-Object estado -eq "fallido").Count
        omitidos = @($results | Where-Object estado -eq "omitido").Count
        no_verificables = @($results | Where-Object estado -eq "no_verificable").Count
    }
}
$target = Join-Path $evidencePath "validacion-sgsi-$stamp.json"
$report | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $target
$report.resumen | Format-List
Write-Output "evidencia=$target"
if ($report.resumen.fallidos -gt 0) { exit 1 }
