# Plan de Continuidad del Negocio (BCP) — borrador UVCG

Generado: 2026-11-07T13:09:47-06:00. Objetivos, roles y estrategias son **supuestos académicos pendientes de aprobación**. Se basa en `bia.md`; el detalle técnico de recuperación está en `drp.md`.

## 1. Alcance y objetivos

Procesos PROC-001 a PROC-007 del BIA. Objetivo: mantener los procesos críticos dentro de su MTPD y recuperarlos dentro del RTO/RPO propuestos.

## 2. Priorización de servicios

| orden | proceso | criticidad | RTO_h | RPO_h | MTPD_h |
|---|---|---|---|---|---|
| 1 | PROC-004 Identidad y autenticación | Crítica | 2 | 0.25 | 4 |
| 2 | PROC-001 Inscripción y matrícula | Crítica | 4 | 1 | 12 |
| 3 | PROC-003 Aprendizaje virtual | Crítica | 4 | 1 | 12 |
| 4 | PROC-002 Gestión académica | Crítica | 8 | 4 | 24 |
| 5 | PROC-005 Gestión financiera y pagos | Crítica | 8 | 1 | 24 |
| 6 | PROC-007 Correo y comunicaciones | Alta | 8 | 4 | 24 |
| 7 | PROC-006 Servicios administrativos | Alta | 24 | 8 | 72 |

Identidad (PROC-004) se recupera primero porque todos los demás procesos dependen de ella.

## 3. Criterios de activación

| Nivel | Condición | Decide |
|---|---|---|
| Alerta | Alerta SIEM alta/crítica, fallo de backup o servicio degradado sin impacto confirmado | Líder TI |
| Activación parcial | Indisponibilidad de un proceso crítico > 50 % de su RTO o corrupción confirmada de datos | Coordinador de Continuidad |
| Activación total | Pérdida del host/sitio, compromiso de identidad, o proyección de superar el MTPD de cualquier proceso crítico | Director de crisis |

## 4. Roles y responsabilidades (RACI resumido)

| Actividad | Director de crisis | Coordinador de Continuidad | Líder TI | Seguridad | Propietario de proceso | Comunicaciones | Legal/privacidad |
|---|---|---|---|---|---|---|---|
| Activar el plan | A | R | C | C | I | I | I |
| Recuperación técnica (DRP) | I | A | R | C | I | – | – |
| Contención y evidencia | I | I | C | R/A | I | – | C |
| Validación funcional | I | A | C | – | R | – | – |
| Comunicación interna/externa | A | C | – | C | C | R | C |
| Notificación de brecha de datos | A | I | – | C | I | C | R |

Los nombramientos reales están pendientes.

## 5. Estrategias de continuidad por proceso

| Proceso | Estrategia técnica | Alternativa manual temporal (definir con propietario) |
|---|---|---|
| PROC-004 Identidad | Backup cifrado + restauración aislada probada; reinicio controlado medido | Ninguna segura sin IAM; priorizar recuperación |
| PROC-001 Inscripción | Recuperar IAM + BD académica + API | Recepción de solicitudes en formulario controlado y carga posterior |
| PROC-003 Aprendizaje virtual | Depende de proveedor LMS (escenario) | Publicación de materiales por correo institucional |
| PROC-002 Gestión académica | Backup/restore de BD académica | Congelar cambios de calificaciones hasta restaurar |
| PROC-005 Finanzas | Proveedor/banca (escenario) | Registro manual de pagos con conciliación posterior |
| PROC-007 Comunicaciones | Proveedor de correo (escenario) | Canales alternos aprobados (sitio web, mensajería oficial) |
| PROC-006 Administrativos | Restauración ordinaria | Diferir trámites no urgentes |

Brechas estratégicas abiertas: sin copia offsite/inmutable ni sitio alterno (R-011, R-014) y RPO no alcanzable con backup diario (R-019).

## 6. Procedimiento de respuesta

1. Detectar (SIEM/IDS/usuarios) y registrar hora de inicio.
2. Evaluar impacto contra el BIA y decidir el nivel de activación.
3. Contener (Seguridad) y preservar evidencia antes de cambios.
4. Ejecutar el DRP en el orden de dependencias.
5. Activar alternativas manuales cuando la recuperación supere el 50 % del RTO.
6. Comunicar sólo hechos confirmados, a intervalos definidos.

## 7. Pruebas y resultados observados

Tiempos medidos en el laboratorio (último registro), comparados con el RTO/RPO académico propuesto. **Sólo cubren la recuperación técnica** de bases pequeñas en un host; no incluyen detección, decisión, comunicación ni validación funcional.

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

Programa: semanal automatizado (tarea `SGSI-UVCG-Prueba-Recuperacion`, `scripts/prueba_recuperacion_periodica.ps1`), mensual (salud y hashes), semestral (interrupción controlada API/IAM con `scripts/prueba_continuidad.ps1`), anual (ejercicio de mesa con todos los roles y, cuando exista, pérdida de sitio).

## 8. Retorno a la normalidad

1. Confirmar integridad (conteos, hashes, pruebas RBAC/MFA) y ausencia de amenaza activa.
2. Aceptación formal del propietario de cada proceso.
3. Sincronizar transacciones registradas manualmente y conciliar.
4. Desactivar alternativas manuales y comunicar la normalización.
5. Reforzar monitoreo 72 h y ejecutar backup completo inmediato.
6. Lecciones aprendidas en 10 días hábiles; actualizar BIA, riesgos y este plan.
