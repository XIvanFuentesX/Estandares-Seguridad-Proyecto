<#
.SYNOPSIS
  Genera y revisa un `terraform plan` REAL del SGSI UVCG. NO ejecuta apply.

.DESCRIPTION
  Sólo debe usarse cuando exista suscripción autorizada. Pasos:
    1. Verifica identidad y suscripción activas (az account show) contra los valores esperados.
    2. Lista los roles del operador en la suscripción (se requiere, como mínimo, Contributor +
       Role Based Access Control Administrator acotado, o Owner temporal vía PIM).
    3. Revisa el registro de proveedores de recursos y uso de cuotas de red en la región.
    4. terraform init (backend remoto opcional), validate y plan -out.
    5. terraform show -json y revisión automática (revisar_plan.py): recursos a crear, recursos con
       costo y comparación con el escenario aprobado.
  Las salidas quedan en azure/scripts/salidas/ (ignorado por git): el plan puede contener datos sensibles.

.EXAMPLE
  $env:ARM_SUBSCRIPTION_ID = "<guid>"
  .\azure\scripts\generar_plan.ps1 -Ambiente dev -SuscripcionEsperada "<guid>" -TenantEsperado "<guid>"
#>
param(
    [ValidateSet("dev", "demo", "inst")] [string]$Ambiente = "dev",
    [Parameter(Mandatory = $true)] [string]$SuscripcionEsperada,
    [Parameter(Mandatory = $true)] [string]$TenantEsperado,
    [string]$Region = "eastus2",
    [switch]$UsarBackendRemoto
)

$ErrorActionPreference = "Stop"
$az = Split-Path -Parent $PSScriptRoot
$salidas = Join-Path $PSScriptRoot "salidas"
New-Item -ItemType Directory -Force -Path $salidas | Out-Null
$sello = Get-Date -Format "yyyyMMdd-HHmmss"
$varFile = Join-Path $az "environments\$Ambiente.tfvars"
if (-not (Test-Path $varFile)) { throw "Copie environments\$Ambiente.tfvars.example a environments\$Ambiente.tfvars y revise los valores." }
foreach ($cmd in @("az", "terraform")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "Falta '$cmd' en PATH (ver CIERRE_AZURE.md, sección de acciones)." }
}

Write-Host "1) Identidad y suscripción"
$cuenta = az account show --output json | ConvertFrom-Json
if ($cuenta.id -ne $SuscripcionEsperada -or $cuenta.tenantId -ne $TenantEsperado) {
    throw "La sesión activa ($($cuenta.id) / $($cuenta.tenantId)) no coincide con la suscripción/tenant autorizados."
}
"Suscripción: $($cuenta.name) | Usuario: $($cuenta.user.name) | Tipo: $($cuenta.user.type)" | Tee-Object (Join-Path $salidas "plan-$Ambiente-$sello-contexto.txt")

Write-Host "2) Roles del operador en la suscripción"
az role assignment list --assignee $cuenta.user.name --scope "/subscriptions/$($cuenta.id)" --include-inherited `
    --query "[].{rol:roleDefinitionName, alcance:scope}" --output table |
    Tee-Object -Append (Join-Path $salidas "plan-$Ambiente-$sello-contexto.txt")

Write-Host "3) Proveedores de recursos y cuotas de red ($Region)"
$proveedores = @("Microsoft.Network", "Microsoft.KeyVault", "Microsoft.Storage", "Microsoft.OperationalInsights",
    "Microsoft.Insights", "Microsoft.RecoveryServices", "Microsoft.Security", "Microsoft.SecurityInsights",
    "Microsoft.ManagedIdentity", "Microsoft.PolicyInsights", "Microsoft.Consumption", "Microsoft.HybridCompute")
foreach ($p in $proveedores) {
    $estado = az provider show --namespace $p --query registrationState --output tsv
    "$p : $estado" | Tee-Object -Append (Join-Path $salidas "plan-$Ambiente-$sello-contexto.txt")
}
az network list-usages --location $Region --query "[?currentValue>``0`` || contains(name.value,'PublicIP') || contains(name.value,'VirtualNetworks')].{recurso:name.localizedValue, uso:currentValue, limite:limit}" --output table |
    Tee-Object -Append (Join-Path $salidas "plan-$Ambiente-$sello-contexto.txt")

Write-Host "4) terraform init/validate/plan (sin apply)"
Push-Location $az
try {
    if ($UsarBackendRemoto) {
        terraform init -input=false -backend-config="environments\backend-$Ambiente.hcl"
    } else {
        terraform init -input=false -backend=false
    }
    terraform validate
    $planFile = Join-Path $salidas "plan-$Ambiente-$sello.tfplan"
    terraform plan -input=false -var-file="$varFile" -out="$planFile" | Tee-Object (Join-Path $salidas "plan-$Ambiente-$sello.txt")
    terraform show -json $planFile | Out-File -Encoding utf8 (Join-Path $salidas "plan-$Ambiente-$sello.json")
} finally { Pop-Location }

Write-Host "5) Revisión automática del plan y de costos"
python -X utf8 -I (Join-Path $PSScriptRoot "revisar_plan.py") (Join-Path $salidas "plan-$Ambiente-$sello.json") |
    Tee-Object (Join-Path $salidas "plan-$Ambiente-$sello-revision.txt")

Write-Host ""
Write-Host "PLAN GENERADO. NO se ejecutó apply. Adjunte la revisión al registro de cambios y solicite autorización."
