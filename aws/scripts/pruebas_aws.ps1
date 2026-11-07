# Pruebas reales tras el despliegue (requiere sesión temporal `aws login`). No borra objetos ni recursos.
# Resultado: evidencias/aws/pruebas-aws-<fecha>.json con estado exitoso/fallido por prueba.
$ErrorActionPreference = "Continue"
. (Join-Path $PSScriptRoot "comun.ps1")
$aws = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$root = (Resolve-Path (Join-Path $aws "..")).Path
$out = Join-Path $root "evidencias\aws"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$results = [System.Collections.Generic.List[object]]::new()
function Add([string]$Id, [bool]$Ok, [string]$Detail) {
    $results.Add([ordered]@{ prueba = $Id; estado = $(if ($Ok) { "exitoso" } else { "fallido" }); detalle = $Detail })
    Write-Output ("[{0}] {1} {2}" -f $(if ($Ok) { "OK" } else { "FALLO" }), $Id, $Detail)
}
function Use-Role([string]$Arn) {
    $c = (aws sts assume-role --role-arn $Arn --role-session-name "uvcg-prueba-$stamp" --output json | ConvertFrom-Json).Credentials
    $env:AWS_ACCESS_KEY_ID = $c.AccessKeyId; $env:AWS_SECRET_ACCESS_KEY = $c.SecretAccessKey; $env:AWS_SESSION_TOKEN = $c.SessionToken
}
function Test-Denied([scriptblock]$Command) {
    $text = (& $Command 2>&1 | Out-String)
    return ($text -match "AccessDenied|Forbidden|403")
}
function Reset-Role { Remove-Item Env:\AWS_ACCESS_KEY_ID, Env:\AWS_SECRET_ACCESS_KEY, Env:\AWS_SESSION_TOKEN -ErrorAction SilentlyContinue }

$tf = Get-Content (Join-Path $aws "terraform.tfstate") -Raw | ConvertFrom-Json
$bucket = $tf.outputs.bucket_name.value
$uploader = $tf.outputs.uploader_role_arn.value
$auditor = $tf.outputs.auditor_role_arn.value
$region = (aws s3api get-bucket-location --bucket $bucket --query LocationConstraint --output text)
if (-not $region -or $region -eq "None") { $region = "us-east-1" }

# 1. Existencia y configuración de seguridad (identidad administradora de la sesión)
aws s3api head-bucket --bucket $bucket 2>$null; Add "PT-AWS-01 bucket existe" ($LASTEXITCODE -eq 0) $bucket
$pab = aws s3api get-public-access-block --bucket $bucket --output json | ConvertFrom-Json
$c = $pab.PublicAccessBlockConfiguration
Add "PT-AWS-02 bloqueo de acceso público" ($c.BlockPublicAcls -and $c.BlockPublicPolicy -and $c.IgnorePublicAcls -and $c.RestrictPublicBuckets) ($c | ConvertTo-Json -Compress)
$enc = aws s3api get-bucket-encryption --bucket $bucket --output json | ConvertFrom-Json
Add "PT-AWS-03 cifrado por defecto SSE-S3" ($enc.ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm -eq "AES256") "AES256"

# 2. Transferencia cifrada (TLS + SSE) de un archivo FICTICIO ya cifrado localmente con AES-256
New-Item -ItemType Directory -Force -Path (Join-Path $aws "salidas") | Out-Null
$sampleRel = "salidas/uvcg-ficticio-$stamp.txt"; $sample = Join-Path $aws $sampleRel
"CLASIFICACION: INTERNA`nMUESTRA FICTICIA para la prueba híbrida AWS ($stamp). Sin datos reales." | Set-Content -Encoding UTF8 $sample
$localHash = (Get-FileHash $sample).Hash.ToLower()
Use-Role $uploader
aws s3api put-object --bucket $bucket --key "laboratorio/prueba-$stamp.txt" --body $sample --output json | Out-Null
Add "PT-AWS-04 carga por HTTPS con rol de carga" ($LASTEXITCODE -eq 0) "laboratorio/prueba-$stamp.txt"
$dlRel = "salidas/uvcg-descarga-$stamp.txt"; $dl = Join-Path $aws $dlRel
$head = aws s3api get-object --bucket $bucket --key "laboratorio/prueba-$stamp.txt" $dl --output json | ConvertFrom-Json
Add "PT-AWS-05 integridad SHA-256 y SSE en reposo" (((Get-FileHash $dl).Hash.ToLower() -eq $localHash) -and $head.ServerSideEncryption -eq "AES256") "sha256=$localHash sse=$($head.ServerSideEncryption)"

# 3. Accesos denegados esperados (mínimo privilegio)
Add "PT-AWS-06 carga fuera de prefijo denegada" (Test-Denied { aws s3api put-object --bucket $bucket --key "otro-prefijo/x.txt" --body $sample }) "otro-prefijo/"
Add "PT-AWS-07 borrado denegado al rol de carga" (Test-Denied { aws s3api delete-object --bucket $bucket --key "laboratorio/prueba-$stamp.txt" }) "s3:DeleteObject"
Add "PT-AWS-08 transporte sin TLS denegado" (Test-Denied { aws s3api put-object --bucket $bucket --key "laboratorio/http-$stamp.txt" --body $sample --endpoint-url "http://s3.$region.amazonaws.com" }) "aws:SecureTransport=false"
Reset-Role
Use-Role $auditor
Add "PT-AWS-09 auditor sin acceso a objetos" (Test-Denied { aws s3api get-object --bucket $bucket --key "laboratorio/prueba-$stamp.txt" $dl }) "s3:GetObject denegado"
aws s3api get-bucket-policy --bucket $bucket --output json | Out-Null
Add "PT-AWS-10 auditor lee la configuración" ($LASTEXITCODE -eq 0) "s3:GetBucketPolicy"
Reset-Role
$anon = & curl.exe --silent --output NUL --write-out "%{http_code}" "https://$bucket.s3.$region.amazonaws.com/laboratorio/prueba-$stamp.txt"
Add "PT-AWS-11 acceso anónimo denegado" ($anon -eq "403") "HTTP $anon"

# 4. Registro (historial de eventos de CloudTrail, gratuito 90 días) y costo
$events = aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole --max-results 5 --output json | ConvertFrom-Json
Add "PT-AWS-12 eventos AssumeRole registrados en CloudTrail" (@($events.Events).Count -gt 0) "eventos=$(@($events.Events).Count) (puede tardar hasta 15 min)"
$plan = aws freetier get-account-plan-state --output json | ConvertFrom-Json
Add "PT-AWS-13 cuenta sigue en plan FREE" ($plan.accountPlanType -eq "FREE" -and $plan.accountPlanStatus -eq "ACTIVE") "creditos=$($plan.accountPlanRemainingCredits.amount)"

Remove-Item $sample, $dl -ErrorAction SilentlyContinue
$report = [ordered]@{ timestamp = (Get-Date).ToString("o"); bucket = $bucket; resultados = $results
    exitosos = @($results | Where-Object estado -eq "exitoso").Count; fallidos = @($results | Where-Object estado -eq "fallido").Count
    nota = "Transferencia por Internet con TLS e identidad temporal; NO equivale a una VPN híbrida privada." }
$report | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $out "pruebas-aws-$stamp.json")
Write-Output "exitosos=$($report.exitosos) fallidos=$($report.fallidos)"
