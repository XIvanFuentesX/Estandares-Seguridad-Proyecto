param(
    # Sin -Aplicar sólo genera y revisa el plan. Con -Aplicar ejecuta EXACTAMENTE el plan revisado.
    [switch]$Aplicar
)

# Flujo: verificar cuenta (plan FREE) -> terraform plan real -> compuerta de costo -> (opcional) apply del plan.
# Terraform se ejecuta en contenedor con credenciales temporales exportadas por `aws configure export-credentials`;
# no se escriben claves en disco ni en archivos .tf. Nunca ejecuta destroy.
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "comun.ps1")
$aws = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$root = (Resolve-Path (Join-Path $aws "..")).Path
$out = Join-Path $root "evidencias\aws"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$tfImage = "hashicorp/terraform:1.14"

& (Join-Path $PSScriptRoot "verificar_cuenta.ps1")
if ($LASTEXITCODE -ne 0) { throw "Cuenta no elegible: no se genera plan ni se despliega." }
if (-not (Test-Path (Join-Path $aws "terraform.tfvars"))) { throw "Falta aws/terraform.tfvars (copiar de terraform.tfvars.example)." }

# Credenciales temporales sólo en variables de entorno de este proceso.
$creds = aws configure export-credentials --format process | ConvertFrom-Json
if (-not $creds.SessionToken) { throw "Se requieren credenciales temporales (con SessionToken)." }
$env:AWS_ACCESS_KEY_ID = $creds.AccessKeyId
$env:AWS_SECRET_ACCESS_KEY = $creds.SecretAccessKey
$env:AWS_SESSION_TOKEN = $creds.SessionToken
$envArgs = @("-e", "AWS_ACCESS_KEY_ID", "-e", "AWS_SECRET_ACCESS_KEY", "-e", "AWS_SESSION_TOKEN")
$run = @("run", "--rm") + $envArgs + @("-v", "${aws}:/workspace", "-w", "/workspace", $tfImage)

try {
    docker @run init -input=false | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "terraform init falló." }
    $planFile = "plan-$stamp.tfplan"
    docker @run plan -input=false -out=$planFile | Tee-Object -FilePath (Join-Path $out "plan-$stamp.txt")
    if ($LASTEXITCODE -ne 0) { throw "terraform plan falló." }
    docker @run show -json $planFile | Set-Content -Encoding UTF8 (Join-Path $aws "salidas-plan-$stamp.json")
    python (Join-Path $PSScriptRoot "revisar_plan.py") (Join-Path $aws "salidas-plan-$stamp.json") (Join-Path $out "revision-plan-$stamp.json")
    if ($LASTEXITCODE -ne 0) { throw "Plan RECHAZADO por la compuerta de costo: no se aplica." }
    $planHash = (Get-FileHash (Join-Path $aws $planFile)).Hash
    Write-Output "Plan aprobado por la compuerta. SHA-256 del plan: $planHash"
    if (-not $Aplicar) { Write-Output "Modo revisión: no se aplicó. Repetir con -Aplicar para ejecutar este plan."; return }
    docker @run apply -input=false $planFile | Tee-Object -FilePath (Join-Path $out "apply-$stamp.txt")
    if ($LASTEXITCODE -ne 0) { throw "terraform apply falló; revisar el estado antes de reintentar." }
    & (Join-Path $PSScriptRoot "verificar_cuenta.ps1")   # el plan debe seguir siendo FREE tras el despliegue
} finally {
    Remove-Item Env:\AWS_ACCESS_KEY_ID, Env:\AWS_SECRET_ACCESS_KEY, Env:\AWS_SESSION_TOKEN -ErrorAction SilentlyContinue
    Get-ChildItem $aws -Filter "salidas-plan-*.json" | Remove-Item -ErrorAction SilentlyContinue  # puede contener identificadores
}
