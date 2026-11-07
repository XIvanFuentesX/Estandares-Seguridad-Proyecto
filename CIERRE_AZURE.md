# Cierre del componente Azure — SGSI UVCG

Fecha: 2026-10-24. Responsable técnico: equipo del proyecto SGSI.
**Resultado: infraestructura Azure PREPARADA y validada de forma estática. NINGÚN servicio está desplegado.**
No existe suscripción; no se ejecutó `az login`, `terraform plan` contra Azure, `apply` ni `destroy`; no se generaron costos.

## 1. Arquitectura final

- Región `eastus2` (alternativa permitida: `southcentralus`), restringida por validación de variable y por Azure Policy.
- Hub `10.20.0.0/16` (gestión, GatewaySubnet, AzureFirewallSubnet + Management, AzureBastionSubnet) y spoke académico
  `10.21.0.0/16` (dmz, apps, datos, gestion, seguridad, privateendpoints) con peering bidireccional.
- NSG por zona: dmz→apps 443, apps→datos 5432, red privada→PE 443; Deny 4096 en todas; datos/PE sin salida a Internet.
- UDR al Azure Firewall (opcional), DNS privado para blob y vault, Key Vault RBAC privado con purge protection,
  Storage privado sin shared keys, Recovery Services Vault, Log Analytics + actividad + alertas + presupuesto,
  Sentinel/Firewall/Bastion/App Gateway WAF_v2/VPN opcionales, Azure Arc como vía híbrida de bajo costo, 15 políticas.
- Código: raíz + 8 módulos en `azure/` (ver `azure/README.md`); diagramas en `evidencias/azure/ARQUITECTURA-AZURE.md`.

## 2. Estado de los recursos

| Recurso / módulo | Estado |
|---|---|
| Grupo de recursos, VNets, subredes, NSG, peering, UDR, DNS privado | PREPARADO / no desplegado |
| Key Vault, Private Endpoints, Azure Firewall, Bastion, App Gateway WAF_v2, Defender for Cloud | PREPARADO / no desplegado |
| Identidades administradas y asignaciones RBAC | PREPARADO / no desplegado |
| Log Analytics, registro de actividad, Sentinel, grupo de acciones, alertas, presupuesto | PREPARADO / no desplegado |
| Storage privado y Recovery Services Vault | PREPARADO / no desplegado |
| VPN S2S y rol de incorporación Azure Arc | PREPARADO / no desplegado |
| Asignaciones de Azure Policy | PREPARADO / no desplegado |
| Backend remoto de estado | DOCUMENTADO (comentado) / no creado |

**Servicios desplegados: ninguno.** Servicios sólo preparados: todos los anteriores (63 recursos en el plan simulado por
defecto; 100 en Escenario 1, 103 en Escenario 2, 139 en Escenario 3 — `evidencias/azure/inventario-recursos-escenarios.md`).

## 3. Pruebas estáticas ejecutadas (resultados reales)

| Prueba | Resultado |
|---|---|
| `terraform fmt -recursive -check` | OK (exit 0) tras corregir 4 archivos en la primera ejecución |
| `terraform init -backend=false` | OK; AzureRM 4.81.0 del lock |
| `terraform validate` | `Success! The configuration is valid.` |
| `terraform test` con mock (defecto, dev, demo, inst) | 20/20 pruebas exitosas (5 por escenario) |
| `terraform plan` real | No ejecutable: falla de autenticación sin credenciales (registrado) |
| TFLint 0.59.1 + azurerm 0.28.0 | 0 problemas |
| Trivy 0.76.1 `config` | defecto 4 LOW; dev 8 (6 LOW, 2 MEDIUM); demo 7 (5 LOW, 2 MEDIUM); inst 4 (1 CRITICAL, 1 LOW, 2 MEDIUM) — todos aceptados con justificación |
| Azure Policy | 11/11 GUID verificados en `Azure/azure-policy` |
| `scripts/validar_terraform_estatico.py` | 32 OK, exit 0 |

## 4. Evidencias

`evidencias/azure/`: `validacion-terraform-20261024.txt`, `trivy-config-azure*.json`, `HALLAZGOS-VALIDACION-IAC.md`,
`politicas-integradas-verificadas-20261024.txt`, `precios-azure-20261024.json`, `comparacion-regiones-20261024.txt`,
`costos-escenarios-20261024*.md/.json`, `inventario-recursos-escenarios.*`, `diagrama-*.mmd` y los documentos listados en
`INDICE-AZURE.md`. No hay capturas del portal (no existe despliegue).

## 5. Costos (API pública oficial de precios, consulta 2026-10-24 16:52 UTC, USD minorista, 730 h/mes)

| Escenario | eastus2 | southcentralus |
|---|---:|---:|
| 1. Mínimo académico | 16.90 | 16.90 |
| 2. Académico recomendado (VPN 40 h) | 73.88 | 73.88 |
| 3. Institucional de referencia (24x7) | 2,962.96 | 3,076.32 |

Detalle, fórmulas, gratuidades (verificadas y no verificadas) y licencias (Entra ID P1/P2, Intune: precio no verificado)
en `evidencias/azure/ANALISIS-COSTOS-AZURE.md`. El presupuesto de Azure **no bloquea** el gasto.

## 6. Seguridad

Mínimo privilegio y separación de funciones validados en código; sin secretos en `.tf`/`.tfvars`/salidas (PSK sólo por
`TF_VAR_vpn_shared_key`); sin estado en el repositorio; PaaS sólo por endpoint privado; políticas Deny; registro centralizado.
Riesgos residuales RC-01…RC-16 en `evidencias/azure/RIESGOS-CLOUD.md`; matriz de controles en `MATRIZ-CONTROLES-AZURE.md`.

## 7. Integración híbrida

Diseño en `evidencias/azure/INTEGRACION-HIBRIDA.md`: Azure Arc (saliente, 0 USD/h de plano de control) como base, VPN S2S
IKEv2 sólo en ventana de demostración y transferencia de respaldos **ya cifrados** de datos **ficticios** a un contenedor
privado con identidad administrada. Un endpoint HTTPS en localhost **no** es conectividad híbrida. No se probó.

## 8. Limitaciones

- Sin suscripción: sin plan real, sin despliegue, sin pruebas post-despliegue, sin costo real medido.
- El plan simulado (mock) no valida nombres globales, cuotas, permisos, disponibilidad de SKU ni efectos reales de Policy.
- Latencia desde Guatemala no medida; Bastion Developer y varias gratuidades no verificables en la API.
- Acceso Condicional, PIM e Intune dependen de licencias no disponibles.

## 9. Autorizaciones pendientes

1. Suscripción Azure (o de educación) y responsable de facturación.
2. Escenario y presupuesto mensual aprobados (recomendado: Escenario 2, presupuesto 60–80 USD).
3. Ventana para la VPN y autorización de cambios en el router del laboratorio.
4. Uso de datos ficticios en EE. UU. (residencia, RC-11).
5. Aprobación del plan concreto (hash del `.tfplan`) antes de cada `apply`.

## 10. Criterios de finalización del componente Azure

Criterios del encargo (sección 14), evaluados con honestidad. La implementación cloud **no se declara terminada**.

| # | Criterio del encargo | Estado | Evidencia o motivo |
|---|---|---|---|
| 1 | Recursos desplegados con autorización | **No cumple** | Sin suscripción ni autorización; no hay recursos reales |
| 2 | Configuraciones verificadas | **Parcial** | Sólo estáticamente: `fmt`, `validate`, `terraform test` 20/20 con proveedor simulado, TFLint 0, Trivy con hallazgos justificados; sin verificación contra recursos reales |
| 3 | Conectividad híbrida demostrada | **No cumple** | Diseño en `evidencias/azure/INTEGRACION-HIBRIDA.md`; requiere despliegue |
| 4 | Identidad y accesos comprobados | **No cumple** | RBAC, grupos y MFA modelados en el módulo `identity`; sin tenant |
| 5 | Monitoreo operativo | **No cumple** | Log Analytics, alertas y diagnósticos modelados; sin despliegue |
| 6 | Respaldo y restauración comprobados | **No cumple** en Azure | Comprobados sólo en el laboratorio local (`CIERRE_LABORATORIO_LOCAL.md`) |
| 7 | Evidencias técnicas existentes | **Parcial** | Evidencias de validación estática y costos; plantillas de pruebas post-despliegue vacías; sin capturas del portal (no se fabricaron) |
| 8 | Costos registrados | **Parcial** | Estimados con la API oficial de precios (2026-10-24); el costo real no existe hasta desplegar |
| 9 | Riesgos residuales documentados | **Cumple** | `evidencias/azure/RIESGOS-CLOUD.md` (RC-01…16), `HALLAZGOS-VALIDACION-IAC.md` |
| 10 | Requisitos de la arquitectura evaluados | **Cumple** (diseño) | `evidencias/azure/MATRIZ-CONTROLES-AZURE.md`, `ARQUITECTURA-AZURE.md` |

## 11. Acciones que debe realizar el usuario para permitir el despliegue real

1. **Suscripción**: crear o solicitar una suscripción (pago por uso o de educación) dedicada al laboratorio; anotar tenant y suscripción fuera del repositorio.
2. **Rol**: asignar a la cuenta operadora (con MFA) *Contributor* + *Role Based Access Control Administrator* acotado a la suscripción (o *Owner* temporal mediante PIM si hay P2); crear los grupos de Entra ID de `principals`.
3. **Registro de proveedores**: `az provider register -n <espacio>` para los 14 espacios de `azure/providers.tf` (o dejar que Terraform registre el conjunto `core` + lista).
4. **Cuotas**: `az network list-usages -l eastus2 -o table` (IP públicas Standard, VNets) y solicitar aumento si hace falta.
5. **Herramientas**: instalar Azure CLI y Terraform ≥ 1.9 en el host, o usar contenedores (`mcr.microsoft.com/azure-cli` para `az login` y `hashicorp/terraform:1.14` con `ARM_*` o identidad federada).
6. **Backend**: crear el Storage de estado según `azure/backend.tf`, descomentar el bloque y copiar `environments/backend-dev.hcl.example`.
7. **Variables**: copiar `environments/dev.tfvars.example` (o `demo`) a `.tfvars`, rellenar `principals`, correos y, si aplica, `onprem_gateway_address`; `ARM_SUBSCRIPTION_ID` y `TF_VAR_vpn_shared_key` sólo como variables de entorno.
8. **Presupuesto**: fijar `budget_amount`/`budget_start_date` y correos; recordar que sólo notifica.
9. **Revisar el plan**: `azure/scripts/generar_plan.ps1 ...` → revisar `plan-*-revision.txt`; actualizar precios con `consultar_precios_azure.py` y comparar con `costos-escenarios-*.md`.
10. **Autorizar**: firmar el registro `CAM-AZ-0xx` con el hash del plan; sólo entonces `terraform apply <plan>`; ejecutar `PLAN-PRUEBAS-POST-DESPLIEGUE.md` y desactivar al terminar la ventana.
