# Estado del proyecto SGSI — UVCG

Última actualización: 2026-10-24 12:30 (cierre local, preparación Azure y preparación AWS Free).

Documentos de cierre: [`CIERRE_LABORATORIO_LOCAL.md`](CIERRE_LABORATORIO_LOCAL.md) (matriz de 44 requisitos, porcentajes y autorizaciones), [`CIERRE_AZURE.md`](CIERRE_AZURE.md) (Terraform, costos, criterios), [`CIERRE_AWS.md`](CIERRE_AWS.md) (despliegue mínimo AWS Free) y [`MANUAL_EJECUCION.md`](MANUAL_EJECUCION.md).

## 1. Avance

| Indicador | Valor | Base del cálculo |
|---|---:|---|
| Laboratorio práctico (10 módulos) | **82.5 %** (antes 78 %) | Tabla por módulo en `CIERRE_LABORATORIO_LOCAL.md` §6 |
| Ejecución local de requisitos locales | **≈ 71 %** | (25 implementados + 7 parciales × 0.5) / 40 |
| Práctica total (académico) | **≈ 69 %** (antes ≈ 65 %) | 50 % laboratorio + 30 % gobierno documental (≈ 85 %) + 20 % validación institucional/Azure/auditoría (≈ 12 %) |
| Azure | **Preparado, no desplegado** | IaC modular validada; 0 recursos reales; 5/10 criterios del encargo sin cumplir por falta de suscripción |
| AWS (plan Free) | **Preparado, no desplegado** | No había AWS CLI ni sesión para verificar el plan Free; Terraform mínimo validado (S3 + IAM + presupuesto); gasto 0.00 USD |
| Componente cloud real | **0 %** | Ninguna nube desplegada todavía: el requisito de nube híbrida sigue pendiente |

No se declara el 100 %: faltan el despliegue híbrido, la copia offsite, el MDM/EDR reales, el IDS en vivo, el WAL en las bases principales y las aprobaciones institucionales.

## 2. Novedades de esta fase

- **WAL/PITR:** validado en réplicas aisladas de ambas bases (recuperación exacta al punto objetivo; RPO observado ≈ 56 s; RTO técnico ≈ 3 s; fallo de archivado detectado). Preparado sin aplicar para las principales (`local/compose.pitr.yaml`).
- **SIEM:** sellado encadenado de eventos, 11 reglas (WAL, configuración, disponibilidad, contenedores, DLP), consultas por fecha y monitor de disponibilidad continuo (15 s).
- **Vigilancia de contenedores:** procesos, deriva y endurecimiento; proceso no autorizado detectado y escritura bloqueada.
- **DLP:** compuerta de transferencia con bloqueo e incidentes. **MDM:** sólo simulación con dispositivos ficticios.
- **Registros operativos:** 6 cambios, 12 incidentes (6 de ejercicio DLP), 2 solicitudes de acceso y 4 eventos de activos, con auditoría encadenada.
- **Respaldo heredado sin cifrar:** cifrado y verificado; el original se conserva.
- **Gobernanza:** 33 activos, 22 riesgos, SoA 30/38/25, COBIT/ITIL/TIA-942 y políticas propuestas; trazabilidad 21/21.
- **Azure:** 8 módulos Terraform; `validate`, 20/20 pruebas simuladas, TFLint 0, Trivy revisado; costos con la API oficial (16.90 / 73.88 / 2,962.96 USD/mes en eastus2).

## 3. Validación

Última corrida completa (`evidencias/automatizacion/validacion-sgsi-20261024-112033.json`): 27 exitosas, 1 fallida (`AZURE-STATIC`, coincidió con la reestructuración de `azure/`; reejecutada aparte: 32 OK) y 1 no verificable (`PITR-PRINCIPALES`). Una corrida completa posterior fue detenida por el sistema por falta de memoria (INC-012) y **no** se cuenta como exitosa.

## 4. Hallazgos pendientes

- Bases principales sin archivado WAL (R-019); copias y claves en un solo host, sin offsite (R-011, R-015); ACL amplia de `.env` (INC-010).
- Keycloak 2 HIGH OpenJDK sin corrección publicada (R-010).
- Sin MDM/EDR reales (R-013), IDS en vivo, NGFW ni alta disponibilidad.
- La ingesta de logs Docker del SIEM es por lotes.
- Supuestos de BIA, riesgos y OCTAVE sin validación institucional; sin capturas de pantalla (pendiente documental).

## 5. Decisiones que requieren autorización

1. Activar WAL/PITR en las bases principales (recrea `db` e `identity-db`).
2. Restringir la ACL de `local/.env`.
3. Eliminar la copia heredada sin cifrar (ya existe la versión cifrada).
4. Borrado real por retención y limpieza de las bases restauradas acumuladas.
5. Tarea programada del ciclo SIEM cada 15 min.
6. IDS en vivo (NET_RAW/NET_ADMIN).
7. Suscripción, presupuesto y despliegue de Azure (pasos en `CIERRE_AZURE.md` §11).
8. AWS: instalar AWS CLI ≥ 2.32, `aws login` y verificación FREE/ACTIVE; el despliegue mínimo ya está autorizado si la verificación confirma cero cargos (pasos en `CIERRE_AWS.md` §5).
