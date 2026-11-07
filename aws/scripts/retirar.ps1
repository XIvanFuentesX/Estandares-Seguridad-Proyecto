param(
    # Exige confirmación explícita: la retirada nunca es automática.
    [Parameter(Mandatory = $true)][ValidateSet("RETIRAR-SGSI-UVCG")][string]$Confirmacion
)

# Retirada posterior a la demostración (manual): vacía SÓLO el bucket del laboratorio (datos ficticios)
# y destruye los recursos de este Terraform. Guarda un inventario previo como evidencia.
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "comun.ps1")
$aws = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$out = Join-Path (Resolve-Path (Join-Path $aws "..")).Path "evidencias\aws"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$tf = Get-Content (Join-Path $aws "terraform.tfstate") -Raw | ConvertFrom-Json
$bucket = $tf.outputs.bucket_name.value
if ($bucket -notlike "uvcg-sgsi-lab-*") { throw "Bucket inesperado '$bucket': se aborta." }

aws s3api list-objects-v2 --bucket $bucket --output json | Set-Content -Encoding UTF8 (Join-Path $out "retirada-inventario-$stamp.json")
aws s3 rm "s3://$bucket" --recursive
$creds = aws configure export-credentials --format process | ConvertFrom-Json
$env:AWS_ACCESS_KEY_ID = $creds.AccessKeyId; $env:AWS_SECRET_ACCESS_KEY = $creds.SecretAccessKey; $env:AWS_SESSION_TOKEN = $creds.SessionToken
try {
    docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN -v "${aws}:/workspace" -w /workspace `
        hashicorp/terraform:1.14 destroy -input=false -auto-approve | Tee-Object -FilePath (Join-Path $out "retirada-$stamp.txt")
} finally {
    Remove-Item Env:\AWS_ACCESS_KEY_ID, Env:\AWS_SECRET_ACCESS_KEY, Env:\AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
}
aws freetier get-account-plan-state --output json | Set-Content -Encoding UTF8 (Join-Path $out "retirada-estado-plan-$stamp.json")
Write-Output "Retirada completada; verificar en Billing que no quedan recursos ni uso."
