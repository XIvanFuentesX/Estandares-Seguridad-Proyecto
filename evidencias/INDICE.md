# Índice general de evidencias — SGSI UVCG

Fecha de consolidación: 2026-10-24. Todas las identidades y datos son ficticios. Los reportes excluyen contraseñas, tokens y valores de coincidencias sensibles. Estado global en [`ESTADO_PROYECTO.md`](../ESTADO_PROYECTO.md); fichas por control en [CONTROLES_IMPLEMENTADOS.md](CONTROLES_IMPLEMENTADOS.md).

## Laboratorio técnico

| Módulo | Estado | Evidencia principal |
|---|---|---|
| Cierre | Documentos | [`CIERRE_LABORATORIO_LOCAL.md`](../CIERRE_LABORATORIO_LOCAL.md), [`CIERRE_AZURE.md`](../CIERRE_AZURE.md), [`MANUAL_EJECUCION.md`](../MANUAL_EJECUCION.md) |
| Validación integral | 27 OK / 1 fallido / 1 no verificable | [validacion-sgsi-20261024-112033.json](automatizacion/validacion-sgsi-20261024-112033.json); el fallo de Azure se reejecutó aparte ([32 OK](azure/validacion-estatica-reejecucion-20261024.txt)) |
| WAL/PITR | Réplicas OK; principales preparado | `pitr/pitr-*.json`, `local/compose.pitr.yaml` |
| Vigilancia de contenedores | Demostración tipo EDR | `edr/vigilancia-*.json` |
| Monitor de disponibilidad | Continuo | `local/monitoring/disponibilidad/disponibilidad.log` |
| DLP (compuerta) / MDM (simulación) | Parcial / preparado | `dlp/compuerta-*.json`, `mdm/cumplimiento-mdm-*.json` |
| Registros operativos | Implementado | [`governance/registros-operativos.md`](../governance/registros-operativos.md), `gestion/registro-sgsi.db` |
| Azure | Preparado, no desplegado | [`azure/INDICE-AZURE.md`](azure/INDICE-AZURE.md) |
| AWS (plan Free) | Preparado, no desplegado | [`aws/INDICE.md`](aws/INDICE.md), [`CIERRE_AWS.md`](../CIERRE_AWS.md) |
| Identidad, MFA y RBAC | Implementado | `automatizacion/validacion-sgsi-*.json` (IAM-RBAC-MFA), `scripts/pruebas_identidad.py` |
| TLS y aplicación | Implementado | `automatizacion/validacion-sgsi-*.json` (APP-HTTPS), [validación base](validacion-local-20261024.md) |
| A. SIEM y monitoreo | SIEM ligero | [Reporte](siem/REPORTE-SIEM.md), `siem/pipeline-siem-*.json`, `siem/alertas-*.json`, `siem/tablero-siem-*.html`, `siem/consulta-*.json` |
| B. IDS | Offline | [Reporte](ids/REPORTE-IDS.md), [resultado](ids/resultado.json), `ids/eve.json`, `ids/fast.log`, `ids/historico/` |
| Segmentación de red | Validada | `network/segmentacion-*.json` |
| C. Backups y recuperación | Implementado local | [Reporte](backup/REPORTE-BACKUP-RECUPERACION.md), `backup/backups-programados-*.json`, `recovery/restauracion-dual-*.json`, `recovery/recuperacion-periodica-*.json` |
| H. Continuidad (pruebas) | Laboratorio | `recovery/continuidad-api-*.json`, `recovery/continuidad-iam-*.json` |
| I. Vulnerabilidades | PostgreSQL mitigado; Keycloak pendiente | [Registro detallado](security/registro-vulnerabilidades-detallado.md) ([CSV](security/registro-vulnerabilidades-detallado.csv)), [imágenes en uso](security/escaneo-imagenes-en-uso-post-upgrade.json), [antes](security/trivy-antes-postgres-16-alpine-pre-upgrade.json), `security/trivy-*.json` |
| Actualización PostgreSQL | Implementada | [Reporte y rollback](postgres-upgrade/REPORTE-ACTUALIZACION-POSTGRESQL.md), [estado de las 5 aplicaciones](postgres-upgrade/estado-aplicaciones-post-upgrade.json), `postgres-upgrade/huella-*.json`, `postgres-upgrade/actualizacion-*.json`, `postgres-upgrade/rollback-*.json` |
| Recuperación programada | Implementada | [Reporte](recovery/tarea-programada/REPORTE-TAREA-PROGRAMADA.md), [ejecuciones](recovery/tarea-programada/ejecuciones.csv), [definición](recovery/tarea-programada/definicion-tarea.xml) |
| Retención (simulación) | Sólo dry-run | `retencion/simulacion-retencion-*.md` / `.json`, política `local/backup/retention-policy.json` |
| Integridad de configuración | Implementado | [Línea base](integridad/linea-base-configuracion.json), `integridad/verificacion-*.json` |
| DLP | Parcial | `dlp/dlp-*.json` |
| Azure | Preparado, no desplegado | [Terraform validate](azure-terraform-validate-20261024.txt) |

## Gobierno del SGSI (`governance/`)

| Entregable | Archivos |
|---|---|
| Inventario de activos | `inventario-activos.md`, `inventario-activos.csv` |
| Marcos COBIT/ITIL/TIA-942 | `marcos-cobit-itil-tia942.md` |
| Políticas ISO 27001/27002 | `../policies/politicas-sgsi-iso27001.md` |
| Registros operativos | `registros-operativos.md` |
| D. BIA | `bia.md`, `bia.csv` |
| E. Análisis de riesgos | `matriz-riesgos.md`, `matriz-riesgos.csv` |
| Matrices de calor (inherente y residual) | `matriz-calor.md` |
| F. OCTAVE Allegro | `octave-allegro.md` |
| G. Plan de tratamiento | `plan-tratamiento.md`, `plan-tratamiento.csv` |
| G. Declaración de Aplicabilidad | `declaracion-aplicabilidad.md`, `declaracion-aplicabilidad.csv` |
| H. BCP y DRP | `bcp.md`, `drp.md` |
| Trazabilidad verificada | `evidencias/gobernanza/trazabilidad-*.json` |

Identificadores: procesos `PROC-xxx`, activos `ACT-xxx`, riesgos `R-xxx`, controles `A.x.y`, escenarios OCTAVE `OS-xx`, pruebas IDS `IDS-Txx`, hallazgos `VULN-xxx`, reglas SIEM `SIEM-*`, fichas `Mxx-*`.

Los archivos de monitoreo y seguridad son evidencia técnica de laboratorio; no equivalen a certificación, auditoría externa ni garantías institucionales. Las evidencias anteriores a esta fase (`monitoring/`, `recovery/restauracion-20261024_*.json`) se conservan como histórico.
