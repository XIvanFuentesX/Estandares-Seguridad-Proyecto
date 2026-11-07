# Reporte del Módulo C — Backups automatizados y recuperación

Fecha: 2026-10-24. Bases protegidas: PostgreSQL académico (`db`) y PostgreSQL de identidad (`identity-db`, Keycloak).

## 1. Cumplimiento de requisitos

| # | Requisito | Implementación | Evidencia | Estado |
|---|---|---|---|---|
| 1 | Respaldos programados de ambas bases | `academic-backup-scheduler` e `identity-backup-scheduler` (perfil `backup-scheduled`, intervalo 86 400 s, `restart: unless-stopped`) | `backups-programados-20261024-095726.json` | Implementado |
| 2 | Scripts reproducibles | `local/backup/backup-encrypted.sh`, `scripts/backup_postgres.ps1`, `scripts/restaurar_prueba.ps1` | Código | Implementado |
| 3 | Retención configurable | Política GFS en `local/backup/retention-policy.json` (diaria 7 días, semanal 4 semanas, mensual 3 meses, siempre la copia más reciente) evaluada por `scripts/simular_retencion.py`, que no contiene código de borrado; SIEM con `retention --days 30` sin `--apply` | `../retencion/simulacion-retencion-*.md` | Implementado **sólo en simulación**; el borrado real no está autorizado |
| 4 | Integridad SHA-256 | `.sha256` por copia, verificado antes de cada restauración | Manifiestos `local/backups/*.json` | Implementado |
| 5 | Cifrado | AES-256-CBC, PBKDF2 200 000 iteraciones, sal aleatoria | `backup-encrypted.sh` | Implementado |
| 6 | Separación de credenciales | Clave en `local/.env` (ignorado por Git), fuera de `local/backups/`; el archivo `.env` no se monta en ningún contenedor (la clave se inyecta sólo como variable de entorno a las herramientas de backup) y nunca se escribe en manifiestos ni bitácoras | `.env.example`, `compose.yaml` | Implementado en laboratorio (mismo host: R-015) |
| 7 | Registro de ejecuciones | `local/backups/execution.log` (éxitos y fallos, también en modo `--once`) | Bitácora | Implementado |
| 8 | Alertas ante fallos | SIEM-BACKUP-001 sobre `result=failure` | `../siem/consulta-backup-failure-20261024-095532.json` | Implementado y probado con fallo real controlado |
| 9 | Restauración automatizada aislada | `restore-db` / `identity-restore-db` en red `recovery` interna; nunca sobre la base activa | `../recovery/restauracion-dual-20261024_100159.json` | Implementado |
| 10 | Pruebas periódicas de recuperación | Tarea `SGSI-UVCG-Prueba-Recuperacion` (domingos 10:00) → `scripts/tarea_recuperacion_programada.ps1` → `prueba_recuperacion_periodica.ps1` | `../recovery/tarea-programada/REPORTE-TAREA-PROGRAMADA.md`, `ejecuciones.csv` | Implementado y probado desde el Programador de tareas |

## 2. Resultados de restauración (última ejecución)

| Base | Copia cifrada | SHA-256 (verificado) | Duración | Registros verificados | Base principal modificada |
|---|---|---|---|---|---|
| Académica | `academic-20261024-160159.dump.enc` | `2c69d6c0f7899152f94226e6dd9e6512749ffcb0c10008738747b0a89b66d51c` | 8.537 s | 3 cursos | No |
| Identidad | `identity-20261024-160159.dump.enc` | `2c40e932ccd31c311316f347825a98e821201aecc4ad93c465c1efdee4d3ccd0` | 9.056 s | 5 identidades | No |

Esta restauración se ejecutó sobre la imagen `local-postgres-hardened:16` (sin `gosu`, UID 70), validando además su compatibilidad. Desde el 2026-10-24 a las 10:29, las bases restauradas se **conservan** en la instancia aislada (no se borra nada por defecto; `-DropRestoredDatabase` requiere autorización). Entre las 10:01 y las 10:20 el script borraba tras verificar las bases temporales que él mismo creaba en la instancia aislada; esto no afectó bases principales, volúmenes ni respaldos.

Errores registrados: 1 fallo real de restauración a las 15:56 UTC por un defecto del script (PowerShell 5.1 y stderr de Docker), corregido y revalidado; 1 fallo provocado de backup (host inexistente) para probar la alerta.

## 3. Comparación con objetivos (supuestos académicos del BIA)

| Base | RTO propuesto | Restauración observada | RPO propuesto | Intervalo actual | Conclusión |
|---|---|---|---|---|---|
| Académica (PROC-002) | 8 h | 8.5 s | 4 h | 24 h | RTO técnico cumplido; **RPO no alcanzable** (R-019) |
| Identidad (PROC-004) | 2 h | 9.1 s | 15 min | 24 h | RTO técnico cumplido; **RPO no alcanzable** (R-019) |

Los tiempos observados corresponden a bases de laboratorio de pocos KB y no se extrapolan a la universidad.

## 4. Limitaciones y decisiones pendientes

- Copias y clave residen en el mismo host: sin copia offsite/inmutable (R-011, R-015).
- Sin archivado WAL/PITR: el RPO depende del intervalo diario (R-019).
- Aplicar el borrado por retención (`-ApplyRetention`, `retention --apply`) sólo con autorización expresa; la simulación identifica hoy 4 conjuntos candidatos (603 KB).
- Hallazgo: `local/backups/universidad-20261024-084707.dump` es una copia antigua **sin cifrar** de la primera fase; queda fuera de la política y su cifrado o eliminación requiere autorización.
- Las bases restauradas se acumulan semanalmente en los volúmenes aislados.

## 5. Respaldos previos a la actualización de PostgreSQL (2026-10-24 10:20)

| Base | Copia | Verificación | Restauración aislada |
|---|---|---|---|
| Académica | `academic-20261024-162047.dump.enc` | SHA-256 correcto | 8.22 s, 3 cursos |
| Identidad | `identity-20261024-162048.dump.enc` | SHA-256 correcto | 8.947 s, 5 identidades |

También se tomaron copias en frío de los volúmenes (`local/rollback/volumes/`). Ver `../postgres-upgrade/REPORTE-ACTUALIZACION-POSTGRESQL.md`.
