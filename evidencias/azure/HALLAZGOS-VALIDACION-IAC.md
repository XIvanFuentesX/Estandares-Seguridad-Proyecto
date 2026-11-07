# Hallazgos de la validación IaC y su tratamiento

Salidas reales: `validacion-terraform-20261024.txt`, `trivy-config-azure*.json`, `politicas-integradas-verificadas-20261024.txt`.
Herramientas: Terraform 1.14.9 + AzureRM 4.81.0, TFLint 0.59.1 + ruleset azurerm 0.28.0, Trivy 0.76.1 (checks embebidos,
sin actualización en línea), todos en contenedores efímeros.

## 1. Resultados

| Verificación | Resultado real |
|---|---|
| `terraform fmt -recursive -check` | exit 0 (sin diferencias) |
| `terraform init -backend=false` | exit 0; reutiliza AzureRM 4.81.0 del lock (no se actualizó) |
| `terraform validate` (raíz + 8 módulos) | `Success! The configuration is valid.` |
| `terraform test` con mock (defecto, dev, demo, inst) | 4 × `5 passed, 0 failed` (20/20) |
| Plan simulado (mock) | defecto 63, dev 100, demo 103, inst 139 recursos a crear |
| `terraform plan` real | **No posible**: `unable to build authorizer ... "az": executable file not found` (sin credenciales ni suscripción) |
| TFLint (raíz con módulos y `--recursive`) | 0 problemas (control de sensibilidad: el mismo linter detectó 4 problemas en un archivo de prueba deliberadamente defectuoso) |
| Trivy `config` valores por defecto | 65 exitosos, 4 fallidos (4 LOW) |
| Trivy con `dev.tfvars.example` | 68 exitosos, 8 fallidos (6 LOW, 2 MEDIUM) |
| Trivy con `demo.tfvars.example` | 68 exitosos, 7 fallidos (5 LOW, 2 MEDIUM) |
| Trivy con `inst.tfvars.example` | 69 exitosos, 4 fallidos (1 CRITICAL, 1 LOW, 2 MEDIUM) |
| Definiciones de Azure Policy | 11/11 GUID verificados contra el repositorio oficial `Azure/azure-policy` |
| `scripts/validar_terraform_estatico.py` | 32 líneas `OK`, exit 0 |

## 2. Problemas encontrados y corregidos durante la validación

| Herramienta | Problema | Corrección |
|---|---|---|
| `terraform fmt -check` (1.ª ejecución) | 4 archivos sin formato (`locals.tf`, `modules/identity/variables.tf`, `modules/monitoring/main.tf`, `modules/networking/main.tf`) | `terraform fmt -recursive` |
| `terraform validate` | Bloque `features.recovery_service` incompleto y luego con dos opciones mutuamente excluyentes | Se dejó sólo `vm_backup_stop_protection_and_retain_data_on_destroy = true` |
| `terraform test` (mock) | `Inconsistent conditional result types` en `modules/policies` (parámetros heterogéneos) | Parámetros serializados con `jsonencode` y filtro `if var.enable_policies` |
| Diseño | El primer escaneo de Trivy sólo evaluaba los valores por defecto (recursos con `count = 0`) | Escaneo adicional con `--tf-vars` por ambiente |

## 3. Hallazgos aceptados (no corregidos) con justificación

| ID Trivy | Severidad | Escenarios | Hallazgo | Decisión | Justificación / control compensatorio |
|---|---|---|---|---|---|
| AZU-0045 | LOW | defecto, dev, demo | Defender for Cloud en nivel Free | **Aceptado** | Requisito del proyecto: Free por defecto para no generar costo; Standard configurable por `defender_plans` (demo usa Standard en servidores; inst en todos). |
| AZU-0046 | LOW | dev, demo, inst | Contacto de seguridad sin teléfono | **Aceptado** | Se usa buzón institucional; no se publican teléfonos personales en el repositorio. |
| AZU-0057 | MEDIUM | dev, demo, inst | Storage sin *logging* clásico (Storage Analytics de colas) | **Aceptado** | Se usa la configuración de diagnóstico moderna (Azure Monitor) para blob (`audit` + `Transaction`). Configurar `queue_properties` exige plano de datos, incompatible con red pública deshabilitada y sin claves. |
| AZU-0058 | LOW | dev, demo | Replicación LRS | **Aceptado** | Costo académico; GRS en el escenario institucional; la copia primaria sigue en el laboratorio local (dos ubicaciones). |
| AZU-0060 | MEDIUM | dev, demo, inst | Sin claves administradas por el cliente (CMK) | **Aceptado con plan** | Claves de Microsoft + cifrado de infraestructura (doble). Los respaldos ya llegan cifrados AES-256 desde el origen. CMK recomendado para el escenario institucional real (requiere clave en Key Vault, identidad y rotación). |
| AZU-0047 | CRITICAL | inst | Regla NSG permite 443 desde Internet | **Aceptado por diseño** | Es la entrada pública del Application Gateway WAF_v2 (modo Prevención, OWASP 3.2) en la DMZ dedicada; sólo existe con `enable_app_gateway = true` y no llega a ningún servicio Docker local. |

## 4. Limitaciones de la validación

- La validación es estática y simulada. No sustituye `terraform plan` contra una suscripción (nombres globales, cuotas,
  registro de proveedores, compatibilidad de SKU en la región y efecto real de Azure Policy quedan sin verificar).
- Trivy usó sus checks embebidos (no se descargó el paquete de checks más reciente).
- TFLint azurerm valida valores enumerados conocidos; no valida lógica de seguridad.
