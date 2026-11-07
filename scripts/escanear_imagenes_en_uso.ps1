param(
    [string]$Label = (Get-Date -Format "yyyyMMdd-HHmmss")
)

# Escanea con Trivy las imágenes de los contenedores del proyecto en ejecución (no las etiquetas upstream).
# Docker escribe progreso en stderr; los fallos se detectan con $LASTEXITCODE y throw explícito.
$ErrorActionPreference = "Continue"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPath = Join-Path $root "local"
$reports = Join-Path $root "evidencias\security"
$summary = [ordered]@{ timestamp = (Get-Date).ToString("o"); label = $Label; images = [System.Collections.Generic.List[object]]::new() }

Push-Location $localPath
try {
    $services = @(docker compose -f compose.yaml --profile backup-scheduled ps --format json | ConvertFrom-Json)
    $images = $services | Group-Object Image | ForEach-Object {
        [ordered]@{ image = $_.Name; services = @($_.Group.Service) }
    }
    foreach ($entry in $images) {
        $name = ($entry.image -replace '[^A-Za-z0-9]+', '-').Trim('-')
        $archive = Join-Path $reports "scan-image.tar"
        $output = "trivy-enuso-$name-$Label.json"
        try {
            docker image save --output $archive $entry.image
            if ($LASTEXITCODE -ne 0) { throw "No se pudo exportar $($entry.image)." }
            docker compose -f compose.yaml --profile security run --rm trivy image --input /reports/scan-image.tar `
                --scanners vuln --severity HIGH,CRITICAL --format json --output "/reports/$output" | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Trivy falló con $($entry.image)." }
        } finally {
            if (Test-Path $archive) { Remove-Item -LiteralPath $archive -Force }
        }
        $data = Get-Content (Join-Path $reports $output) -Raw -Encoding UTF8 | ConvertFrom-Json
        $vulns = @($data.Results | ForEach-Object { $_.Vulnerabilities } | Where-Object { $_ })
        $summary.images.Add([ordered]@{
            image = $entry.image; services = $entry.services
            image_id = ((docker image inspect $entry.image --format '{{.Id}}') -join "").Substring(7, 19)
            scope = @($data.Results | ForEach-Object { $_.Class } | Sort-Object -Unique)
            critical = @($vulns | Where-Object Severity -eq "CRITICAL").Count
            high = @($vulns | Where-Object Severity -eq "HIGH").Count
            fixable = @($vulns | Where-Object { $_.FixedVersion }).Count
            packages = @($vulns | ForEach-Object { $_.PkgName } | Sort-Object -Unique)
            report = "evidencias/security/$output"
        })
        Write-Output "OK: $($entry.image) critical=$($summary.images[-1].critical) high=$($summary.images[-1].high)"
    }
} finally { Pop-Location }
$summary | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $reports "escaneo-imagenes-en-uso-$Label.json")
Write-Output "evidencia=evidencias/security/escaneo-imagenes-en-uso-$Label.json"
