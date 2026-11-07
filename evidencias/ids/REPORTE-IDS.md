# Reporte del Módulo B — IDS y protección de infraestructura

Fecha: 2026-10-24. Motor: Suricata 7.0 (`jasonish/suricata:7.0`), perfil Docker `ids`, `network_mode: none`, usuario no root, `cap_drop: ALL`, raíz de sólo lectura.

## 1. Modalidad implementada

**IDS offline sobre PCAP sintético autorizado** (`local/ids/pcap/trafico-controlado.pcap`, generado por `scripts/generar_pcap_ids.py`). El tráfico nunca se transmite por la red ni se dirige a servicios externos. No es IPS (no bloquea), ni EDR/XDR (no observa endpoints).

## 2. Reglas documentadas (`local/ids/rules/uvcg.rules`)

| SID | Detecta | Lógica | Riesgo vinculado |
|---|---|---|---|
| 1000001 | Path traversal | `../` en URI sin normalizar | R-001, R-003 |
| 1000002 | Conexión directa a PostgreSQL | SYN a 5432 (las bases no deben ser alcanzables desde DMZ) | R-009 |
| 1000003 | Inyección SQL | `union` … `select` en URI normalizada | R-001, R-003 |
| 1000004 | Herramienta de escaneo | User-Agent `sqlmap`/`nikto`/`nmap` | R-001 |
| 1000005 | Acceso a consola admin Keycloak | URI inicia con `/auth/admin/` | R-016 |
| 1000006 | Puerto de gestión Keycloak | SYN a 9000 | R-010, R-016 |
| 1000007 | Ráfaga de login | ≥ 6 POST a `/login-actions/authenticate` por origen en 60 s (`detection_filter`) | R-002 |

## 3. Pruebas controladas

| Escenario | Esperado | Observado | Resultado |
|---|---|---|---|
| IDS-T01 Path traversal | sid 1000001 | 1 alerta | Exitoso |
| IDS-T02 SYN a PostgreSQL | sid 1000002 | 1 alerta | Exitoso |
| IDS-T03 UNION SELECT | sid 1000003 | 1 alerta | Exitoso |
| IDS-T04 User-Agent sqlmap | sid 1000004 | 1 alerta | Exitoso |
| IDS-T05 Consola admin | sid 1000005 | 1 alerta | Exitoso |
| IDS-T06 SYN puerto 9000 | sid 1000006 | 1 alerta | Exitoso |
| IDS-T07 6 POST de login | sid 1000007 | 1 alerta (al superar el umbral) | Exitoso |
| IDS-N01 GET /health benigno | 0 alertas | 0 alertas | Exitoso (sin falso positivo) |

Totales: 7 verdaderos positivos, 0 falsos positivos en el escenario benigno. Evidencia: `resultado.json`, `escenarios-pcap.json`, `fast.log`, `eve.json`. Las salidas de ejecuciones anteriores se archivan en `historico/` porque Suricata agrega a `eve.json`.

Advertencia conocida del motor: la regla 1000006 (SYN sin dirección explícita) se deshabilita para el sentido `toclient`; no afecta la detección `toserver` validada.

## 4. Integración con el monitoreo

`scripts/siem_pipeline.py` ingiere `eve.json` (sólo campos de firma, severidad, protocolo y puerto; sin payload) y la regla SIEM-IDS-001 genera la alerta correlacionada (`../siem/consulta-suricata-20261024-095532.json`).

## 5. Validación de segmentación y restricciones de red

`scripts/validar_segmentacion.ps1`: sólo Nginx publica puertos (127.0.0.1:8080/8443); la API resuelve `db`; el proxy **no** resuelve `db`; la base **no** resuelve el proxy; redes `apps`, `datos`, `identity` y `recovery` son `internal: true`. Evidencia: `../network/segmentacion-20261024-093648.json`. Limitación: valida aislamiento DNS/redes Docker, no un firewall físico.

## 6. Viabilidad de captura en tiempo real en Docker Desktop (Windows)

- Docker Desktop ejecuta los contenedores dentro de una VM WSL2; `network_mode: host` muestra la red **de esa VM**, no las interfaces físicas de Windows. No hay visibilidad del tráfico del host Windows ni de la LAN.
- El tráfico cliente → Nginx es HTTPS: un IDS en red sólo vería metadatos TLS, no URIs. El tráfico Nginx → API/Keycloak (red `apps`) sí es HTTP en claro.
- **Opción técnicamente viable:** un contenedor Suricata que comparta el espacio de red del proxy (`network_mode: service:proxy`) con capacidades `NET_RAW` y `NET_ADMIN` para AF_PACKET, inspeccionando la interfaz `apps`. Requiere **elevar privilegios del contenedor**, por lo que no se implementó sin autorización.
- Sin esa autorización se conserva la modalidad offline, que es funcional y reproducible.

## 7. Procedimiento de investigación

Ver `policies/procedimiento-investigacion-incidentes.md`. Guía rápida por firma:

| SID | Primera verificación | Contención sugerida |
|---|---|---|
| 1000001/1000003/1000004 | Buscar en SIEM las respuestas 4xx/5xx del mismo origen y ventana | Bloquear origen en Nginx; revisar validación de entradas |
| 1000002/1000006 | Confirmar origen: ¿contenedor fuera de su red permitida? | Revisar `compose.yaml`/redes; aislar contenedor |
| 1000005 | Correlacionar con eventos admin de Keycloak | Restringir ruta admin a red de gestión |
| 1000007 | Correlacionar con SIEM-AUTH-001 y bloqueos Keycloak | Bloqueo temporal de cuenta/origen; verificar MFA |

## 8. Lo que **no** está implementado

IPS en línea, EDR/XDR, captura en vivo, reglas de comunidad (ET Open) actualizadas automáticamente, ni correlación con inteligencia de amenazas.
