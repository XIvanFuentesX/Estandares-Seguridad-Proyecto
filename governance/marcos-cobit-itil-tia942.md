# Alineación con COBIT 2019, ITIL 4 y TIA-942 — UVCG

Fecha: 2026-10-24. Las columnas distinguen lo **ejecutado en el laboratorio** (con evidencia) de lo **propuesto** (diseño o política sin operación institucional). No hay evaluaciones de capacidad ni auditorías formales: los niveles indicados son una autoevaluación académica.

## 1. COBIT 2019 — objetivos de gobierno y gestión relevantes

| Objetivo | Propósito resumido | Ejecutado en laboratorio (evidencia) | Propuesto / pendiente | Autoevaluación (0–5) |
|---|---|---|---|---|
| EDM03 Riesgo optimizado | Apetito y tolerancia al riesgo | Criterios de aceptación definidos (`matriz-riesgos.md`) | Aprobación del apetito por la Dirección | 1 |
| APO12 Riesgo gestionado | Identificar, analizar y responder al riesgo | 19 riesgos con P×I inherente/residual, OCTAVE, trazabilidad validada | Talleres con propietarios | 2 |
| APO13 Seguridad gestionada | Operar el SGSI | SoA de 93 controles, 15 fichas de control, validación integral | Comité de seguridad, auditoría interna | 2 |
| BAI06 Cambios TI gestionados | Controlar cambios | Registro CHG-001..005 con rollback; línea base SHA-256 de configuración | CAB institucional | 2 |
| BAI09 Activos gestionados | Ciclo de vida de activos | Inventario de 24 activos; eventos AST-001..004 | CMDB institucional | 2 |
| BAI10 Configuración gestionada | Línea base y control de configuración | `integridad_configuracion.py` con autoprueba de detección | Herramienta CMDB | 2 |
| DSS01 Operaciones gestionadas | Operación de servicios | Healthchecks, monitor continuo, tareas programadas | Turnos/NOC | 2 |
| DSS02 Solicitudes e incidentes | Respuesta a incidentes y solicitudes | Registro INC-001..011 y ACC-001..002 con auditoría encadenada | Mesa de servicio | 2 |
| DSS04 Continuidad gestionada | BCP/DRP y pruebas | BIA, BCP/DRP, restauraciones, PITR en réplicas, prueba semanal programada | Sitio alterno, ejercicio de mesa | 2 |
| DSS05 Servicios de seguridad | Protección contra amenazas | MFA/RBAC, TLS, segmentación, IDS offline, vigilancia de contenedores, DLP | EDR/MDM reales | 2 |
| DSS06 Controles de procesos de negocio | Integridad de datos de procesos | Huella de datos pre/post cambio; RBAC por ruta | Controles en sistemas académicos reales | 1 |
| MEA01 Desempeño monitoreado | Medición | `validar_sgsi.ps1` (resultados exitoso/fallido/omitido/no verificable) | Indicadores aprobados | 2 |
| MEA03 Cumplimiento externo | Requisitos legales | Identificados en BIA (supuestos) | Análisis legal guatemalteco | 0 |

## 2. ITIL 4 — prácticas

| Práctica | Implementación demostrable | Evidencia |
|---|---|---|
| Gestión de incidentes | Apertura, contención, cierre y lección aprendida | `governance/registros-operativos.md` (INC) |
| Habilitación de cambios | Registro con tipo (estándar/normal), riesgo, rollback y aprobación | `registros-operativos.md` (CHG) |
| Gestión de solicitudes de servicio | Solicitud y resolución de accesos con mínimo privilegio | `registros-operativos.md` (ACC) |
| Gestión de activos de TI | Inventario y eventos de ciclo de vida | `inventario-activos.md`, AST |
| Gestión de la configuración del servicio | Línea base y verificación de integridad | `evidencias/integridad/` |
| Monitoreo y gestión de eventos | SIEM ligero, monitor de disponibilidad, alertas | `evidencias/siem/` |
| Gestión de la continuidad del servicio | BIA, BCP, DRP, pruebas | `governance/bcp.md`, `drp.md`, `evidencias/recovery/`, `evidencias/pitr/` |
| Gestión de la seguridad de la información | SGSI, SoA y controles | `declaracion-aplicabilidad.md` |
| Gestión de la disponibilidad | Healthchecks, monitor continuo cada 15 s, mediciones de recuperación | `local/monitoring/`, continuidad |
| Gestión de problemas | Lecciones de INC-008/009 traducidas en cambios de scripts | `registros-operativos.md` |

## 3. TIA-942 — aplicabilidad

TIA-942 especifica la infraestructura física de centros de datos (arquitectura, electricidad, climatización, cableado, seguridad física y niveles de disponibilidad Rated 1–4).

| Aspecto | Estado en el proyecto | Justificación |
|---|---|---|
| Infraestructura física del laboratorio | **No aplica** | El laboratorio es un único equipo personal; no constituye un centro de datos. |
| Selección de región/zonas en Azure | Considerado en la arquitectura cloud (`CIERRE_AZURE.md`) | Microsoft opera los centros de datos; la evidencia de cumplimiento físico la proveen sus informes de auditoría (no evaluados aquí). |
| Centro de datos o cuarto de servidores institucional | **Propuesto** | Requeriría un levantamiento físico real (energía, climatización, control de acceso). Vinculado a R-014 y a los controles A.7.x de la SoA, hoy pendientes. |
| Nivel de disponibilidad objetivo | Propuesta: equivalente a Rated 2 para el sitio local más la redundancia en Azure | Coherente con los RTO del BIA (2–24 h); pendiente de aprobación. |
