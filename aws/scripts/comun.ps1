# Se carga con: . (Join-Path $PSScriptRoot "comun.ps1")
# Si AWS CLI no está instalado en Windows, define `aws` como la CLI oficial en contenedor (amazon/aws-cli).
# Monta la caché de credenciales temporales (%USERPROFILE%\.aws, creada por `aws login --remote`) y la
# carpeta aws/ del proyecto como directorio de trabajo (/aws). Las credenciales de un rol asumido se
# pasan sólo como variables de entorno del proceso; nunca se escriben en disco.
$script:AwsDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not (Get-Command aws.exe -ErrorAction SilentlyContinue)) {
    function global:aws {
        $profileDir = Join-Path $env:USERPROFILE ".aws"
        New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
        $envArgs = @()
        foreach ($name in "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_REGION") {
            if (Test-Path "Env:\$name") { $envArgs += @("-e", $name) }
        }
        docker run --rm -i -v "${profileDir}:/root/.aws" -v "${script:AwsDir}:/aws" -w /aws @envArgs amazon/aws-cli:latest @args
    }
}
if (-not $env:AWS_REGION) { $env:AWS_REGION = "us-east-1" }
