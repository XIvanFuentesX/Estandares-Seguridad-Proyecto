#!/usr/bin/env bash
# Validación estática y "plan simulado" (mock) de la infraestructura Azure, SIN credenciales.
# Requisitos: Docker. Usa contenedores efímeros (--rm) y no toca otros contenedores/volúmenes.
# Uso (Git Bash, desde la raíz del repositorio):
#   bash azure/scripts/validar_terraform.sh [AAAAMMDD]
# Salidas en evidencias/azure/.
set -u
export MSYS_NO_PATHCONV=1

FECHA="${1:-$(date +%Y%m%d)}"
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
AZ="$RAIZ/azure"
EV="$RAIZ/evidencias/azure"
TMP="$AZ/scripts/salidas"
mkdir -p "$EV" "$TMP"

# Ruta montable por Docker Desktop en Windows (D:/...) o POSIX en Linux.
if command -v cygpath >/dev/null 2>&1; then AZ_M="$(cygpath -m "$AZ")"; TMP_M="$(cygpath -m "$TMP")"; EV_M="$(cygpath -m "$EV")"; else AZ_M="$AZ"; TMP_M="$TMP"; EV_M="$EV"; fi

TF_IMG="hashicorp/terraform:1.14"
TRIVY_IMG="aquasec/trivy:0.76.1"
TFLINT_IMG="ghcr.io/terraform-linters/tflint:v0.59.1"
TF="docker run --rm -m 1g -v $AZ_M:/ws -w /ws $TF_IMG"
OUT="$EV/validacion-terraform-$FECHA.txt"
ENVS="dev demo inst"

: >"$OUT"
log() { echo "$*" | tee -a "$OUT"; }
run() { # run <descripcion> <comando...>
  local desc="$1"; shift
  log ""
  log "### $desc"
  log "\$ $*"
  "$@" >>"$OUT" 2>&1
  local rc=$?
  log "[exit=$rc]"
  return 0
}

log "VALIDACIÓN TERRAFORM — SGSI UVCG (Azure, NO desplegado)"
log "Fecha local: $(date '+%Y-%m-%d %H:%M:%S %z')"
log "Imágenes: $TF_IMG | $TFLINT_IMG | $TRIVY_IMG"
log "Alcance: sin credenciales, sin backend, sin suscripción. 'terraform test' usa mock_provider (no es un plan real)."

run "terraform version" $TF version
run "terraform fmt -recursive -check" $TF fmt -recursive -check -diff
run "terraform init -backend=false" $TF init -backend=false -input=false -no-color
run "terraform validate (raíz + módulos)" $TF validate -no-color
run "terraform test (valores por defecto)" $TF test -no-color
for e in $ENVS; do
  run "terraform test -var-file=environments/$e.tfvars.example" $TF test -no-color -var-file=environments/$e.tfvars.example
done

# Plan simulado detallado por escenario (para inventario; no se versiona el texto completo).
$TF test -no-color -verbose -var-file=environments/dev.tfvars.example >"$TMP/verbose-dev.txt" 2>&1
$TF test -no-color -verbose -var-file=environments/demo.tfvars.example >"$TMP/verbose-demo.txt" 2>&1
$TF test -no-color -verbose -var-file=environments/inst.tfvars.example >"$TMP/verbose-inst.txt" 2>&1
$TF test -no-color -verbose >"$TMP/verbose-default.txt" 2>&1
for f in default dev demo inst; do
  log "Plan simulado ($f): $(grep -m1 '^Plan:' "$TMP/verbose-$f.txt")"
done

# Intento de plan real: se espera fallo por falta de credenciales (documentado).
run "terraform plan (intento SIN credenciales; se espera error de autenticación)" $TF plan -input=false -no-color -lock=false -refresh=false -var-file=environments/dev.tfvars.example

# Grafo y valores locales para el diagrama.
$TF graph >"$TMP/graph.dot" 2>&1
echo 'jsonencode({hub=local.hub_subnets, spoke=local.spoke_subnets, name=local.name, kv=local.key_vault_name, st=local.storage_account_name, tags=local.tags})' |
  docker run --rm -i -m 1g -v "$AZ_M:/ws" -w /ws $TF_IMG console >"$TMP/locals.json" 2>&1

# TFLint (plugins en carpeta temporal).
mkdir -p "$TMP/tflint-plugins"
TFL="docker run --rm -m 512m -v $AZ_M:/data -v $TMP_M/tflint-plugins:/plugins -e TFLINT_PLUGIN_DIR=/plugins -w /data $TFLINT_IMG"
run "tflint --init" $TFL --init
run "tflint --version" $TFL --version
run "tflint (raíz con módulos locales)" $TFL --format compact
run "tflint --recursive" $TFL --recursive --config /data/.tflint.hcl --format compact

# Trivy (checks embebidos; sin descarga de actualizaciones).
TRV="docker run --rm -m 1g -v $AZ_M:/src:ro $TRIVY_IMG config --skip-check-update -q"
$TRV -f json /src >"$EV/trivy-config-azure.json" 2>"$TMP/trivy-default.err"
log ""
log "### trivy config azure (valores por defecto) -> evidencias/azure/trivy-config-azure.json"
for e in $ENVS; do
  $TRV -f json --tf-vars "/src/environments/$e.tfvars.example" /src >"$EV/trivy-config-azure-$e.json" 2>"$TMP/trivy-$e.err"
  log "### trivy config --tf-vars environments/$e.tfvars.example -> evidencias/azure/trivy-config-azure-$e.json"
done
python -X utf8 -I "$AZ_M/scripts/resumir_trivy.py" "$EV_M" 2>&1 | tee -a "$OUT"

log ""
log "Fin. Ninguna de estas pruebas crea, modifica ni consulta recursos en Azure."
