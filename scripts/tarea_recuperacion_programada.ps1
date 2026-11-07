param(
    [string]$Trigger = "programada"
)

# Punto de entrada de la tarea "SGSI-UVCG-Prueba-Recuperacion".
# - No contiene credenciales: los secretos se leen de local/.env por los scripts de Docker y nunca se registran.
# - Restaura sólo en instancias aisladas (perfil recovery); no borra bases, volúmenes ni respaldos.
# - Evita ejecuciones simultáneas (mutex) y detecta Docker no disponible.
$ErrorActionPreference = "Continue"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$outDir = Join-Path $root "evidencias\recovery\tarea-programada"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$csv = Join-Path $outDir "ejecuciones.csv"
$started = Get-Date
$stamp = $started.ToString("yyyyMMdd-HHmmss")
$record = [ordered]@{
    fecha = $started.ToString("yyyy-MM-dd"); hora_inicio = $started.ToString("HH:mm:ss"); origen = $Trigger
    usuario = $env:USERNAME; duracion_s = 0; resultado = "fallido"; detalle = ""; evidencia = ""
}

function Test-DockerAvailable([int]$TimeoutSeconds = 45) {
    $psi = [Diagnostics.ProcessStartInfo]::new("docker", "info --format {{.ServerVersion}}")
    $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true; $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    try {
        $process = [Diagnostics.Process]::Start($psi)
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) { $process.Kill(); return $false }
        return ($process.ExitCode -eq 0)
    } catch { return $false }
}

$mutex = [Threading.Mutex]::new($false, "Local\SGSI-UVCG-Prueba-Recuperacion")
$owned = $false
try {
    $owned = $mutex.WaitOne(0)
    if (-not $owned) {
        $record.resultado = "omitido"; $record.detalle = "Otra ejecución en curso; no se inicia una simultánea."
    } elseif (-not (Test-DockerAvailable)) {
        $record.resultado = "no_verificable"; $record.detalle = "Docker Desktop no disponible (¿sesión sin iniciar o motor detenido?)."
        Add-Content -Encoding ASCII (Join-Path $root "local\backups\execution.log") `
            ("{0} target=recovery-test result=failure reason=docker_unavailable" -f (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ"))
    } else {
        $transcript = & (Join-Path $PSScriptRoot "prueba_recuperacion_periodica.ps1") 2>&1 | ForEach-Object { "$_" }
        $last = ($transcript | Where-Object { $_ -match "^OK:|fallida|Error" } | Select-Object -Last 1)
        if ($transcript -match "^OK: restore_dual=success") {
            $record.resultado = "exitoso"
        }
        $record.detalle = "$last".Trim()
        $evidence = Get-ChildItem (Join-Path $root "evidencias\recovery") -Filter "recuperacion-periodica-*.json" |
            Where-Object LastWriteTime -ge $started | Sort-Object LastWriteTime | Select-Object -Last 1
        if ($evidence) { $record.evidencia = "evidencias/recovery/$($evidence.Name)" }
    }
} catch {
    $record.detalle = $_.Exception.Message
} finally {
    if ($owned) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
    $record.duracion_s = [math]::Round(((Get-Date) - $started).TotalSeconds, 1)
    $record.hora_fin = (Get-Date).ToString("HH:mm:ss")
    [pscustomobject]$record | Export-Csv -Append -NoTypeInformation -Encoding UTF8 $csv
    $record | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $outDir "ejecucion-$stamp.json")
}
Write-Output "resultado=$($record.resultado) duracion_s=$($record.duracion_s) evidencia=$($record.evidencia)"
if ($record.resultado -eq "fallido") { exit 1 }
