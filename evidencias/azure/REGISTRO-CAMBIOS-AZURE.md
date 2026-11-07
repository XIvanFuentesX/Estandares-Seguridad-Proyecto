# Registro de cambios — infraestructura Azure (IaC)

| ID | Fecha | Tipo | Descripción | Archivos | Validación | Riesgo | Aprobación | Estado en Azure |
|---|---|---|---|---|---|---|---|---|
| CAM-AZ-001 | 2026-10-24 (previo) | Creación | `azure/main.tf` monolítico (RG, hub/spoke, NSG, LAW/backup/VPN opcionales) | `azure/main.tf` | `terraform validate` OK (`evidencias/azure-terraform-validate-20261024.txt`) | R-017 | No requerida (sin despliegue) | No desplegado |
| CAM-AZ-002 | 2026-10-24 | Reestructuración | Raíz modular + 8 módulos; región restringida; ambientes dev/demo/inst; backend documentado; `.gitignore` ampliado | `azure/**` | fmt/validate/test 20/20, TFLint 0, Trivy (ver hallazgos) | RC-01…RC-16 | No requerida (sin despliegue) | No desplegado |
| CAM-AZ-003 | 2026-10-24 | Seguridad | Key Vault RBAC/privado/purge, Storage privado sin shared keys, PE + DNS privado, 15 asignaciones de Policy, SoD | `modules/security`, `storage`, `networking`, `policies`, `identity` | Pruebas de endurecimiento en `tests/` | RC-02, RC-04 | — | No desplegado |
| CAM-AZ-004 | 2026-10-24 | Monitoreo/costo | LAW, registro de actividad, Sentinel opcional, 8 alertas + consulta, presupuesto | `modules/monitoring` | idem | RC-01, RC-08 | — | No desplegado |
| CAM-AZ-005 | 2026-10-24 | Herramientas | Scripts de validación, precios, costos, inventario/diagramas, plan y revisión de plan | `azure/scripts/*`, `scripts/validar_terraform_estatico.py` | Ejecutados; salidas en `evidencias/azure/` | — | — | N/A |

## Plantilla para cambios futuros (despliegue o desactivación)

| Campo | Valor |
|---|---|
| ID | CAM-AZ-0xx |
| Solicitante / aprobador | |
| Ambiente y escenario | |
| Archivo de plan y hash SHA-256 | |
| Recursos a crear / cambiar / destruir (de `revisar_plan.py`) | |
| Costo mensual estimado (fuente y fecha de precios) | |
| Ventana y plan de reversión | |
| Pruebas post-cambio (PT-AZ-xx) | |
| Resultado y evidencia | |
