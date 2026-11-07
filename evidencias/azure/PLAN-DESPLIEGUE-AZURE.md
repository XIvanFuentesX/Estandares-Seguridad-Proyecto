# Plan de despliegue paso a paso (para cuando exista suscripción autorizada)

Principio: **nada se aplica sin plan revisado, costo estimado y autorización escrita**. Sólo se aplica lo aprobado.

| Paso | Acción | Comando / evidencia | Criterio de salida | Responsable |
|---|---|---|---|---|
| 0 | Autorización del alcance y presupuesto | Acta firmada (escenario, monto, ventana, responsables) | Escenario aprobado (1, 2 o subconjunto) | Responsable SGSI + Dirección |
| 1 | Herramientas | Instalar Azure CLI y Terraform ≥ 1.9, o usar contenedores (`mcr.microsoft.com/azure-cli`, `hashicorp/terraform:1.14`) | `az version`, `terraform version` | Operador de plataforma |
| 2 | Verificar identidad | `az login` (cuenta con MFA) ; `az account show` | Tenant y suscripción coinciden con el acta | Operador |
| 3 | Verificar permisos | `az role assignment list --assignee <upn> --all` | Contributor + RBAC Administrator acotado (o Owner temporal vía PIM) en la suscripción | Administrador de identidad |
| 4 | Registrar proveedores | `az provider register -n Microsoft.Network` (y los 14 de `providers.tf`) | `registrationState = Registered` | Operador |
| 5 | Cuotas | `az network list-usages -l eastus2 -o table`; cuota de IP públicas Standard | Uso + nuevo < límite | Operador |
| 6 | Backend de estado | Crear Storage de estado (ver `backend.tf`), rol de datos sólo en `tfstate`, copiar `backend-dev.hcl.example` | `terraform init -backend-config=...` exitoso | Operador + Seguridad |
| 7 | Variables | Copiar `environments/<amb>.tfvars.example` → `.tfvars` (ignorado); IDs de grupos en `principals`; `ARM_SUBSCRIPTION_ID` en entorno; PSK sólo en `TF_VAR_vpn_shared_key` | `git status` sin `.tfvars` | Operador |
| 8 | Validación estática | `bash azure/scripts/validar_terraform.sh` | fmt/validate/test/tflint OK; Trivy sin hallazgos nuevos | DevSecOps |
| 9 | Plan real | `azure/scripts/generar_plan.ps1 -Ambiente dev -SuscripcionEsperada ... -TenantEsperado ...` | Plan + `revisar_plan.py` sin destrucciones; recursos con costo = los aprobados | Operador |
| 10 | Revisión de costos | Comparar recursos del plan con `costos-escenarios-20261024.md`; actualizar precios con `consultar_precios_azure.py` | Diferencia explicada y ≤ presupuesto aprobado | Finanzas + SGSI |
| 11 | Autorización del plan | Registrar hash del archivo `.tfplan` en `REGISTRO-CAMBIOS-AZURE.md` | Firma de aprobación | CAB / Responsable SGSI |
| 12 | Apply del plan aprobado | `terraform apply <archivo.tfplan>` (sólo ese archivo; nunca `apply` sin plan) | Recursos creados = plan | Operador |
| 13 | Pruebas post-despliegue | `PLAN-PRUEBAS-POST-DESPLIEGUE.md` | Todas las pruebas con evidencia | Seguridad |
| 14 | Cierre o desactivación | `DESACTIVACION-SEGURA-AZURE.md` al terminar la ventana | Costo diario vuelve al mínimo | Operador |

Orden recomendado de habilitación (cada uno con su propio plan aprobado): (1) red + políticas + presupuesto + Defender Free;
(2) monitoring + alertas; (3) Key Vault + Storage + PE; (4) backup; (5) VPN sólo en ventana; (6) componentes institucionales.
Las asignaciones de Azure Policy con efecto *Deny* pueden bloquear despliegues mal etiquetados: aplicar primero en
`policy_effect = "Audit"` si el plan lo aconseja (las de ubicación, NIC y etiquetas son siempre Deny).
