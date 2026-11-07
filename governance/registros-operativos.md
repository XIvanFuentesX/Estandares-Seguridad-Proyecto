# Registros operativos del SGSI (laboratorio)

Exportado: 2026-10-24T11:34:28-06:00 desde `evidencias/gestion/registro-sgsi.db`. Origen `real-laboratorio` = hecho ocurrido en este laboratorio; `ejercicio` = caso de práctica con identidades ficticias. Ninguna entrada representa una aprobación institucional; "aprobado_por" refleja la autorización dada por el usuario del laboratorio en la conversación de trabajo.

Integridad de la bitácora de auditoría: verificada (cadena SHA-256); entradas: 34.

## Incidentes (12)

| id | creado | titulo | severidad | origen | estado | detectado | contencion | resolucion | leccion | riesgo | evidencia | cerrado |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| INC-001 | 2026-10-24T11:07:52-06:00 | DLP: transferencia bloqueada de confidencial-ficticio.txt (CONFIDENCIAL) al canal externo | media | ejercicio | cerrado | 2026-10-24T11:07:52-06:00 | Transferencia bloqueada automáticamente; archivo no copiado | Bloqueo automático de la compuerta DLP verificado; muestra sintética, sin exposición |  | R-003 | evidencias/dlp/compuerta-*.json | 2026-10-24T11:08:43-06:00 |
| INC-002 | 2026-10-24T11:07:52-06:00 | DLP: transferencia bloqueada de credencial-ficticia.txt (INTERNA) al canal externo | media | ejercicio | cerrado | 2026-10-24T11:07:52-06:00 | Transferencia bloqueada automáticamente; archivo no copiado | Bloqueo automático de la compuerta DLP verificado; muestra sintética, sin exposición |  | R-003 | evidencias/dlp/compuerta-*.json | 2026-10-24T11:08:43-06:00 |
| INC-003 | 2026-10-24T11:07:52-06:00 | DLP: transferencia bloqueada de restringido-ficticio.txt (RESTRINGIDA) al canal externo | media | ejercicio | cerrado | 2026-10-24T11:07:52-06:00 | Transferencia bloqueada automáticamente; archivo no copiado | Bloqueo automático de la compuerta DLP verificado; muestra sintética, sin exposición |  | R-003 | evidencias/dlp/compuerta-*.json | 2026-10-24T11:08:43-06:00 |
| INC-004 | 2026-10-24T11:07:52-06:00 | DLP: transferencia bloqueada de tarjeta-ficticia.txt (INTERNA) al canal externo | media | ejercicio | cerrado | 2026-10-24T11:07:52-06:00 | Transferencia bloqueada automáticamente; archivo no copiado | Bloqueo automático de la compuerta DLP verificado; muestra sintética, sin exposición |  | R-003 | evidencias/dlp/compuerta-*.json | 2026-10-24T11:08:43-06:00 |
| INC-005 | 2026-10-24T11:07:52-06:00 | DLP: transferencia bloqueada de credencial-ficticia.txt (INTERNA) al canal interno | media | ejercicio | cerrado | 2026-10-24T11:07:52-06:00 | Transferencia bloqueada automáticamente; archivo no copiado | Bloqueo automático de la compuerta DLP verificado; muestra sintética, sin exposición |  | R-003 | evidencias/dlp/compuerta-*.json | 2026-10-24T11:08:44-06:00 |
| INC-006 | 2026-10-24T11:07:52-06:00 | DLP: transferencia bloqueada de restringido-ficticio.txt (RESTRINGIDA) al canal interno | media | ejercicio | cerrado | 2026-10-24T11:07:52-06:00 | Transferencia bloqueada automáticamente; archivo no copiado | Bloqueo automático de la compuerta DLP verificado; muestra sintética, sin exposición |  | R-003 | evidencias/dlp/compuerta-*.json | 2026-10-24T11:08:44-06:00 |
| INC-007 | 2026-10-24T11:08:32-06:00 | Copia de respaldo antigua sin cifrar en local/backups (universidad-20261024-084707.dump) | media | real-laboratorio | abierto | 2026-10-24T10:32:13-06:00 | Copia cifrada creada y verificada (round-trip SHA-256); original conservado hasta autorizar eliminación |  |  | R-015 | evidencias/retencion/simulacion-retencion-20261024-103213.md |  |
| INC-008 | 2026-10-24T11:08:33-06:00 | Fallo de restauración aislada por defecto de script (PowerShell 5.1 + stderr Docker) | baja | real-laboratorio | cerrado | 2026-10-24T09:56:32-06:00 |  | Scripts con ErrorActionPreference=Continue y validación por LASTEXITCODE; restauración revalidada con éxito | Probar los scripts en el mismo contexto (redirigido/programado) en que se ejecutarán | R-007 | evidencias/siem/REPORTE-SIEM.md | 2026-10-24T11:08:43-06:00 |
| INC-009 | 2026-10-24T11:08:33-06:00 | Eliminación no autorizada de 2 bases temporales de prueba en instancia aislada | baja | real-laboratorio | cerrado | 2026-10-24T10:20:49-06:00 |  | restaurar_prueba.ps1 conserva por defecto las bases restauradas; borrado sólo con -DropRestoredDatabase | Los comportamientos por defecto deben ser no destructivos; revisar valores predeterminados al cambiar las autorizaciones | R-008 | evidencias/postgres-upgrade/REPORTE-ACTUALIZACION-POSTGRESQL.md | 2026-10-24T11:08:43-06:00 |
| INC-010 | 2026-10-24T11:08:33-06:00 | Archivo de secretos .env con permisos heredados amplios | media | real-laboratorio | abierto | 2026-10-24T11:08:33-06:00 | Sin cambio de ACL (requiere autorización); propuesta registrada como cambio |  |  | R-015 |  |  |
| INC-011 | 2026-10-24T11:08:33-06:00 | Bases principales sin archivado WAL: RPO propuesto no alcanzable | alta | real-laboratorio | abierto | 2026-10-24T11:08:33-06:00 | PITR validado en réplicas; activación pendiente de autorización |  |  | R-019 | local/backups/execution.log (target=wal-*-principal) |  |
| INC-012 | 2026-10-24T11:34:28-06:00 | Validación integral interrumpida por falta de memoria del sistema; contenedor PITR efímero huérfano | baja | real-laboratorio | abierto | 2026-10-24T11:34:28-06:00 | Contenedor efímero detenido; servicios principales verificados healthy; datos y volúmenes intactos |  |  | R-004 |  |  |

## Cambios (6)

| id | creado | titulo | tipo | riesgo | descripcion | rollback | aprobado_por | estado | ejecutado | evidencia | origen |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CHG-001 | 2026-10-24T11:08:32-06:00 | db e identity-db a local-postgres-hardened:16 (sin gosu, UID 70) | normal | R-009 | Respaldo lógico + copia en frío + huella; recreación sin borrar volúmenes | scripts/rollback_postgres.ps1 con local/rollback/compose.yaml.pre-upgrade-20261024-102045.bak | Usuario del laboratorio (autorización expresa 2026-10-24) | implementado | 2026-10-24T10:22:29-06:00 | evidencias/postgres-upgrade/REPORTE-ACTUALIZACION-POSTGRESQL.md | real-laboratorio |
| CHG-002 | 2026-10-24T11:08:32-06:00 | Tarea programada SGSI-UVCG-Prueba-Recuperacion (domingos 10:00) | normal | R-007 |  | Unregister-ScheduledTask -TaskName SGSI-UVCG-Prueba-Recuperacion | Usuario del laboratorio (autorización expresa 2026-10-24) | implementado | 2026-10-24T10:30:41-06:00 | evidencias/recovery/tarea-programada/REPORTE-TAREA-PROGRAMADA.md | real-laboratorio |
| CHG-003 | 2026-10-24T11:08:32-06:00 | Servicio opcional uptime-monitor (perfil monitoring) y reglas SIEM WAL/CFG/AVAIL/EDR/DLP | estandar | R-012 |  | docker compose --profile monitoring stop uptime-monitor; restaurar compose.yaml de local/rollback | Encargo de cierre local (cambio seguro y reversible) | implementado | 2026-10-24T11:05:43-06:00 | evidencias/integridad/linea-base-configuracion.json | real-laboratorio |
| CHG-004 | 2026-10-24T11:08:32-06:00 | Activar archivado WAL en db e identity-db (compose.pitr.yaml) | normal | R-019 | Requiere recrear ambas bases; validado en réplicas aisladas | Levantar sólo con compose.yaml |  | preparado - pendiente de autorizacion |  | evidencias/pitr | real-laboratorio |
| CHG-005 | 2026-10-24T11:08:32-06:00 | Restringir ACL de local/.env al usuario propietario | normal | R-015 | ACL heredada concede Modificar a Usuarios autentificados | icacls .env /restore con la ACL guardada |  | propuesto - pendiente de autorizacion |  |  | real-laboratorio |
| CHG-006 | 2026-10-24T11:34:28-06:00 | uptime-monitor: deshabilitar healthcheck heredado (falso unhealthy) | estandar | R-012 |  | Quitar el bloque healthcheck del servicio | Encargo de cierre local (cambio seguro y reversible) | implementado |  | evidencias/integridad/linea-base-configuracion.json | real-laboratorio |

## Accesos (2)

| id | creado | solicitante | recurso | rol | justificacion | origen | estado | decision | motivo | resuelto |
|---|---|---|---|---|---|---|---|---|---|---|
| ACC-001 | 2026-10-24T11:08:44-06:00 | docente01 | C:/Program Files/Git/administracion | administrativo | Consultar pagos de estudiantes (ejercicio) | ejercicio | resuelta | denegada | Mínimo privilegio: el rol docente no requiere datos financieros; verificado con RBAC (403) en pruebas_identidad.py | 2026-10-24T11:08:44-06:00 |
| ACC-002 | 2026-10-24T11:08:44-06:00 | administrativo01 | C:/Program Files/Git/administracion | administrativo | Gestión de matrícula (ejercicio) | ejercicio | resuelta | aprobada | Coincide con la función; rol existente con MFA obligatorio | 2026-10-24T11:08:44-06:00 |

## Activos (4)

| id | creado | activo_id | evento | detalle | responsable | origen |
|---|---|---|---|---|---|---|
| AST-001 | 2026-10-24T11:08:44-06:00 | ACT-005 | cambio de imagen | postgres:16-alpine -> local-postgres-hardened:16 (CHG-001) | DBA | real-laboratorio |
| AST-002 | 2026-10-24T11:08:44-06:00 | ACT-007 | cambio de imagen | postgres:16-alpine -> local-postgres-hardened:16 (CHG-001) | DBA/IAM | real-laboratorio |
| AST-003 | 2026-10-24T11:08:44-06:00 | ACT-010 | copia cifrada de respaldo heredado | universidad-20261024-084707.dump.enc creado; original conservado (INC-007) | DBA | real-laboratorio |
| AST-004 | 2026-10-24T11:08:44-06:00 | ACT-022 | alta | Monitor de disponibilidad continuo (uptime-monitor) | Seguridad TI | real-laboratorio |

## Evaluaciones (0)

Sin registros.
