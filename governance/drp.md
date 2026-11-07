# Disaster Recovery Plan (DRP) — laboratorio UVCG

Generado: 2026-11-07T11:23:29-06:00. Borrador académico pendiente de aprobación y de infraestructura alterna. Deriva de `bia.md` y `bcp.md`.

## 1. Dependencias y orden de recuperación

1. Host/Docker, almacenamiento, red y tiempo (ACT-001, ACT-002).
2. Secretos y clave de cifrado de backups (ACT-011), custodiados fuera del directorio de copias.
3. PostgreSQL de identidad (ACT-007) → Keycloak (ACT-006).
4. PostgreSQL académico (ACT-005) → API (ACT-003).
5. Nginx/TLS (ACT-004, ACT-013).
6. SIEM, IDS y schedulers de backup (ACT-008, ACT-009, ACT-010).

## 2. Objetivos propuestos

| proceso | RTO_h | RPO_h | MTPD_h |
|---|---|---|---|
| PROC-004 Identidad y autenticación | 2 | 0.25 | 4 |
| PROC-001 Inscripción y matrícula | 4 | 1 | 12 |
| PROC-003 Aprendizaje virtual | 4 | 1 | 12 |
| PROC-002 Gestión académica | 8 | 4 | 24 |
| PROC-005 Gestión financiera y pagos | 8 | 1 | 24 |
| PROC-007 Correo y comunicaciones | 8 | 4 | 24 |
| PROC-006 Servicios administrativos | 24 | 8 | 72 |

El backup lógico diario (86 400 s) **no satisface** por sí solo el RPO de 15 min / 4 h. El archivado WAL/PITR se validó en réplicas aisladas (RPO observado ≈ 56 s con `archive_timeout` 60 s; recuperación exacta al punto objetivo); en las bases principales está **preparado** (`local/compose.pitr.yaml`) y pendiente de autorización (R-019).

## 3. Escenarios y procedimientos

**DR-1 Caída de un contenedor** (probado): `docker compose -f local/compose.yaml up -d --no-deps <servicio>`; esperar `healthy`; verificar `/health` y conteos. Evidencia: `evidencias/recovery/continuidad-*.json`.

**DR-2b Error lógico con hora conocida (PITR)** (probado en réplicas): restaurar el respaldo base, aplicar WAL hasta `recovery_target_time` anterior al error y promover en una instancia aislada (`scripts/pitr_prueba.py`); validar y migrar con autorización.

**DR-2 Corrupción de la base académica o de identidad** (restauración aislada probada):
1. Declarar incidente, congelar cambios y registrar tiempo; preservar logs y hashes.
2. No restaurar sobre la base activa. Verificar SHA-256 de la copia cifrada y disponibilidad separada de la clave.
3. Restaurar en instancia aislada: `scripts/restaurar_prueba.ps1 -Target Both` (conserva la base restaurada para su revisión).
4. Validar conteos (≥ 3 cursos, ≥ 4 identidades), MFA/RBAC y TLS.
5. Para recuperación productiva: autorización, respaldo del estado fallido, ventana definida y migración controlada.

**DR-3 Compromiso de identidad:** aislar Keycloak (detener el servicio), rotar secretos (`scripts/generar_secretos_lab.ps1` tras autorización), restaurar IAM desde copia anterior al compromiso, forzar reinscripción MFA.

**DR-4 Pérdida del host:** hoy **no recuperable dentro del RTO** (sin sitio ni copia externa: R-011). Procedimiento objetivo: nuevo host con Docker → recuperar código y `.env` desde custodia → restaurar copias offsite → DR-2.

**DR-5 Ransomware/cifrado de archivos:** aislar el host de la red, preservar evidencia, no pagar, reconstruir desde copia offsite inmutable (pendiente) y verificar integridad con `scripts/integridad_configuracion.py --verify`.

## 4. Resultados observados vs. objetivo

| prueba | proceso | rto_propuesto | observado_s | diferencia_s | cumple_tecnico | fecha |
|---|---|---|---|---|---|---|
| Interrupción de la API (contenedor detenido) | PROC-002 | 8 h | 11.98 | 28788.0 | Sí | 2026-10-24T11:19:22 |
| Interrupción de Keycloak (contenedor detenido) | PROC-004 | 2 h | 70.242 | 7129.8 | Sí | 2026-10-24T11:20:33 |
| Restauración aislada academic desde copia cifrada | PROC-002 | 8 h | 8.33 | 28791.7 | Sí | 2026-10-24T11:33:41 |
| Restauración aislada identity desde copia cifrada | PROC-004 | 2 h | 8.965 | 7191.0 | Sí | 2026-10-24T11:33:41 |
| PITR academic (réplica aislada) al punto objetivo | PROC-002 | 8 h | 2.1 | 28797.9 | Sí | 2026-10-24T11:16:44 |
| PITR identity (réplica aislada) al punto objetivo | PROC-004 | 2 h | 2.1 | 7197.9 | Sí | 2026-10-24T11:16:44 |

| base | proceso | rpo_propuesto_s | intervalo_backup_s | cumple |
|---|---|---|---|---|
| academic | PROC-002 | 14400 | 86400 | No — brecha R-019 |
| identity | PROC-004 | 900 | 86400 | No — brecha R-019 |

## 5. Pruebas

Mensual: salud y hashes. Semanal (tarea programada `SGSI-UVCG-Prueba-Recuperacion`, domingos 10:00): `scripts/prueba_recuperacion_periodica.ps1` (restore aislado de ambas bases y comparación con RTO/RPO). Semestral: `scripts/prueba_continuidad.ps1 -Service api|keycloak`. Anual: pérdida de host/sitio cuando exista entorno alterno. Registrar observado contra objetivo, desviaciones, responsables y correcciones.

## 6. Reversión y retorno

Toda recuperación productiva conserva la copia del estado fallido hasta la aceptación del propietario. El retorno sigue la sección 8 del BCP.
