# Manual de ejecución y validación — Laboratorio SGSI UVCG

Requisitos: Windows con Docker Desktop iniciado, Python 3.10+, PowerShell 5.1. Todos los comandos se ejecutan desde `D:\sgsi_laboratorio` salvo que se indique otra carpeta. Ningún comando de este manual borra volúmenes, bases ni respaldos.

## 1. Arranque y estado

```powershell
cd local
docker compose -f compose.yaml up -d                                 # cinco servicios principales
docker compose -f compose.yaml --profile backup-scheduled up -d      # respaldos programados diarios
docker compose -f compose.yaml --profile monitoring up -d            # monitor de disponibilidad continuo (15 s)
docker compose -f compose.yaml --profile backup-scheduled --profile monitoring ps
```

## 2. Validación integral

```powershell
scripts\validar_sgsi.ps1                                             # pruebas sin interrupción
scripts\validar_sgsi.ps1 -IncludeIds -IncludeRecovery -IncludeSecurity -IncludeContinuity
```

Resultado en `evidencias/automatizacion/validacion-sgsi-<fecha>.json` con estados `exitoso`, `fallido`, `omitido` y `no_verificable`. `-IncludeContinuity` detiene la API y Keycloak unos segundos. `-IncludeRecovery` incluye restauraciones aisladas y PITR en réplicas (unos 6 minutos).

## 3. Operación por módulo

| Módulo | Comando | Evidencia |
|---|---|---|
| Identidad/MFA/RBAC | `python scripts\pruebas_identidad.py` | salida OK |
| HTTPS | `python scripts\pruebas_locales.py` | salida OK |
| Segmentación | `scripts\validar_segmentacion.ps1` | `evidencias/network/` |
| SIEM (ciclo completo) | `python scripts\siem_pipeline.py` | `evidencias/siem/pipeline-siem-*.json`, `tablero-siem-*.html` |
| SIEM (consulta histórica) | `python scripts\siem_ligero.py search --category authentication --since 2026-10-24T00:00:00Z` | consola/JSON |
| SIEM (integridad) | `python scripts\siem_ligero.py seal` y `verify` | consola |
| IDS | `python scripts\generar_pcap_ids.py`; `docker compose -f local\compose.yaml --profile ids run --rm ids`; `python scripts\validar_alerta_ids.py` | `evidencias/ids/` |
| Vigilancia de contenedores | `python scripts\vigilancia_contenedores.py --check` | `evidencias/edr/` |
| Integridad de configuración | `python scripts\integridad_configuracion.py --verify` / `--self-test` | `evidencias/integridad/` |
| DLP | `python scripts\dlp_compuerta.py local\dlp\samples\*.txt --canal externo` | `evidencias/dlp/`, incidentes |
| MDM (simulación) | `python scripts\mdm_cumplimiento.py` | `evidencias/mdm/` |
| Respaldos | `scripts\backup_postgres.ps1 -Target Both` | `evidencias/backup/` |
| Restauración aislada | `scripts\restaurar_prueba.ps1 -Target Both` (conserva las bases restauradas) | `evidencias/recovery/` |
| Recuperación periódica | Tarea `SGSI-UVCG-Prueba-Recuperacion` (domingos 10:00) o `scripts\tarea_recuperacion_programada.ps1 -Trigger manual` | `evidencias/recovery/tarea-programada/` |
| PITR (réplicas aisladas) | `python scripts\pitr_prueba.py` | `evidencias/pitr/` |
| Monitor WAL | `python scripts\monitor_wal.py --container local-db-1 --env-user DB_USER --env-db DB_NAME` | `local/backups/execution.log` |
| Retención (simulación) | `python scripts\simular_retencion.py` | `evidencias/retencion/` |
| Continuidad | `scripts\prueba_continuidad.ps1 -Service api` / `-Service keycloak` | `evidencias/recovery/continuidad-*.json` |
| Vulnerabilidades | `scripts\ejecutar_seguridad.ps1`; `scripts\escanear_imagenes_en_uso.ps1` | `evidencias/security/` |
| Gobernanza | `python scripts\generar_gobernanza_sgsi.py`; `python scripts\validar_trazabilidad.py` | `governance/`, `evidencias/gobernanza/` |
| Registros operativos | `python scripts\gestion_sgsi.py incidente abrir ...` / `cambio registrar ...` / `exportar` | `governance/registros-operativos.md` |

## 4. Procedimientos que requieren autorización (no ejecutar sin ella)

| Acción | Comando preparado |
|---|---|
| Activar WAL/PITR en las bases principales | `docker compose -f compose.yaml -f compose.pitr.yaml up -d --no-deps --force-recreate db identity-db` (desde `local/`), seguido de `pruebas_identidad.py` y `monitor_wal.py` |
| Revertir PostgreSQL a la imagen oficial | `scripts\rollback_postgres.ps1 -RollbackCompose local\rollback\compose.yaml.pre-upgrade-20261024-102045.bak -Execute` |
| Borrado por retención | No existe un comando automatizado: revisar `evidencias/retencion/` y autorizar archivo por archivo |
| Restringir la ACL de `local/.env` | `icacls local\.env /save local\rollback\env-acl.txt`; `icacls local\.env /inheritance:r /grant:r "%USERNAME%:(M)" "SYSTEM:(F)"` |
| Programar el ciclo SIEM | `Register-ScheduledTask` análogo a la tarea de recuperación, cada 15 minutos |

## 5. Cambios y registro

Todo cambio de configuración debe registrarse (`gestion_sgsi.py cambio registrar`) y, tras su aprobación, actualizar la línea base (`integridad_configuracion.py --baseline --reason "..."`). Un `--verify` fallido sin cambio registrado es un incidente.
