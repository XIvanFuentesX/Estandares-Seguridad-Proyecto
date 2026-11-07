param(
    # Días mínimos de vigencia restante del plan Free para permitir el despliegue.
    [int]$MinDaysRemaining = 7
)

# Verifica identidad, plan Free y créditos con credenciales TEMPORALES (`aws login`, CLI >= 2.32).
# Sólo lectura: GetCallerIdentity y freetier Get* (sin costo según la documentación de AWS).
# NUNCA llama a freetier UpgradeAccountPlan. Escribe evidencias/aws/verificacion-cuenta-<fecha>.json
# con el ID de cuenta parcialmente enmascarado.
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "comun.ps1")
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$out = Join-Path $root "evidencias\aws"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$result = [ordered]@{ timestamp = (Get-Date).ToString("o"); checks = [ordered]@{}; eligible = $false }

function Fail([string]$Reason) {
    $result.reason = $Reason
    $result | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $out "verificacion-cuenta-$stamp.json")
    Write-Output "NO ELEGIBLE: $Reason"
    exit 1
}

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) { Fail "AWS CLI no disponible (ni instalado ni vía Docker)." }
$version = (aws --version) -join ""
$result.checks.cli_version = $version

$identity = aws sts get-caller-identity --output json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or -not $identity) { Fail "Sin sesión válida: ejecute 'aws login' (credenciales temporales)." }
$result.checks.account_masked = $identity.Account.Substring(0, 4) + "****" + $identity.Account.Substring(8)
$result.checks.principal_type = ($identity.Arn -split ":")[5] -replace "/.*", ""
if ($identity.Arn -match ":root$") { $result.checks.warning_root = "Sesión con usuario raíz: se recomienda un usuario IAM/Identity Center con MFA." }

$state = aws freetier get-account-plan-state --output json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or -not $state) { Fail "No se pudo leer el estado del plan (freetier:GetAccountPlanState)." }
$result.checks.plan_type = $state.accountPlanType
$result.checks.plan_status = $state.accountPlanStatus
$result.checks.remaining_credits = $state.accountPlanRemainingCredits
$result.checks.expiration = $state.accountPlanExpirationDate
if ($state.accountPlanType -ne "FREE") { Fail "La cuenta NO está en plan Free (tipo=$($state.accountPlanType)): un despliegue podría generar cargos." }
if ($state.accountPlanStatus -ne "ACTIVE") { Fail "El plan Free no está activo (estado=$($state.accountPlanStatus))." }
if ([double]$state.accountPlanRemainingCredits.amount -le 1) { Fail "Créditos insuficientes ($($state.accountPlanRemainingCredits.amount))." }
$days = ([datetime]$state.accountPlanExpirationDate - (Get-Date)).TotalDays
$result.checks.days_remaining = [math]::Round($days, 1)
if ($days -lt $MinDaysRemaining) { Fail "El plan vence en $([math]::Round($days,1)) días (< $MinDaysRemaining)." }

$result.eligible = $true
$result.note = "Plan Free activo: AWS documenta que no se generan cargos. Comparar manualmente los créditos con la consola de Billing (Créditos y Página de inicio) y registrar cualquier diferencia antes de desplegar."
$file = Join-Path $out "verificacion-cuenta-$stamp.json"
$result | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $file
Write-Output "ELEGIBLE: plan=FREE estado=ACTIVE creditos=$($state.accountPlanRemainingCredits.amount) $($state.accountPlanRemainingCredits.unit) vence=$($state.accountPlanExpirationDate) evidencia=$file"
