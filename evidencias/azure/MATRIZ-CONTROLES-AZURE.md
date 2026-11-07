# Matriz de controles — componentes Azure del SGSI UVCG

Estado de implementación de **todas** las filas: *Preparado en Terraform, no desplegado* (salvo la columna "Evidencia
estática", que sí existe). Referencias: ISO/IEC 27001:2022 Anexo A (= ISO/IEC 27002:2022), NIST CSF 2.0, principios Zero
Trust de Microsoft (verificar explícitamente, mínimo privilegio, asumir brecha), ISO 22301:2019 (cláusulas), COBIT 2019
(objetivos de gestión), ITIL 4 (prácticas) y ANSI/TIA-942.

## 1. Matriz principal

| # | Componente (módulo) | Activo protegido | Riesgo tratado | ISO 27001/27002:2022 | NIST CSF 2.0 | Zero Trust | ISO 22301 | COBIT 2019 | ITIL 4 | Evidencia estática |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Hub-and-spoke, subredes por zona (networking) | Servicios académicos, datos (ACT-015) | RC-02, R-009, R-017 | A.8.20, A.8.22, A.8.27 | PR.IR-01, PR.PS-01 | Asumir brecha (microsegmentación) | — | DSS05.02, BAI03.02 | Infrastructure and platform mgmt; Information security mgmt | `modules/networking`, prueba `plan_simulado` (6 subredes) |
| 2 | NSG con allow explícito y Deny 4096 | Flujos DMZ→apps→datos | RC-02, R-009 | A.8.20, A.8.22, A.5.15 | PR.IR-01, PR.AA-05 | Mínimo privilegio de red | — | DSS05.02 | Information security mgmt | Prueba `Deny:4096` por zona |
| 3 | DMZ dedicada + App Gateway WAF_v2 (opcional) | Portal/API publicados | RC-02, R-001 | A.8.20, A.8.21, A.8.26, A.8.23 | PR.IR-01, DE.CM-01 | Verificar cada solicitud (WAF Prevención OWASP 3.2) | — | DSS05.02 | Information security mgmt | `modules/security`; Trivy AZU-0047 aceptado |
| 4 | UDR + Azure Firewall (opcional) | Tráfico este-oeste y salida | RC-02, RC-14 | A.8.20, A.8.21, A.8.22, A.8.23 | PR.IR-01, DE.CM-01 | Asumir brecha; inspección central | — | DSS05.02 | Monitoring and event mgmt | `azurerm_route_table` × 6 en inst |
| 5 | DNS privado (blob, vault) | Resolución de PaaS privados | RC-02 | A.8.20, A.8.21 | PR.IR-01 | Sin exposición pública | — | BAI03.02 | Infrastructure and platform mgmt | 2 zonas en dev/demo/inst |
| 6 | Private Endpoints | Key Vault, Storage | RC-02 | A.8.20, A.8.3, A.5.14 | PR.DS-02, PR.IR-01 | Acceso sólo por red privada verificada | — | DSS05.02, APO14 | Information security mgmt | PE blob + vault |
| 7 | Key Vault RBAC, sin acceso público, purge protection | Secretos/certificados (ACT-011 en la nube) | R-015, RC-05 | A.8.24, A.5.17, A.8.2, A.8.3 | PR.DS-01, PR.AA-05 | Mínimo privilegio; verificación explícita | 8.3 (protección de recursos críticos) | DSS05.03, APO13 | Information security mgmt | Prueba de endurecimiento KV |
| 8 | Identidades administradas | Credenciales de carga | RC-03, RC-05 | A.5.16, A.5.17, A.8.5 | PR.AA-01, PR.AA-03 | Sin secretos estáticos | — | DSS05.04 | Information security mgmt | `modules/identity` |
| 9 | RBAC por grupo con separación de funciones (lectores, auditores, red, respaldo, seguridad, costos) | Plano de control Azure | RC-04, R-016 | A.5.3, A.5.15, A.5.18, A.8.2 | PR.AA-05, GV.RR-02 | Mínimo privilegio | — | APO07, DSS05.04, DSS06.03 | Information security mgmt; Service configuration mgmt | Pruebas `separacion_de_funciones` y `rol_privilegiado_rechazado` |
| 10 | Azure Policy: ubicaciones, NIC sin IP pública, etiquetas, Storage/KV seguros | Toda la suscripción del laboratorio | RC-01, RC-02, RC-10, RC-11 | A.5.1, A.5.23, A.8.9, A.5.12, A.5.31 | GV.PO-01, PR.PS-01, ID.AM-08 | Verificar explícitamente (cumplimiento continuo) | — | APO01, BAI10, MEA03 | Service configuration mgmt; Change enablement | 11 GUID verificados; 15 asignaciones |
| 11 | Etiquetas obligatorias (proyecto, ambiente, propietario, clasificación, gestionado_por) | Inventario | RC-10 | A.5.9, A.5.12, A.5.13 | ID.AM-01, ID.AM-02, ID.AM-07 | Visibilidad | 8.2 (dependencias) | BAI09.01 | IT asset mgmt | Prueba de etiquetas |
| 12 | Defender for Cloud (Free; Standard opcional) | Cargas y host Arc | RC-16, R-013 | A.8.7, A.8.8, A.8.16 | ID.RA-01, DE.CM-09 | Asumir brecha (detección) | — | DSS05.01, APO12 | Monitoring and event mgmt; Information security mgmt | Trivy AZU-0045 aceptado |
| 13 | Log Analytics (≥ 30 d, tope diario) + diagnostic settings | Registros de seguridad | RC-08, R-012 | A.8.15, A.8.16, A.5.28, A.8.17 | PR.PS-04, DE.CM-01, DE.CM-03 | Visibilidad y analítica | 9.1 | DSS05.07, MEA01 | Monitoring and event mgmt | 11 diagnostic settings en inst |
| 14 | Registro de actividad de la suscripción | Operaciones de administración | RC-04, RC-10 | A.8.15, A.5.28 | DE.CM-03, PR.PS-04 | Verificar explícitamente | — | DSS05.07 | Monitoring and event mgmt | `diag-actividad-a-law` |
| 15 | Alertas (RBAC, políticas, NSG, KV, claves Storage, salud de servicio, fallos) + grupo de acciones | Integridad del plano de control | RC-04, RC-10 | A.5.24, A.5.25, A.8.16 | DE.AE-02, DE.AE-03, RS.MA-01 | Asumir brecha | 8.4 (alerta y comunicación) | DSS02.01, DSS05.07 | Incident mgmt; Monitoring and event mgmt | 8 alertas + 1 de consulta |
| 16 | Sentinel (opcional) | Correlación SIEM | R-012 | A.5.25, A.5.26, A.8.16 | DE.AE-02, DE.AE-06, RS.AN-03 | Visibilidad/automatización | — | DSS02, DSS05.07 | Incident mgmt | Sólo inst |
| 17 | Storage privado, sin anónimo, TLS 1.2, sin shared keys, versionado, borrado suave, ciclo de vida | Evidencias y copias cifradas (ficticias) | R-011, R-003, RC-02 | A.8.24, A.5.14, A.8.10, A.8.13, A.5.33 | PR.DS-01, PR.DS-02, PR.DS-11 | Proteger los datos | 8.3 | APO14, DSS04.07 | Information security mgmt; Service continuity mgmt | Prueba de endurecimiento Storage |
| 18 | Recovery Services Vault (inmutable *Unlocked*, alertas) | Respaldos (ACT-010/ACT-016) | R-011, R-014, R-019 | A.8.13, A.8.14, A.5.29, A.5.30 | PR.DS-11, RC.RP-03 | Asumir brecha (copias inmutables) | 8.3, 8.4, 8.5 | DSS04.07, DSS04.04 | Service continuity mgmt | `modules/backup` |
| 19 | VPN S2S IKEv2 AES-256/SHA-256/DH14 (opcional) | Canal híbrido | RC-06, RC-14 | A.8.20, A.8.21, A.8.24, A.5.14 | PR.DS-02, PR.IR-01 | Cifrado en tránsito; verificación de extremos | 8.3 | DSS05.02 | Infrastructure and platform mgmt | `ipsec_policy` explícita |
| 20 | Azure Arc (rol de incorporación mínimo) | Host Docker local | RC-14, R-013 | A.8.1, A.8.9, A.8.16, A.5.16 | ID.AM-01, DE.CM-09 | Identidad del dispositivo | — | BAI10, DSS05.03 | IT asset mgmt; Service configuration mgmt | Rol `Azure Connected Machine Onboarding` |
| 21 | Presupuesto + alertas (no bloquea gasto) | Recursos financieros del proyecto | RC-01 | A.5.1 (política de uso), A.8.6 | GV.RR-03, GV.OV-03 | — | 7.1 (recursos) | APO06.02, APO06.05 | Service financial mgmt | `budget-*` |
| 22 | Banderas de costo `false` + prueba `valores_por_defecto_sin_costo` | Recursos financieros | RC-01 | A.8.32, A.8.6 | GV.RM-03, PR.PS-01 | — | — | BAI06, APO06 | Change enablement | 5/5 pruebas por escenario |
| 23 | Backend remoto documentado (Entra ID, sin claves) | Estado de Terraform | RC-05 | A.8.4, A.8.9, A.5.33 | PR.DS-01, PR.PS-01 | Mínimo privilegio | — | BAI10.02 | Service configuration mgmt | `backend.tf` comentado; `.gitignore` |
| 24 | Validación IaC (fmt, validate, test, tflint, Trivy) | Código de infraestructura | RC-10, R-017 | A.8.25, A.8.29, A.8.32, A.8.9 | PR.PS-06, ID.IM-02 | Verificar explícitamente | — | BAI03.08, BAI07 | Change enablement; Deployment mgmt | `validacion-terraform-20261024.txt` |
| 25 | Región restringida (eastus2/southcentralus) | Datos (residencia) | RC-11 | A.5.31, A.5.34, A.5.23 | GV.OC-03 | — | — | MEA03.01 | Risk mgmt | Prueba `region_no_permitida` |

## 2. Controles no aplicables o parciales (justificación)

| Marco / control | Decisión | Justificación |
|---|---|---|
| ISO 27001 A.7.1–A.7.14 (seguridad física) para Azure | **No aplicable a UVCG** (responsabilidad del proveedor) | Modelo de responsabilidad compartida: los centros de datos son de Microsoft. Se trata mediante A.5.19–A.5.23 (revisión de informes de cumplimiento del proveedor: **no obtenidos**). Siguen aplicando al host local (R-014). |
| ISO 27001 A.8.11 (enmascaramiento) | No aplicable en Azure | Sólo se transfieren datos ficticios cifrados; no hay consultas sobre datos personales en Azure. |
| ISO 27001 A.8.28 (codificación segura) | No aplicable a este módulo | No se despliega código de aplicación en Azure (la API sigue local). |
| ISO 27001 A.6.x (personas) | Fuera del alcance técnico | Se gestionan en el SGSI general (`governance/`). |
| **ANSI/TIA-942** (Rated 1–4: arquitectura, eléctrico, mecánico, telecomunicaciones) | **No aplicable** a Azure ni al laboratorio | Azure: infraestructura física del proveedor, no auditable por UVCG. Laboratorio: un equipo Windows con Docker Desktop no es un centro de datos. Sólo se toma su principio de redundancia de telecomunicaciones como recomendación (doble enlace para la VPN institucional, RC-09). |
| ISO 22301 cláusulas 4–7 (contexto, liderazgo, planificación, soporte) | Parcial | Se cubren en `governance/bcp.md`/`bia.md`; aquí sólo se aportan estrategias 8.3/8.4 y ejercicios 8.5. |
| NIST CSF RC.CO (comunicación de recuperación) | Parcial | El grupo de acciones notifica; no hay plan de comunicación cloud aprobado. |
| COBIT APO10 (proveedores) | Parcial | No hay contrato ni acuerdo con Microsoft (sin suscripción). |
| Acceso Condicional / PIM (A.5.15, A.8.2, A.8.5) | **No implementable** sin Entra ID P1/P2 | Dependencia de licencia (RC-15). |
| Cifrado con clave del cliente (CMK) en Storage (A.8.24) | No implementado (hallazgo Trivy AZU-0060 aceptado) | Claves gestionadas por Microsoft + cifrado de infraestructura; CMK agrega costo y operación de claves. Recomendado para escenario institucional. |
