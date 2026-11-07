# Infraestructura Azure del SGSI UVCG — PREPARADA, NO DESPLEGADA

Terraform modular para la extensión híbrida del laboratorio SGSI de la UVCG. **No existe suscripción ni despliegue**:
todo lo que tiene costo está en `false` por defecto y nunca se ha ejecutado `apply`. Cierre y estado: `../CIERRE_AZURE.md`.
Evidencias: `../evidencias/azure/INDICE-AZURE.md`.

## Estructura

```
azure/
├── versions.tf            # Terraform >= 1.9, AzureRM ~> 4.0 (lock 4.81.0, sin actualizar)
├── providers.tf           # storage_use_azuread, sin plano de datos de Storage, registro acotado de proveedores
├── backend.tf             # backend azurerm DOCUMENTADO Y COMENTADO (sin estado en el repo)
├── variables.tf           # región restringida, 11 banderas enable_* de costo (false), SoD, políticas
├── locals.tf              # nombres <prefijo>-<ambiente>-<región>, etiquetas obligatorias, CIDR
├── main.tf / outputs.tf   # orquestación de módulos y salidas (incluye cost_features_enabled)
├── environments/          # dev (Escenario 1), demo (Escenario 2), inst (Escenario 3, referencia) + backend-dev.hcl.example
├── modules/
│   ├── networking/        # hub-spoke, subredes, NSG (Deny 4096), DMZ, UDR→firewall, DNS privado
│   ├── security/          # Key Vault (RBAC, privado, purge), Firewall, Bastion, App Gateway WAF_v2, Defender
│   ├── identity/          # identidades administradas, RBAC mínimo con separación de funciones
│   ├── monitoring/        # Log Analytics, actividad, Sentinel, action group, alertas, presupuesto
│   ├── storage/           # Storage privado (TLS1.2, sin shared keys, versionado, PE, ciclo de vida)
│   ├── backup/            # Recovery Services Vault + política
│   ├── hybrid-connectivity/ # VPN S2S IKEv2 opcional + rol de incorporación Azure Arc
│   └── policies/          # 15 asignaciones de Azure Policy integradas (GUID verificados)
├── tests/escenarios.tftest.hcl  # 5 pruebas con mock_provider (sin credenciales)
├── scripts/               # validación, precios, costos, inventario/diagramas, plan real y revisión
└── .tflint.hcl / .gitignore
```

## Banderas de costo (todas `false` por defecto)

`enable_monitoring`, `enable_sentinel`, `enable_alerts`, `enable_key_vault`, `enable_storage`, `enable_private_endpoints`,
`enable_backup`, `enable_vpn_gateway`, `enable_firewall`, `enable_bastion`, `enable_app_gateway`. Sin costo y activos por
defecto: red, NSG, políticas (`enable_policies`), presupuesto (`enable_budget`; **no bloquea el gasto**), identidades y
Defender for Cloud en nivel Free (`manage_defender_plans` actúa a nivel de **suscripción**).

## Validación sin credenciales (Docker, desde la raíz del repositorio, Git Bash)

```bash
bash azure/scripts/validar_terraform.sh 20261024            # fmt, init, validate, test x4, tflint, trivy
python -X utf8 -I azure/scripts/generar_inventario_diagrama.py  # inventario y Mermaid desde el código
python scripts/validar_terraform_estatico.py                 # verificación textual usada por validar_sgsi.ps1
```

Comandos individuales (PowerShell):

```powershell
docker run --rm -v "${PWD}/azure:/ws" -w /ws hashicorp/terraform:1.14 fmt -recursive -check
docker run --rm -v "${PWD}/azure:/ws" -w /ws hashicorp/terraform:1.14 init -backend=false
docker run --rm -v "${PWD}/azure:/ws" -w /ws hashicorp/terraform:1.14 validate
docker run --rm -v "${PWD}/azure:/ws" -w /ws hashicorp/terraform:1.14 test -var-file=environments/dev.tfvars.example
docker run --rm -v "${PWD}/azure:/src:ro" aquasec/trivy:0.76.1 config --tf-vars /src/environments/dev.tfvars.example /src
```

`terraform test` usa `mock_provider`: expande módulos, banderas, validaciones y precondiciones, pero **no es un plan real**.
`terraform plan` con AzureRM exige credenciales y suscripción (el intento sin ellas falla con
`unable to build authorizer`, registrado en la evidencia).

## Costos

Precios oficiales: `python -I azure/scripts/consultar_precios_azure.py evidencias/azure/precios-azure-<fecha>.json`
(API pública, sin autenticación) y `python -X utf8 -I azure/scripts/calcular_costos_escenarios.py`. Resultado del
2026-10-24 (eastus2): Escenario 1 = 16.90 USD/mes, Escenario 2 = 73.88 USD/mes, Escenario 3 = 2,962.96 USD/mes.

## Cuando exista suscripción (no antes)

1. Seguir `../evidencias/azure/PLAN-DESPLIEGUE-AZURE.md`.
2. Copiar `environments/<amb>.tfvars.example` → `<amb>.tfvars` (ignorado por git); `ARM_SUBSCRIPTION_ID` por entorno;
   PSK sólo en `TF_VAR_vpn_shared_key`.
3. `azure/scripts/generar_plan.ps1 -Ambiente dev -SuscripcionEsperada <guid> -TenantEsperado <guid>` (no aplica).
4. Revisión de costo, autorización y `terraform apply <plan aprobado>`; luego `PLAN-PRUEBAS-POST-DESPLIEGUE.md`.
5. Reducir costos con `../evidencias/azure/DESACTIVACION-SEGURA-AZURE.md`.

No ejecute `apply` ni `destroy` sin suscripción, presupuesto y autorización escrita.
