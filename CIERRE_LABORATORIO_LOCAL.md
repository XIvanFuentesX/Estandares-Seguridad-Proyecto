# Cierre del laboratorio local — SGSI UVCG

Fecha: 2026-10-24. Entorno: Windows, Docker Desktop (VM WSL2 de 7.6 GiB), 16 GB de RAM. Universidad ficticia (3,000 estudiantes, 180 docentes, 120 administrativos). Este documento cierra la **implementación práctica local**; no declara el 100 % de los requisitos originales, porque varios dependen de Azure, de licencias o de aprobación institucional.

## 1. Inventario de servicios implementados

| Servicio | Imagen | Red(es) | Exposición | Estado |
|---|---|---|---|---|
| Nginx (proxy TLS) | `local-proxy:latest` | dmz, apps | 127.0.0.1:8080/8443 | healthy |
| API Flask/Gunicorn | `local-api` | apps, datos | ninguna | healthy |
| Keycloak 26.8.1 (OIDC, MFA, RBAC) | `local-keycloak` | apps, identity | sólo vía proxy | healthy |
| PostgreSQL académico | `local-postgres-hardened:16` (UID 70, sin gosu) | datos (interna) | ninguna | healthy |
| PostgreSQL identidad | `local-postgres-hardened:16` | identity (interna) | ninguna | healthy |
| Schedulers de respaldo ×2 | `local-backup-tool:latest` | datos / identity | ninguna | healthy |
| Monitor de disponibilidad | `local-api` (perfil `monitoring`) | dmz | ninguna | running (15 s) |
| Restauración aislada ×2, PITR, IDS, escáneres | perfiles `recovery`, `ids`, `security` y contenedores efímeros | recovery (interna) / none | ninguna | bajo demanda |
| Tarea `SGSI-UVCG-Prueba-Recuperacion` | Programador de tareas (usuario actual, sin elevación) | — | — | domingos 10:00 |

## 2. Matriz de requisitos

Estados: IMPLEMENTADO, PARCIAL, PREPARADO, NO IMPLEMENTADO, NO APLICA JUSTIFICADO.

| ID | Requisito | Estado | Evidencia / prueba | Riesgo | Control |
|---|---|---|---|---|---|
| RQ-01 | IAM centralizado OIDC | IMPLEMENTADO | `pruebas_identidad.py` (IAM-RBAC-MFA) | R-001 | A.5.16 |
| RQ-02 | MFA | IMPLEMENTADO | TOTP obligatorio verificado | R-002 | A.8.5 |
| RQ-03 | RBAC / mínimo privilegio | IMPLEMENTADO | Matriz 200/401/403 de 4 roles; ACC-001/002 | R-001 | A.5.15; A.8.3 |
| RQ-04 | Zero Trust (demostrativo) | PARCIAL | Verificación explícita de token/rol por ruta; sin postura de dispositivo | R-001 | A.8.20 |
| RQ-05 | HTTPS/TLS y cabeceras | IMPLEMENTADO | `pruebas_locales.py` | R-003 | A.8.24 |
| RQ-06 | Gestión de certificados | PARCIAL | Certificado de laboratorio autofirmado; sin PKI ni renovación | R-008 | A.8.24 |
| RQ-07 | Segmentación / DMZ local | IMPLEMENTADO (Docker) | `validar_segmentacion.ps1`; redes internas | R-001 | A.8.22 |
| RQ-08 | NGFW | NO IMPLEMENTADO | Un proxy inverso y las redes Docker no sustituyen un NGFW; Azure Firewall preparado en Terraform | R-012 | A.8.20 |
| RQ-09 | VLAN físicas | NO APLICA JUSTIFICADO | Un solo equipo; las redes Docker no equivalen a VLAN | — | A.8.22 |
| RQ-10 | Gestión de secretos | PARCIAL | `.env` fuera de Git, clave de cifrado separada; ACL amplia (INC-010, CHG-005 pendiente) | R-015 | A.5.17 |
| RQ-11 | Endurecimiento de imágenes y contenedores | IMPLEMENTADO | Vigilancia: raíz de sólo lectura, no root, cap_drop, no-new-privileges en los 5 servicios | R-008 | A.8.9 |
| RQ-12 | Gestión de vulnerabilidades | IMPLEMENTADO | Escaneo de imágenes en uso; PostgreSQL 0/0; Keycloak 2 HIGH sin fix | R-009; R-010 | A.8.8 |
| RQ-13 | Gestión de configuración | IMPLEMENTADO | Línea base SHA-256 + autoprueba de detección | R-008 | A.8.9 |
| RQ-14 | Gestión de cambios | IMPLEMENTADO (laboratorio) | CHG-001..005 con rollback | R-008 | A.8.32 |
| RQ-15 | Registro de incidentes | IMPLEMENTADO (laboratorio) | INC-001..011 con auditoría encadenada | R-012 | A.5.24–A.5.27 |
| RQ-16 | Solicitudes de acceso | IMPLEMENTADO (ejercicio) | ACC-001/002 | R-016 | A.5.18 |
| RQ-17 | Seguimiento de activos | IMPLEMENTADO | Inventario de 33 activos; AST-001..004 | — | A.5.9 |
| RQ-18 | SIEM: recolección y correlación | PARCIAL | 12 fuentes, 11 reglas, consultas históricas, tablero; ingesta de logs Docker por lotes | R-012 | A.8.15; A.8.16 |
| RQ-19 | SIEM: integridad y retención | IMPLEMENTADO | Sellado encadenado + `verify`; retención de 30 días (sin borrado) | R-012 | A.8.15 |
| RQ-20 | Monitoreo de disponibilidad continuo | IMPLEMENTADO | `uptime-monitor` cada 15 s; alerta SIEM-AVAIL-001 | R-004 | A.8.16 |
| RQ-21 | Alertas por fallos de backup y WAL | IMPLEMENTADO | SIEM-BACKUP-001 y SIEM-WAL-001 disparadas por fallos reales/inyectados | R-007; R-019 | A.8.16 |
| RQ-22 | Alertas por modificación no autorizada | IMPLEMENTADO | SIEM-CFG-001 (autoprueba) | R-008 | A.8.16 |
| RQ-23 | IDS con casos maliciosos y benignos | IMPLEMENTADO (offline) | 7/7 detecciones, 0 falsos positivos | R-001 | A.8.16 |
| RQ-24 | IDS en vivo / IPS en línea | NO IMPLEMENTADO | Requiere NET_RAW/NET_ADMIN (no autorizado) | R-012 | A.8.20 |
| RQ-25 | Detección de cambios de archivos y monitoreo de procesos | IMPLEMENTADO (contenedores) | `vigilancia_contenedores.py`: proceso no autorizado detectado; escritura bloqueada | R-013 | A.8.7 |
| RQ-26 | EDR en endpoints | NO IMPLEMENTADO | Sin agente; Defender for Endpoint/Wazuh requieren instalación o licencia | R-013 | A.8.7 |
| RQ-27 | DLP con bloqueo e incidentes | PARCIAL | Compuerta de transferencia; no cubre endpoint, correo ni nube | R-003 | A.8.12 |
| RQ-28 | Clasificación de información | IMPLEMENTADO | 4 niveles aplicados por la compuerta DLP | R-003 | A.5.12 |
| RQ-29 | MDM / cumplimiento de dispositivos | PREPARADO | Política + simulación con dispositivos ficticios + mapeo a Intune | R-013 | A.8.1 |
| RQ-30 | Respaldos cifrados de ambas bases, programados, con SHA-256 | IMPLEMENTADO | Schedulers diarios; copia heredada cifrada (INC-007) | R-005; R-006 | A.8.13 |
| RQ-31 | Restauración aislada y pruebas periódicas | IMPLEMENTADO | Tarea semanal verificada; restauración dual | R-007 | A.8.13 |
| RQ-32 | Retención | PARCIAL (simulación) | GFS 7/4/3 en dry-run; borrado no autorizado | R-007 | A.8.10 |
| RQ-33 | WAL/PITR con RPO medido | PARCIAL | Réplicas: recuperación exacta, RPO ≈ 56 s, RTO ≈ 3 s; principales con `archive_mode=off` (preparado) | R-019 | A.8.13 |
| RQ-34 | Continuidad API e identidad | IMPLEMENTADO | 12 s y 70 s, integridad preservada | R-004 | A.5.30 |
| RQ-35 | Redundancia / alta disponibilidad | NO IMPLEMENTADO | Un único host; Azure preparado | R-004; R-011 | A.8.14 |
| RQ-36 | Copia offsite/inmutable | NO IMPLEMENTADO | Requiere Azure o medio externo | R-011 | A.8.13 |
| RQ-37 | Acceso remoto seguro | PREPARADO | Bastion/VPN en Terraform; localmente sólo loopback | R-016 | A.6.7; A.8.20 |
| RQ-38 | Virtualización adicional | NO APLICA JUSTIFICADO | Una VM extra (pfSense, Wazuh) superaría la RAM disponible con los servicios activos | — | — |
| RQ-39 | Inventario, BIA, riesgos 27005/800-30, OCTAVE, calor, tratamiento | IMPLEMENTADO (borrador académico) | `governance/*`; trazabilidad 21/21 | — | Cl. 6.1 |
| RQ-40 | SoA 93 controles | IMPLEMENTADO (borrador) | 30 implementados / 38 parciales / 25 pendientes | — | Cl. 6.1.3 |
| RQ-41 | Políticas ISO 27001/27002 | PREPARADO | `policies/politicas-sgsi-iso27001.md` (propuestas) | — | A.5.1 |
| RQ-42 | BCP/DRP ISO 22301 | IMPLEMENTADO (borrador + pruebas) | `bcp.md`, `drp.md` con tiempos observados | R-004 | A.5.29 |
| RQ-43 | COBIT 2019, ITIL 4, TIA-942 | PREPARADO | `governance/marcos-cobit-itil-tia942.md` (TIA-942 local: no aplica) | — | — |
| RQ-44 | Aprobaciones, entrevistas y talleres institucionales | NO IMPLEMENTADO | No se inventaron | — | Cl. 5 |

Resumen (conteo verificado sobre la tabla): IMPLEMENTADO 25 · PARCIAL 7 · PREPARADO 4 · NO IMPLEMENTADO 6 · NO APLICA JUSTIFICADO 2 (total 44; las aclaraciones entre paréntesis no cambian el estado principal).

## 3. Pruebas

Validación integral reproducible: `scripts/validar_sgsi.ps1 -IncludeIds -IncludeRecovery -IncludeSecurity -IncludeContinuity` (ver §7). El manual de ejecución está en `MANUAL_EJECUCION.md`.

## 4. Evidencias

Índice completo en `evidencias/INDICE.md`; fichas por control (M01–M21) en `evidencias/CONTROLES_IMPLEMENTADOS.md`; registros operativos en `governance/registros-operativos.md`. **Capturas de pantalla:** no se generaron en esta etapa; quedan como pendiente documental. Pueden tomarse capturas auténticas del tablero SIEM (`evidencias/siem/tablero-siem-*.html`) y de la consola de Keycloak; no se fabricaron imágenes.

## 5. Brechas y riesgos residuales

Residuales críticos: R-011 (sin sitio ni copia externa) y R-013 (sin MDM/EDR). Altos: R-004, R-009 si se revierte, R-010 (Keycloak upstream), R-014, R-017/R-020 (cloud), R-019 hasta activar WAL en las principales. Detalle en `governance/matriz-riesgos.md` y `matriz-calor.md`.

## 6. Porcentajes

**Laboratorio práctico (10 módulos ponderados): 82.5 %** (antes 78 %).

| Módulo | Antes | Ahora | Motivo |
|---|---:|---:|---|
| Identidad/MFA/RBAC | 9 | 9 | — |
| TLS/aplicación | 9 | 9 | — |
| Monitoreo/SIEM | 8 | 8.5 | Sellado de integridad, monitor continuo, 11 reglas; ingesta Docker por lotes |
| IDS/endpoint | 7 | 7.5 | Vigilancia de contenedores; sin IDS en vivo ni EDR |
| Respaldos/recuperación | 9.5 | 9.5 | PITR en réplicas; principales sin WAL |
| Zero Trust | 8 | 8 | — |
| MDM/DLP | 4 | 5.5 | Compuerta DLP real; MDM sólo simulado |
| Azure | 6 | 7 | IaC modular validada, pruebas y costos oficiales; nada desplegado |
| Vulnerabilidades | 9 | 9 | — |
| Continuidad | 8.5 | 9 | PITR, registros operativos, lecciones aprendidas |

**Ejecución local de los requisitos locales:** de los 40 requisitos con componente local (excluye RQ-09, RQ-38, RQ-43 y RQ-44), 25 implementados y 7 parciales → **≈ 71 %** (parciales a la mitad: (25 + 3.5)/40).

**Cumplimiento de la práctica total (académico): ≈ 69 %** = laboratorio 50 % × 82.5 % + gobierno documental 30 % × 85 % + validación institucional, despliegue Azure y auditoría 20 % × 12 %.

## 7. Resultado de la validación integral

Última corrida **completa**: `evidencias/automatizacion/validacion-sgsi-20261024-112033.json` (29 controles, todos los perfiles):
**27 exitosos, 1 fallido, 1 no verificable, 0 omitidos**.

- `PITR-PRINCIPALES` = **no verificable**: `archive_mode=off` en `db` e `identity-db` (activación pendiente de autorización).
- `AZURE-STATIC` = **fallido** en esa corrida, porque coincidió con la reestructuración modular de `azure/` en curso. Reejecutado por separado tras la reestructuración: 32 verificaciones OK, 0 errores (`evidencias/azure/validacion-estatica-reejecucion-20261024.txt`). La corrida completa posterior **no terminó**: el sistema la detuvo por falta de memoria del equipo (INC-012). No se cuenta como exitosa; debe repetirse cuando haya memoria disponible.

Controles exitosos en la última corrida completa: Compose, HTTPS, IAM/MFA/RBAC, segmentación, SIEM sintético e integrado (12 fuentes, 10 reglas disparadas), sellado SIEM, backups programados, integridad de configuración y su autoprueba, PostgreSQL endurecido + rollback preparado, tarea programada, vigilancia de contenedores, monitor de disponibilidad, compuerta DLP, simulación MDM, registros operativos, retención en simulación, gobernanza y trazabilidad, DLP demostrativo, IDS (7/7, 0 FP), backup + restauración dual, **PITR en réplicas**, DevSecOps, escaneo de imágenes en uso, continuidad de la API (12.0 s) e IAM (70.2 s).

## 8. Dependencias de Azure

Copia offsite/inmutable (RQ-36), redundancia (RQ-35), NGFW (RQ-08), acceso remoto (RQ-37), SIEM empresarial/Sentinel, Defender, Intune/Entra ID P1-P2 (RQ-26, RQ-29). Estado y costos en `CIERRE_AZURE.md`.

## 9. Autorizaciones pendientes

1. Activar WAL/PITR en `db` e `identity-db` (`local/compose.pitr.yaml`; recrea ambas bases).
2. Restringir la ACL de `local/.env` (CHG-005).
3. Eliminar la copia heredada sin cifrar (ya existe la copia cifrada y verificada).
4. Borrado real por retención y limpieza de bases restauradas acumuladas.
5. Programar el ciclo SIEM (tarea de Windows cada 15 min) para la ingesta continua de logs Docker.
6. IDS en vivo con NET_RAW/NET_ADMIN.
7. Suscripción Azure, presupuesto y despliegue (ver `CIERRE_AZURE.md`).
