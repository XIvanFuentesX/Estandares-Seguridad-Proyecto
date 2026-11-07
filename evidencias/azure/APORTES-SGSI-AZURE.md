# Aportes al SGSI (filas propuestas para integrar en `governance/`)

Filas **propuestas**; no se modificó `governance/`. Los ID de activo comienzan en ACT-030 para no chocar con los existentes
(hasta ACT-024 a la fecha); ajústelos al integrar. Estado de todos: *Preparado (no desplegado)*.

## 1. Inventario de activos (formato de `inventario-activos.csv`)

| id | activo | tipo | propietario | custodio | ubicacion | informacion_procesada | C | I | D | criticidad | dependencias | estado_real |
|---|---|---|---|---|---|---|---:|---:|---:|---|---|---|
| ACT-030 | Suscripción y grupo de recursos Azure del SGSI | Servicio cloud | Dirección TI | Operador de plataforma | Azure eastus2 | Recursos del laboratorio híbrido | 3 | 4 | 3 | Alta | Contrato Azure; Entra ID | Preparado (no desplegado) |
| ACT-031 | Red hub-and-spoke y NSG Azure | Red | Seguridad TI | Operador de plataforma | Azure eastus2 | Flujos DMZ/apps/datos/PE | 3 | 5 | 4 | Alta | ACT-030; ACT-015 | Preparado (no desplegado) |
| ACT-032 | Key Vault del SGSI | Seguridad/criptografía | Seguridad TI | Administrador de seguridad | Azure (PE) | Secretos y certificados | 5 | 5 | 4 | Crítica | ACT-030; ACT-031 | Preparado (no desplegado) |
| ACT-033 | Cuenta de almacenamiento privada (evidencias e intercambio) | Información/almacenamiento | Responsable SGSI | Operador de plataforma | Azure (PE) | Evidencias y copias cifradas ficticias | 4 | 5 | 3 | Alta | ACT-031; ACT-032; ACT-011 | Preparado (no desplegado) |
| ACT-034 | Log Analytics / Sentinel | Monitoreo | Seguridad TI | Analista de seguridad | Azure eastus2 | Registros de actividad y diagnósticos | 4 | 5 | 3 | Alta | ACT-030 | Preparado (no desplegado) |
| ACT-035 | Recovery Services Vault | Respaldo | TI UVCG | Operador de respaldo | Azure eastus2 | Copias de servidores locales | 5 | 5 | 4 | Alta | ACT-030; ACT-001 | Preparado (no desplegado) |
| ACT-036 | Conectividad híbrida (VPN S2S / Azure Arc) | Red/servicio | Redes | Operador de redes | Azure + laboratorio | Tráfico cifrado local↔Azure | 4 | 5 | 3 | Alta | ACT-001; ACT-031 | Preparado (no desplegado) |
| ACT-037 | Código IaC y estado de Terraform | Software/configuración | DevSecOps | Operador de plataforma | Repositorio + backend Storage | Definición de infraestructura; estado sensible | 4 | 5 | 3 | Alta | ACT-030 | Código validado; estado inexistente |
| ACT-038 | Políticas de Azure y presupuesto | Gobierno | Responsable SGSI | Finanzas/SGSI | Azure | Reglas de cumplimiento y alertas de gasto | 2 | 4 | 2 | Media | ACT-030 | Preparado (no desplegado) |

## 2. Riesgos (resumen para `matriz-riesgos.csv`; detalle en `RIESGOS-CLOUD.md`)

| id | proceso | activo | amenaza | riesgo_inherente | nivel | controles | riesgo_residual | nivel_residual | responsable |
|---|---|---|---|---:|---|---|---:|---|---|
| RC-01 | Todos | ACT-030; ACT-038 | Gasto no controlado | 16 | Crítico | Banderas false, presupuesto, revisión de plan | 6 | Moderado | Responsable SGSI |
| RC-02 | Todos | ACT-032; ACT-033 | Exposición pública por mala configuración | 15 | Alto | PE, políticas Deny, NSG Deny 4096, Trivy | 5 | Bajo | Cloud/DevSecOps |
| RC-03 | PROC-004 | ACT-030 | Compromiso de cuenta administrativa | 15 | Alto | MFA, alertas RBAC | 10 | Moderado | IAM |
| RC-05 | Todos | ACT-037 | Exposición del estado de Terraform | 12 | Alto | Backend Entra ID, `.gitignore` | 8 | Moderado | Plataforma |
| RC-14 | Todos | ACT-001; ACT-036 | Exposición de Docker por la integración híbrida | 10 | Moderado | Arc saliente, VPN sólo a PE | 5 | Bajo | Redes |
| RC-15 | PROC-004 | ACT-030 | Falta de licencias P1/P2/Intune | 12 | Alto | Security defaults, MFA Keycloak | 9 | Moderado | Dirección TI |

Relación con riesgos existentes: RC-01/RC-02 desglosan **R-017**; ACT-033/ACT-035 tratan **R-011** y **R-014** (copia
fuera del sitio) cuando se desplieguen; RC-03/RC-04 complementan **R-016**.

## 3. Plan de tratamiento (formato de `plan-tratamiento.csv`)

| riesgo_id | estrategia | control_propuesto | referencia_iso_27001_27002_2022 | responsable | prioridad | plazo | estado | evidencia | residual_esperado |
|---|---|---|---|---|---|---|---|---|---|
| R-011 | Mitigar | Copia cifrada fuera del sitio en Storage privado/RSV (Escenario 2) | A.8.13; A.8.14; A.5.30 | Continuidad | Alta | Tras autorización | Preparado | `azure/modules/storage`, `backup` | 8 Moderado |
| R-017 | Mitigar | Validación IaC + pruebas mock + políticas Deny + presupuesto | A.5.23; A.8.9; A.8.32 | Cloud/DevSecOps | Alta | Hecho (estático) | Implementado estático | `validacion-terraform-20261024.txt` | 8 Moderado |
| RC-01 | Mitigar | Revisión de plan con `revisar_plan.py` y aprobación previa | A.8.32; A.5.1 | Responsable SGSI | Alta | Antes de cada apply | Preparado | `azure/scripts/revisar_plan.py` | 6 Moderado |
| RC-05 | Mitigar | Backend Storage con Entra ID, sin claves, versionado y bloqueo | A.8.4; A.8.9 | Plataforma | Alta | Paso 6 del despliegue | Documentado | `azure/backend.tf` | 6 Moderado |
| RC-15 | Transferir/Aceptar | Adquirir Entra ID P1 (CA) y P2 (PIM) o validar inclusión en licencia académica | A.5.15; A.8.2; A.8.5 | Dirección TI | Media | Presupuesto 2027 | Pendiente | `ANALISIS-COSTOS-AZURE.md` §4 | 6 Moderado |

## 4. Declaración de aplicabilidad (actualizaciones sugeridas a `declaracion-aplicabilidad.csv`)

| control_id | control_name | applicable | justificación | implementation_status | related_risks | evidence |
|---|---|---|---|---|---|---|
| A.5.23 | Information security for use of cloud services | Sí | Uso planificado de Azure con políticas, región restringida y presupuesto | Preparado (IaC validada, no desplegado) | R-017; RC-01; RC-02; RC-11 | `azure/`; `evidencias/azure/` |
| A.8.9 | Configuration management | Sí | Configuración como código con validación y pruebas | Implementado estático | RC-10 | `validacion-terraform-20261024.txt` |
| A.8.20 / A.8.22 | Networks security / Segregation of networks | Sí | Hub-spoke, NSG, UDR | Local implementado; Azure preparado | R-009; RC-02 | `azure/modules/networking` |
| A.8.24 | Use of cryptography | Sí | TLS 1.2, IPsec AES-256, cifrado en reposo, Key Vault | Local implementado; Azure preparado | R-015; RC-06 | `azure/modules/security`, `hybrid-connectivity` |
| A.8.13 | Information backup | Sí | Copia fuera del sitio en Azure | Local implementado; Azure preparado | R-011 | `azure/modules/backup`, `storage` |
| A.8.15 / A.8.16 | Logging / Monitoring activities | Sí | LAW, registro de actividad, alertas | Local implementado (SIEM ligero); Azure preparado | R-012; RC-08 | `azure/modules/monitoring` |
| A.5.3 / A.8.2 | Segregation of duties / Privileged access rights | Sí | Roles por grupo con validación SoD; PIM pendiente de licencia | Preparado | RC-04; RC-15 | `azure/modules/identity` |
| A.7.x | Controles físicos en Azure | No (para Azure) | Responsabilidad del proveedor (modelo compartido) | No aplica | — | `MATRIZ-CONTROLES-AZURE.md` §2 |

## 5. BIA / BCP / DRP (filas sugeridas)

| Documento | Proceso / escenario | Aporte Azure | RTO/RPO afectado | Condición |
|---|---|---|---|---|
| BIA | PROC-002 (gestión académica) | Copia offsite de la base académica (ficticia) en Storage/RSV | RPO local 24 h → sin cambio hasta WAL/PITR; protege contra pérdida del sitio | Requiere Escenario 2 desplegado |
| BIA | PROC-004 (identidad) | Copia offsite de la base de Keycloak cifrada | Igual | idem |
| BCP | Pérdida del host (R-011/R-014) | Estrategia 8.3: recuperar desde Azure en un equipo alterno | RTO estimado no medido | Probar con PT-AZ-20/22 |
| DRP | Restauración desde nube | Procedimiento: descargar `.dump.enc` (identidad Arc) → verificar SHA-256 → restaurar en entorno aislado | Medir en PT-AZ-22 | Sin suscripción no ejecutable |
| DRP | Desastre regional Azure | GRS/RSV geo-redundante sólo en escenario institucional | — | Escenario 3 |
