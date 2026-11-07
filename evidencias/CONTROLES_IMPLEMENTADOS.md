# Fichas de controles implementados

## M01-IAM-01 — Identidad, MFA y RBAC

- **Descripción:** Keycloak centraliza cuatro usuarios ficticios y roles `administrador`, `docente`, `estudiante`, `administrativo`; exige TOTP SHA-256 y política de contraseñas. Flask valida JWT/JWKS, emisor, expiración, cliente y rol.
- **Estándar relacionado:** ISO 27001/27002 A.5.15–A.5.18; NIST CSF PR.AA; Zero Trust/NIST SP 800-207.
- **Riesgo mitigado:** suplantación, privilegios excesivos y acceso no autorizado.
- **Archivos:** `local/identity/*`, `local/api/app.py`, `local/compose.yaml`, `scripts/pruebas_identidad.py`.
- **Configuración:** IdP y base de identidad en red interna; consola no publicada; eventos `LOGIN`/`LOGIN_ERROR`; secretos en `.env` excluido.
- **Prueba y resultado real:** cuatro roles, TOTP obligatorio/válido, matriz permitida/denegada, token inválido y eventos: **exit 0** el 2026-10-24 09:15:33 -06:00.
- **Estado:** **implementado**.

## M02-APP-01 — TLS y endurecimiento de aplicación

- **Descripción:** HTTPS por Nginx, certificado autofirmado identificado como laboratorio, redirección HTTP, headers, rutas protegidas, métodos bloqueados y contenedores endurecidos.
- **Estándar relacionado:** ISO 27002 A.8.20, A.8.24, A.8.26, A.8.28; NIST CSF PR.DS/PR.PS.
- **Riesgo mitigado:** interceptación, manipulación y superficie de ataque del contenedor.
- **Archivos:** `local/nginx/*`, `local/tls/*` (clave ignorada), `local/api/*`, `local/compose.yaml`, `scripts/pruebas_locales.py`.
- **Configuración:** TLS sólo en loopback 8443; Nginx único punto publicado; raíces de solo lectura; `tmpfs` seguro; capacidades reducidas.
- **Prueba y resultado real:** redirección, TLS confiando exclusivamente en CA de laboratorio, health 200, ruta sin token 401, cinco métodos 403, headers correctos: **exit 0** el 2026-10-24 09:14:40 -06:00.
- **Estado:** **implementado en laboratorio**.

## M03-SIEM-01 — Monitoreo centralizado y correlación (SIEM ligero)

- **Descripción:** ingesta de logs Docker de Nginx, Flask, Keycloak y ambas PostgreSQL, bitácora de backups y alertas Suricata; normalización con hora UTC y origen, redacción de secretos, búsqueda SQLite, 6 reglas de correlación, alertas, tablero HTML y retención de 30 días.
- **Estándar relacionado:** ISO 27002 A.8.15, A.8.16, A.5.25, A.5.28; NIST CSF DE.CM/DE.AE.
- **Riesgo mitigado:** R-002, R-007, R-012 (detección tardía, fuerza bruta, fallo de backup no advertido).
- **Archivos:** `scripts/siem_ligero.py`, `scripts/siem_pipeline.py`, `scripts/pruebas_siem.py`, `local/monitoring/rules.json`, `evidencias/siem/*`.
- **Configuración:** sin puertos ni servicio residente; rotación Docker 10 MB × 5; retención SIEM sólo informa candidatos salvo `--apply`.
- **Prueba y resultado real:** ciclo integrado con 10 orígenes; SIEM-AUTH, RBAC, DB, IDS y BACKUP disparadas desde eventos reales (fallos PostgreSQL y de backup provocados de forma controlada); 0 secretos sin redactar; 2026-10-24 09:55:32 -06:00 (`siem/pipeline-siem-20261024-095532.json`).
- **Estado:** **implementado como SIEM ligero**; brechas frente a un SIEM empresarial en `siem/REPORTE-SIEM.md` (agentes, HA, inmutabilidad, UEBA, SOAR).

## M04-IDS-01 — Detección Suricata controlada

- **Descripción:** Suricata 7 analiza un PCAP sintético autorizado con 7 reglas locales documentadas (path traversal, SQLi, escáner, consola admin, puertos 5432/9000, ráfaga de login) y un escenario benigno de control.
- **Estándar relacionado:** ISO 27002 A.8.16, A.8.20, A.8.22; NIST CSF DE.CM.
- **Riesgo mitigado:** R-001, R-002, R-016 (actividad sospechosa no detectada).
- **Archivos:** `local/ids/rules/uvcg.rules`, perfil `ids`, `scripts/generar_pcap_ids.py`, `scripts/validar_alerta_ids.py`, `evidencias/ids/*`.
- **Configuración:** `network_mode: none`, raíz de solo lectura, sin capacidades; salidas previas archivadas en `ids/historico/`.
- **Prueba y resultado real:** 8 escenarios: 7 verdaderos positivos y 0 falsos positivos; alertas integradas en el SIEM (SIEM-IDS-001); segmentación validada.
- **Estado:** **parcial (offline)**; la captura en vivo requiere `NET_RAW/NET_ADMIN` (autorización); no es IPS, EDR ni XDR (`ids/REPORTE-IDS.md`).

## M05-BCP-01 — Respaldos programados, cifrados y restauración aislada

- **Descripción:** schedulers diarios para la base académica y la de identidad; `pg_dump` cifrado AES-256/PBKDF2, SHA-256, manifiesto y bitácora con éxitos y fallos; restauración automatizada en instancias aisladas; prueba periódica comparada con el RTO/RPO del BIA.
- **Estándar relacionado:** ISO 27002 A.8.13, A.5.30, A.8.24; ISO 22301.
- **Riesgo mitigado:** R-005, R-006, R-007, R-019.
- **Archivos:** `local/backup/*`, `scripts/backup_postgres.ps1`, `scripts/restaurar_prueba.ps1`, `scripts/prueba_recuperacion_periodica.ps1`, `scripts/validar_backups_programados.ps1`.
- **Configuración:** nunca restaura sobre la base activa; clave fuera del directorio de copias; retención de 30 días sin borrado automático; la copia restaurada se elimina tras verificarse.
- **Prueba y resultado real:** restauración académica 8.537 s (3 cursos) e identidad 9.056 s (5 identidades), SHA-256 verificado, base principal no modificada; fallo de backup provocado y alertado; 2026-10-24 10:01:59 -06:00 (`backup/REPORTE-BACKUP-RECUPERACION.md`).
- **Estado:** **implementado localmente**; pendientes: copia offsite/inmutable, WAL/PITR para cumplir el RPO y programación en Windows.

## M06-ZTA-01 — Zero Trust demostrativo

- **Descripción:** verificar explícitamente identidad/MFA/token/rol, mínimo privilegio, segmentación, decisiones registradas y control de sesión.
- **Estándar relacionado:** NIST SP 800-207; NIST CSF PR.AA; ISO 27002 A.5.15/A.8.20.
- **Riesgo mitigado:** confianza implícita por ubicación y movimiento lateral.
- **Archivos:** `policies/matriz-acceso-zero-trust.md`, API, Keycloak, Nginx y redes Compose.
- **Configuración:** matriz por ruta/rol y redes `dmz`, `apps`, `datos`, `identity` internas.
- **Prueba y resultado real:** decisiones 200/401/403 verificadas para cuatro roles; metadatos Docker confirman que sólo proxy publica puertos.
- **Estado:** **implementado demostrativo**; postura de dispositivo y acceso adaptativo están pendientes.

## M07-DLP-01 — Clasificación, DLP y BYOD

- **Descripción:** cuatro niveles de clasificación, escáner DLP sobre datos sintéticos y política de requisitos BYOD/MDM.
- **Estándar relacionado:** ISO 27002 A.5.12–A.5.13, A.8.12; NIST CSF PR.DS.
- **Riesgo mitigado:** exposición y transferencia no autorizada de información sensible.
- **Archivos:** `policies/clasificacion-informacion.md`, `policies/byod-mdm.md`, `scripts/dlp_scan.py`, `local/dlp/samples/*`.
- **Configuración:** reporta sólo hash parcial/tipo, nunca el valor coincidente.
- **Prueba y resultado real:** 2 hallazgos sintéticos y acción `blocked`, exit 0 el 2026-10-24 09:15:33 -06:00.
- **Estado:** **DLP parcial; MDM preparado/pendiente** para Intune u otra plataforma licenciada.

## M08-AZ-01 — Arquitectura Azure preparada

- **Descripción:** Terraform para RG, hub-and-spoke, cinco zonas, NSG, peerings, RBAC, monitoreo, almacenamiento GRS/bóveda y gateway VPN opcionales.
- **Estándar relacionado:** ISO 27002 A.5.23/A.8.20; NIST CSF PR.PS; TIA-942; COBIT APO13/DSS04.
- **Riesgo mitigado:** despliegue cloud improvisado, exposición pública y costo accidental.
- **Archivos:** `azure/main.tf`, `.terraform.lock.hcl`, `terraform.tfvars.example`, `README.md`.
- **Configuración:** funciones con costo `false`; almacenamiento privado; deny lateral; sin secretos reales.
- **Prueba y resultado real:** `terraform fmt -check` y `terraform validate` con AzureRM 4.81.0: **válido**, sin despliegue, 2026-10-24.
- **Estado:** **preparado, no implementado en Azure** por falta de suscripción/autorización.

## M09-VULN-01 — Pipeline DevSecOps y gestión de vulnerabilidades

- **Descripción:** Bandit, pip-audit y Trivy (SAST, dependencias, secretos, misconfiguraciones e imágenes SO+JAR), más el escaneo de las imágenes **realmente en ejecución**; registro detallado con CVE, versión, exposición, mitigación y riesgo residual.
- **Estándar relacionado:** ISO 27002 A.8.8, A.8.25, A.8.29; NIST CSF ID.RA/PR.PS.
- **Riesgo mitigado:** R-008, R-009, R-010.
- **Archivos:** `security-tools/*`, perfil `security`, `scripts/ejecutar_seguridad.ps1`, `scripts/escanear_imagenes_en_uso.ps1`, `scripts/generar_registro_vulnerabilidades.py`.
- **Configuración:** escáneres efímeros sin privilegios; las imágenes locales se analizan exportadas.
- **Prueba y resultado real:** imágenes en uso: PostgreSQL endurecida 0/0, API 0/0, proxy 0/0, backup 0/0 y Keycloak 0 CRITICAL/2 HIGH (OpenJDK sin fix). La imagen oficial anterior conserva 1 CRITICAL + 25 HIGH en `gosu` (`security/escaneo-imagenes-en-uso-post-upgrade.json`).
- **Estado:** **implementado**; los 26 hallazgos de PostgreSQL quedan **mitigados por eliminación del componente**, no corregidos upstream. Keycloak sigue pendiente de upstream.

## M10-BCM-01 — Continuidad: interrupción y recuperación

- **Descripción:** detención controlada de la API y de Keycloak, observación del fallo por el proxy, recuperación y verificación de integridad; BIA, BCP y DRP con tiempos observados frente a objetivos.
- **Estándar relacionado:** ISO 22301; ISO 27002 A.5.29, A.5.30, A.8.14; COBIT DSS04.
- **Riesgo mitigado:** R-004 (parcial), recuperación no probada y objetivos irreales.
- **Archivos:** `scripts/prueba_continuidad.ps1 -Service api|keycloak`, `governance/bcp.md`, `governance/drp.md`, `evidencias/recovery/*`.
- **Configuración:** reinicio `--no-deps` sólo del servicio probado; no toca volúmenes.
- **Prueba y resultado real:** API 504 → 200 en 11.927 s (3 cursos); Keycloak sin respuesta → 200 en 70.822 s (5 identidades); 2026-10-24 09:58–10:00 -06:00.
- **Estado:** **implementado en laboratorio**; la pérdida de host/sitio no es recuperable hoy (R-011) y el RPO no es alcanzable (R-019).

## M11-GOV-01 — Gobierno del riesgo: inventario, BIA, riesgos, OCTAVE, tratamiento y SoA

- **Descripción:** 21 activos (implementados/planificados/académicos), BIA de 7 procesos con escalas explícitas, 19 riesgos ISO 27005/NIST 800-30 con P×I inherente y residual, matrices de calor 5×5, OCTAVE Allegro de escritorio (8 escenarios), plan de tratamiento y SoA de 93 controles.
- **Estándar relacionado:** ISO 27001 cláusulas 6.1.2, 6.1.3, 8.2 y 8.3; ISO 27005; NIST SP 800-30; ISO 22301 (BIA).
- **Riesgo mitigado:** decisiones de seguridad sin base de riesgo ni trazabilidad.
- **Archivos:** `governance/*`, `scripts/generar_gobernanza_sgsi.py`, `scripts/validar_trazabilidad.py`.
- **Configuración:** documentos generados desde una sola fuente; tiempos de laboratorio leídos de las evidencias; supuestos marcados como pendientes de aprobación.
- **Prueba y resultado real:** 21 verificaciones de trazabilidad (IDs, RPO ≤ RTO < MTPD, P×I, activos/procesos/controles referenciados, evidencias existentes): 0 fallidas (`gobernanza/trazabilidad-*.json`).
- **Estado:** **borrador académico completo**; sin entrevistas, talleres ni aprobación institucional.

## M12-CFG-01 — Integridad de configuraciones

- **Descripción:** línea base SHA-256 de 18 archivos de configuración (Compose, Nginx, realm, reglas IDS/SIEM, Dockerfiles, scripts de backup); detección de cambios, faltantes y nuevos.
- **Estándar relacionado:** ISO 27002 A.8.9, A.8.32, A.5.28.
- **Riesgo mitigado:** R-008 (cambio no autorizado o no detectado).
- **Archivos:** `scripts/integridad_configuracion.py`, `evidencias/integridad/*`.
- **Configuración:** excluye secretos del hash (sólo verifica su presencia); la línea base anterior se archiva al aprobar cambios.
- **Prueba y resultado real:** 18 archivos verificados, 0 cambios (2026-10-24 10:07 -06:00).
- **Estado:** **implementado**; no sustituye el control de versiones ni un proceso formal de cambios.

## M13-PG-01 — Actualización controlada de PostgreSQL a imagen endurecida

- **Descripción:** `db` e `identity-db` migradas de `postgres:16-alpine` a `local-postgres-hardened:16` (misma versión 16.15 y mismo binario, sin `gosu`, UID 70) con respaldo lógico, copia en frío de los volúmenes, huella de datos y reversión automática.
- **Estándar relacionado:** ISO 27002 A.8.8, A.8.9, A.8.32, A.8.13.
- **Riesgo mitigado:** R-009 (y R-008 por control de cambios).
- **Archivos:** `local/postgres-hardened/Dockerfile`, `local/compose.yaml`, `scripts/actualizar_postgres_endurecido.ps1`, `scripts/huella_datos_postgres.ps1`, `scripts/rollback_postgres.ps1`, `local/rollback/*`.
- **Configuración:** cambio mínimo del Compose (imagen, `user: "70:70"`, sin `cap_add`); volúmenes conservados.
- **Prueba y resultado real:** bases `healthy` en 7.3 s y cinco servicios en 55.7 s; 0 diferencias de datos; HTTPS, MFA, RBAC y segmentación correctos; reversión verificada (la imagen anterior arranca sobre las copias en frío); 2026-10-24 10:22 (`postgres-upgrade/REPORTE-ACTUALIZACION-POSTGRESQL.md`).
- **Estado:** **implementado**.

## M14-REC-02 — Prueba de recuperación programada

- **Descripción:** tarea semanal `SGSI-UVCG-Prueba-Recuperacion` (domingos 10:00) que restaura ambas bases en instancias aisladas, compara con el RTO/RPO y registra fecha, duración y resultado.
- **Estándar relacionado:** ISO 27002 A.8.13, A.5.30; ISO 22301 (ejercicios y pruebas).
- **Riesgo mitigado:** R-005, R-006, R-007, R-019.
- **Archivos:** `scripts/tarea_recuperacion_programada.ps1`, `evidencias/recovery/tarea-programada/*`.
- **Configuración:** cuenta actual, sesión interactiva, sin credenciales ni elevación, sin ejecuciones simultáneas, límite de 30 minutos, detección de Docker no disponible.
- **Prueba y resultado real:** ejecución manual, concurrencia (`omitido`), Docker no disponible (`no_verificable`) y ejecución desde el Programador (`LastTaskResult 0`, 20.1 s).
- **Estado:** **implementado**; requiere sesión iniciada con Docker Desktop.

## M15-RET-01 — Retención de respaldos en simulación

- **Descripción:** política GFS configurable (diaria 7 días, semanal 4 semanas, mensual 3 meses, siempre la copia más reciente) evaluada en modo simulación con candidatos, antigüedad, tamaño, ruta, motivo y elementos protegidos.
- **Estándar relacionado:** ISO 27002 A.8.10, A.8.13, A.5.33.
- **Riesgo mitigado:** R-007 (crecimiento sin control y borrado accidental de copias necesarias).
- **Archivos:** `local/backup/retention-policy.json`, `scripts/simular_retencion.py`, `evidencias/retencion/*`.
- **Configuración:** el simulador no contiene operaciones de borrado; protege `local/rollback`, `evidencias` y las copias usadas en restauraciones.
- **Prueba y resultado real:** 16 conjuntos: 2 conservar, 10 protegidos, 4 candidatos (603 KB); el número de archivos no cambió; hallazgo de una copia antigua sin cifrar.
- **Estado:** **implementado sólo en simulación**; la política no está validada institucionalmente y el borrado real no está autorizado.

## M16-PITR-01 — WAL/PITR en réplicas aisladas

- **Descripción:** réplicas aisladas de ambas bases cargadas con el respaldo cifrado real; respaldo base, archivado WAL continuo, filas ficticias antes y después del punto objetivo, recuperación a `recovery_target_time` y verificación; monitor WAL (fallos de `archive_command`, retraso y crecimiento).
- **Estándar relacionado:** ISO 27002 A.8.13, A.5.30; ISO 22301; NIST CSF RC.RP.
- **Riesgo mitigado:** R-019 (RPO), R-005, R-006.
- **Archivos:** `scripts/pitr_prueba.py`, `scripts/monitor_wal.py`, `local/compose.pitr.yaml` (preparado), `evidencias/pitr/*`.
- **Configuración:** `wal_level=replica`, `archive_mode=on`, `archive_timeout=60`, archivo en volumen aislado `sgsi_pitr_archive`; recuperación sin red; manifiesto SHA-256 revalidado antes de restaurar.
- **Prueba y resultado real:** académica e identidad: 3 filas anteriores presentes y 3 posteriores ausentes (`recovery stopping before commit …`); RTO técnico 2.5–2.8 s; RPO observado ≈ 56–58 s (objetivos: 4 h y 15 min); fallo inyectado de archivado detectado y alerta SIEM-WAL-001 (`evidencias/pitr/pitr-20261024-105933.json`).
- **Estado:** **implementado en réplicas**; en las bases principales `archive_mode=off` → RPO real todavía limitado al backup diario hasta que se autorice `compose.pitr.yaml`.

## M17-SIEM-02 — Integridad del SIEM y monitoreo continuo

- **Descripción:** sellado encadenado SHA-256 de los eventos con verificación; consultas por rango temporal; 11 reglas (incluye WAL, integridad de configuración, disponibilidad, contenedores y DLP); contenedor `uptime-monitor` que sondea Nginx, API y Keycloak cada 15 s por HTTPS.
- **Estándar relacionado:** ISO 27002 A.8.15, A.8.16, A.8.6, A.5.28.
- **Riesgo mitigado:** R-012.
- **Archivos:** `scripts/siem_ligero.py` (`seal`, `verify`), `local/monitoring/uptime_monitor.py`, `local/monitoring/rules.json`.
- **Configuración:** monitor sin socket Docker, sin puertos, usuario no root, raíz de sólo lectura, 64 MiB.
- **Prueba y resultado real:** alteración y borrado simulados en una **copia** de la base de eventos detectados; base real verificada. Ciclo SIEM con 12 fuentes y 9 reglas disparadas con eventos reales.
- **Estado:** **parcial**: la disponibilidad es continua, pero la ingesta de logs Docker es por lotes (requiere ejecutar el ciclo o programarlo con autorización). No es un SIEM empresarial (sin HA, agentes ni almacenamiento WORM).

## M18-EDR-01 — Vigilancia de contenedores (demostración tipo EDR)

- **Descripción:** procesos frente a una lista permitida (`docker top`), deriva del sistema de archivos (`docker diff`) y auditoría de endurecimiento (`docker inspect`) de los cinco servicios.
- **Estándar relacionado:** ISO 27002 A.8.7, A.8.9, A.8.16.
- **Riesgo mitigado:** R-013 (parcial, sólo contenedores), R-008.
- **Archivos:** `scripts/vigilancia_contenedores.py`, `local/monitoring/procesos-permitidos.json`, `evidencias/edr/*`.
- **Prueba y resultado real:** benigno 0 hallazgos; proceso `sleep` no autorizado en la API detectado (SIEM-EDR-001); escritura en `/etc` bloqueada por la raíz de sólo lectura; estado limpio después.
- **Estado:** **implementado como demostración**; no es EDR (no hay agente en endpoints, ni respuesta automática ni telemetría de kernel).

## M19-DLP-02 — Compuerta DLP de transferencia

- **Descripción:** aplicación de la clasificación al copiar archivos hacia canales `interno`/`externo`; detectores de DPI, tarjeta (Luhn) y credenciales; bloqueo con incidente y evento SIEM.
- **Estándar relacionado:** ISO 27002 A.5.12–A.5.14, A.8.12.
- **Riesgo mitigado:** R-003.
- **Archivos:** `scripts/dlp_compuerta.py`, `local/dlp/samples/*` (sintéticas), `evidencias/dlp/compuerta-*.json`.
- **Prueba y resultado real:** canal externo: 1 permitido y 4 bloqueados; canal interno: 3 permitidos y 2 bloqueados; incidentes INC-001..006.
- **Estado:** **parcial**: controla transferencias de archivos del laboratorio; no es DLP de endpoint, correo ni nube.

## M20-MDM-01 — Política de cumplimiento de dispositivos (simulación)

- **Descripción:** política BYOD con requisitos (cifrado, bloqueo, PIN, SO mínimo, antimalware, root/jailbreak, borrado selectivo, perfil de trabajo), decisión de acceso condicional y mapeo a Intune, evaluada sobre 5 dispositivos **ficticios**.
- **Estándar relacionado:** ISO 27002 A.8.1, A.6.7, A.7.9.
- **Riesgo mitigado:** R-013 (preparación).
- **Archivos:** `local/mdm/*`, `scripts/mdm_cumplimiento.py`, `evidencias/mdm/*`.
- **Prueba y resultado real:** 3/5 conformes; un dispositivo con root recibe la acción de borrado selectivo.
- **Estado:** **preparado / simulación**: no existe MDM real; requiere Intune y Entra ID P1.

## M21-OPS-01 — Registros operativos del SGSI

- **Descripción:** incidentes, cambios, solicitudes de acceso, eventos de activos y evaluación de controles en una base con bitácora de auditoría encadenada; exportación a Markdown.
- **Estándar relacionado:** ISO 27001 cl. 8.1 y 10.2; ISO 27002 A.5.24–A.5.27, A.8.32, A.5.18, A.5.9; ITIL 4; COBIT DSS02/BAI06.
- **Riesgo mitigado:** R-008 y R-016 (cambios y accesos sin control).
- **Archivos:** `scripts/gestion_sgsi.py`, `evidencias/gestion/registro-sgsi.db`, `governance/registros-operativos.md`.
- **Prueba y resultado real:** 5 cambios reales (2 implementados con autorización, 1 estándar, 2 pendientes de autorización), 5 incidentes reales y 6 de ejercicio, 2 solicitudes de acceso de ejercicio, 4 eventos de activos; auditoría verificada.
- **Estado:** **implementado en laboratorio**; sin aprobaciones institucionales.
