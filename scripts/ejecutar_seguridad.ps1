$ErrorActionPreference = "Continue"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$localPath = Join-Path $root "local"
$status = [ordered]@{}

Push-Location $localPath
try {
    docker compose -f compose.yaml --profile security build security-python
    if ($LASTEXITCODE -ne 0) { throw "No se pudo construir security-python." }

    docker compose -f compose.yaml --profile security run --rm security-python `
        bandit -r /workspace/local/api /workspace/scripts -f json -o /reports/bandit.json
    $status.bandit_exit = $LASTEXITCODE

    docker compose -f compose.yaml --profile security run --rm security-python `
        pip-audit -r /workspace/local/api/requirements.txt -f json -o /reports/pip-audit.json
    $status.pip_audit_exit = $LASTEXITCODE

    docker compose -f compose.yaml --profile security run --rm trivy fs `
        --scanners misconfig,secret --format json --output /reports/trivy-fs.json `
        --skip-files /workspace/local/.env `
        --skip-dirs /workspace/local/tls,/workspace/local/backups,/workspace/evidencias `
        /workspace
    $status.trivy_fs_exit = $LASTEXITCODE

    $images = [ordered]@{
        "python:3.12-alpine" = "trivy-python-image.json"
        "local-proxy:latest" = "trivy-nginx-image.json"
        "postgres:16-alpine" = "trivy-postgres-image.json"
        "local-postgres-hardened:16" = "trivy-postgres-hardened-image.json"
        "quay.io/keycloak/keycloak:26.8.1" = "trivy-keycloak-image.json"
    }
    foreach ($entry in $images.GetEnumerator()) {
        # Imágenes construidas localmente: Trivy las analiza desde un archivo exportado.
        if ($entry.Key -like "local-*") {
            $archive = Join-Path $root "evidencias\security\local-image.tar"
            try {
                docker image save --output $archive $entry.Key
                if ($LASTEXITCODE -ne 0) { throw "No se pudo exportar la imagen local $($entry.Key)." }
                docker compose -f compose.yaml --profile security run --rm trivy image `
                    --input /reports/local-image.tar --scanners vuln --severity HIGH,CRITICAL `
                    --format json --output ("/reports/" + $entry.Value)
                $status["trivy_" + $entry.Value] = $LASTEXITCODE
            } finally {
                if (Test-Path $archive) { Remove-Item -LiteralPath $archive -Force }
            }
            continue
        }
        docker compose -f compose.yaml --profile security run --rm trivy image `
            --scanners vuln --severity HIGH,CRITICAL --format json --output ("/reports/" + $entry.Value) $entry.Key
        $status["trivy_" + $entry.Value] = $LASTEXITCODE
    }
} finally {
    Pop-Location
}

$status | ConvertTo-Json | Set-Content -Encoding UTF8 `
    (Join-Path $root "evidencias\security\ejecucion-herramientas.json")
python (Join-Path $PSScriptRoot "resumir_seguridad.py")
if ($LASTEXITCODE -ne 0) { throw "No se pudieron resumir los resultados." }
python (Join-Path $PSScriptRoot "generar_registro_vulnerabilidades.py")
if ($LASTEXITCODE -ne 0) { throw "No se pudo generar el registro detallado." }
