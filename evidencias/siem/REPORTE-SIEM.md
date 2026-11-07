# Reporte del Módulo A — SIEM y monitoreo

Fecha: 2026-10-24. Alcance: laboratorio local UVCG (Docker Desktop/WSL2, VM de 7.6 GiB asignada desde un host de 16 GB).

## 1. Selección de la solución

| Opción | Requisito de memoria aproximado | Evaluación |
|---|---|---|
| Wazuh (indexer + manager + dashboard) | ≥ 8 GB recomendados para all-in-one; indexer basado en OpenSearch con heap propio | **Descartada**: la VM de Docker tiene 7.6 GiB y ya aloja Keycloak (1 GiB límite), bases, API, proxy y otros proyectos del usuario. Riesgo de agotar memoria y degradar servicios principales. |
| OpenSearch + Dashboards (nodo único) | ≥ 2–4 GB (heap ≥ 1 GB por nodo más Dashboards) | **Descartada por ahora**: viable sólo deteniendo otros servicios; no cumple la restricción de no detener servicios ni ejecutar servicios pesados simultáneos. |
| SIEM ligero propio (Python + SQLite) | < 100 MB, ejecución por lotes | **Seleccionada**: proporcional al hardware, sin puertos expuestos, reproducible y auditable. |

## 2. Arquitectura implementada

- **Recolección:** `docker compose logs --timestamps` de `proxy` (Nginx), `api` (Flask/Gunicorn), `keycloak`, `db` e `identity-db` (PostgreSQL) y schedulers de backup; `local/backups/execution.log`; `evidencias/ids/eve.json` (Suricata).
- **Normalización:** marca de tiempo UTC, origen, categoría y resultado; hash SHA-256 por evento para deduplicar e indicar integridad.
- **Saneamiento:** redacción de `Authorization: Bearer`, `access/refresh/id_token`, `password`, `cookie`/`set-cookie` y cualquier JWT (`eyJ…`). Verificado en cada ejecución (`unredacted_secret_patterns = 0`).
- **Almacenamiento y búsqueda:** `evidencias/siem/eventos.db` (SQLite, índices por tiempo/origen/categoría).
- **Correlación:** `local/monitoring/rules.json` (6 reglas con umbral y ventana temporal).
- **Consulta:** CLI `scripts/siem_ligero.py search|alerts` y tablero HTML estático de sólo lectura (`tablero-siem-*.html`).
- **Retención/rotación:** logs Docker con `json-file` `max-size 10m` × `max-file 5` por servicio; SIEM con `retention --days 30` (sólo informa candidatos; borra únicamente con `--apply`).

## 3. Reglas de correlación

| Regla | Detecta | Umbral / ventana | Fuente real que la disparó |
|---|---|---|---|
| SIEM-AUTH-001 | Ráfaga de autenticaciones fallidas (`LOGIN_ERROR`, token inválido) | 3 / 300 s | keycloak-1, api-1 |
| SIEM-RBAC-001 | Acceso denegado por RBAC | 1 / 300 s | api-1 |
| SIEM-HTTP-001 | Ráfaga HTTP 401/403 | 5 / 120 s | proxy-1 |
| SIEM-DB-001 | Fallo de autenticación PostgreSQL | 1 / 300 s | db-1 |
| SIEM-IDS-001 | Alerta Suricata | 1 / 300 s | suricata |
| SIEM-BACKUP-001 | Fallo de respaldo/restauración | 1 / 300 s | backup-scheduler |

## 4. Pruebas ejecutadas

| Prueba | Método | Resultado | Evidencia |
|---|---|---|---|
| Detección sintética y redacción | 5 eventos sintéticos con JWT y contraseña ficticios en BD separada | Exitosa: AUTH, RBAC y BACKUP disparadas; secretos ausentes del archivo SQLite | `prueba-controlada-20261024-094553.json` |
| Fallo de autenticación PostgreSQL real | 2 conexiones con usuario sintético inexistente desde la red `datos` | Exitosa: 2 eventos `password authentication failed`, alerta SIEM-DB-001 | `consulta-db-auth-denied-20261024-095532.json` |
| Fallo de backup real | Respaldo de identidad dirigido a un host inexistente (no toca la base) | Exitosa: `result=failure` registrado, alerta SIEM-BACKUP-001 | `consulta-backup-failure-20261024-095532.json` |
| Autenticación/RBAC reales | `scripts/pruebas_identidad.py` (credenciales y TOTP inválidos, rol insuficiente) | Exitosa: 7 eventos auth denegados, 12 RBAC denegados | `consulta-auth-denied-*.json`, `consulta-rbac-denied-*.json` |
| Integración IDS | Ingesta de `eve.json` de 8 escenarios PCAP | Exitosa: SIEM-IDS-001 | `consulta-suricata-20261024-095532.json` |
| Ciclo integrado | `scripts/siem_pipeline.py`: 10 orígenes, 6 reglas disparadas, 5 esperadas con soporte en eventos reales | Exitosa | `pipeline-siem-20261024-095532.json`, `alertas-20261024-095532.json`, `tablero-siem-20261024-095532.html` |

Nota: durante la consolidación se registró además un fallo **real** de restauración (`target=restore-academic result=failure`, 15:56 UTC) causado por un defecto del script (PowerShell 5.1 convertía el progreso de Docker en stderr en excepción). La alerta lo detectó; el defecto se corrigió y la prueba posterior fue exitosa.

## 5. Consultas reproducibles

```powershell
python scripts/siem_pipeline.py                      # ciclo completo con verificación
python scripts/siem_ligero.py search --category database_authentication
python scripts/siem_ligero.py search --category backup --outcome failure
python scripts/siem_ligero.py alerts --rule SIEM-AUTH-001
python scripts/siem_ligero.py dashboard --output evidencias/siem/tablero.html
```

## 6. Capacidades faltantes frente a un SIEM empresarial

Recolección continua por agentes (hoy es por lotes); alta disponibilidad y almacenamiento inmutable/WORM; firma o encadenamiento criptográfico de lotes; UEBA y líneas base de comportamiento; inteligencia de amenazas; gestión de casos y SOAR; notificaciones activas (correo/chat); cobertura de endpoints, red física y nube; control de acceso por rol a la consola; parsers formales por fuente; retención y cumplimiento legal configurables por categoría. Por ello se clasifica como **monitoreo centralizado ligero**, no como SIEM empresarial (riesgo R-012).
