# Conjunto de políticas del SGSI — UVCG (propuesta)

Estado: **propuesta académica pendiente de aprobación por la Dirección**. Cada política indica qué parte está **ejecutada en el laboratorio** (con evidencia verificable) y qué parte es sólo **política propuesta**. Las referencias corresponden a ISO/IEC 27001:2022 (cláusulas) y al Anexo A / ISO/IEC 27002:2022.

| ID | Política | Requisitos clave | Ejecutado en laboratorio | Sólo propuesto | Referencias |
|---|---|---|---|---|---|
| POL-01 | Política general de seguridad | Alcance, objetivos, roles, mejora continua | Estructura del SGSI, SoA y validación | Aprobación y comunicación por la Dirección | Cl. 5.2; A.5.1 |
| POL-02 | Control de acceso e identidad | Mínimo privilegio, MFA, revisiones periódicas, solicitudes registradas | Keycloak OIDC, MFA TOTP, 4 roles, RBAC por ruta, ACC-001/002 | Revisión trimestral formal de accesos | A.5.15–A.5.18; A.8.2; A.8.3; A.8.5 |
| POL-03 | Criptografía | TLS 1.2+, cifrado de respaldos, gestión de claves separada | TLS en Nginx, AES-256/PBKDF2 en respaldos, clave fuera del repositorio de copias | Vault/HSM, rotación, ACL estricta de `.env` (CHG-005) | A.8.24 |
| POL-04 | Respaldo y recuperación | Copias cifradas, verificación, pruebas, retención | Respaldos diarios, SHA-256, restauración aislada semanal programada, PITR en réplicas, retención simulada | Copia offsite/inmutable, WAL en principales, borrado por retención | A.8.13; A.5.30 |
| POL-05 | Registro y monitoreo | Centralizar, proteger y revisar registros | SIEM ligero con sellado encadenado, 11 reglas, monitor de disponibilidad | SIEM empresarial, revisión diaria por SOC | A.8.15; A.8.16 |
| POL-06 | Gestión de incidentes | Registrar, clasificar, contener, resolver y aprender | Registro INC con auditoría; procedimiento de investigación | Notificación legal, equipo de respuesta formal | A.5.24–A.5.28; A.6.8 |
| POL-07 | Gestión de cambios y configuración | Aprobación, rollback, línea base | Registro CHG, línea base SHA-256 con autoprueba, rollback de PostgreSQL verificado | CAB institucional | A.8.9; A.8.32 |
| POL-08 | Gestión de vulnerabilidades | Escaneo periódico, priorización, mitigación | Trivy/Bandit/pip-audit, registro detallado, imagen PostgreSQL sin `gosu` | Escaneo mensual programado, SLA de parcheo | A.8.8 |
| POL-09 | Clasificación y DLP | Etiquetado y control de transferencia | 4 niveles, compuerta DLP con bloqueo e incidentes | DLP de endpoint/correo/nube | A.5.12–A.5.14; A.8.12 |
| POL-10 | Dispositivos y BYOD | Cumplimiento antes de acceder a información sensible | Política y simulación de cumplimiento con dispositivos ficticios | MDM real (Intune), acceso condicional | A.6.7; A.8.1; A.7.9 |
| POL-11 | Seguridad de redes y Zero Trust | Segmentación, mínima exposición, verificación explícita | Redes Docker internas, sólo el proxy publica en 127.0.0.1, matriz Zero Trust | NGFW, microsegmentación física, VLAN | A.8.20–A.8.22 |
| POL-12 | Continuidad del negocio | BIA, BCP/DRP, pruebas | BIA, BCP, DRP, pruebas de continuidad API/IAM | Sitio alterno, ejercicio con roles reales | A.5.29; A.5.30; ISO 22301 |
| POL-13 | Proveedores y nube | Evaluación, contratos, salida | Arquitectura Azure preparada (no desplegada) | Due diligence, SLA, cláusulas contractuales | A.5.19–A.5.23 |
| POL-14 | Uso aceptable y concienciación | Reglas de uso, capacitación | — | Programa de capacitación | A.5.10; A.6.3 |
| POL-15 | Seguridad física | Perímetros, equipos, suministros | — (no aplica al laboratorio) | Levantamiento físico institucional | A.7.1–A.7.14 |

La matriz de acceso Zero Trust (`matriz-acceso-zero-trust.md`), la clasificación (`clasificacion-informacion.md`), BYOD/MDM (`byod-mdm.md`) y el procedimiento de investigación de incidentes (`procedimiento-investigacion-incidentes.md`) desarrollan POL-02, POL-09, POL-10 y POL-06.
