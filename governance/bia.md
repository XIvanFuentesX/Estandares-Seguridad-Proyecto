# Business Impact Analysis — UVCG

Generado: 2026-11-07T11:23:29-06:00. **Supuestos académicos pendientes de validación y aprobación por responsables institucionales; no provienen de entrevistas ni de datos financieros reales.**

## Escalas de impacto (1–5)

Umbrales financieros en quetzales, propuestos para una universidad privada de ~3,000 estudiantes.

| nivel | operativo | financiero | academico | reputacional | legal |
|---|---|---|---|---|---|
| 1 | Sin efecto perceptible | < Q10,000 | Sin efecto en actividades | Sin difusión | Sin incumplimiento |
| 2 | Demora menor con alternativa | Q10,000–50,000 | Reprogramación menor | Quejas aisladas | Incumplimiento interno menor |
| 3 | Proceso degradado < 1 día | Q50,000–250,000 | Afecta a un grupo de cursos | Difusión local | Observación de ente regulador o contractual |
| 4 | Proceso detenido en periodo normal | Q250,000–1,000,000 | Afecta a una facultad o evaluación | Medios regionales/redes | Sanción o reclamo formal probable |
| 5 | Proceso detenido en periodo crítico | > Q1,000,000 | Afecta a toda la población estudiantil | Cobertura nacional/pérdida de confianza | Sanción grave o exposición de datos personales |

## Reglas de coherencia verificadas automáticamente

- RPO ≤ RTO < MTPD, y RTO ≤ 50 % del MTPD (margen para detección, decisión y comunicación).
- Criticidad: **Crítica** si dos o más dimensiones valen 5; **Alta** si el máximo es 4 o una sola dimensión vale 5; **Media** si el máximo es 3; **Baja** en otro caso.
- Todos los activos referenciados existen en `inventario-activos.csv`.

## Evidencia técnica del laboratorio (no son objetivos institucionales)

Última medición: recuperación de la API en 11.98 s; recuperación de Keycloak en 70.242 s; restauración aislada academic en 8.33 s; restauración aislada identity en 8.965 s. Estos tiempos corresponden a bases pequeñas y a un solo host; no incluyen detección, decisión, comunicación ni validación funcional, por lo que no se extrapolan al RTO universitario.

## Matriz BIA

| id | proceso | responsable | descripcion | dependencias_tecnologicas | activos | impacto_operativo_1_5 | impacto_financiero_1_5 | impacto_academico_1_5 | impacto_reputacional_1_5 | impacto_legal_1_5 | rto_horas | rpo_horas | mtpd_horas | criticidad | justificacion | estado_datos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PROC-001 | Inscripción y matrícula | Registro Académico | Alta y modificación de matrícula estudiantil | Identidad; portal; base académica; pagos | ACT-005; ACT-006; ACT-020 | 5 | 4 | 5 | 5 | 4 | 4 | 1 | 12 | Crítica | La indisponibilidad en ventanas de inscripción detiene el ingreso académico y puede afectar ingresos. | Supuestos académicos pendientes de validación y aprobación por responsables institucionales; no provienen de entrevistas ni de datos financieros reales. |
| PROC-002 | Gestión académica | Dirección Académica | Cursos, calificaciones, expedientes y programación | API; base académica; identidad | ACT-003; ACT-005; ACT-006 | 5 | 3 | 5 | 4 | 5 | 8 | 4 | 24 | Crítica | La integridad de expedientes es esencial y existen obligaciones de conservación/privacidad. | Supuestos académicos pendientes de validación y aprobación por responsables institucionales; no provienen de entrevistas ni de datos financieros reales. |
| PROC-003 | Aprendizaje virtual | Dirección Académica | Entrega de contenido, tareas, evaluación y clases | LMS; identidad; comunicaciones; Internet | ACT-006; ACT-019; ACT-021 | 5 | 3 | 5 | 4 | 3 | 4 | 1 | 12 | Crítica | Una interrupción durante evaluaciones afecta directamente continuidad docente. | Supuestos académicos pendientes de validación y aprobación por responsables institucionales; no provienen de entrevistas ni de datos financieros reales. |
| PROC-004 | Identidad y autenticación | Seguridad TI | Autenticación, MFA, sesiones y roles | Keycloak; DB identidad; TLS; DNS/tiempo | ACT-006; ACT-007; ACT-013 | 5 | 4 | 5 | 5 | 5 | 2 | 0.25 | 4 | Crítica | Es dependencia transversal; su caída bloquea múltiples procesos. | Supuestos académicos pendientes de validación y aprobación por responsables institucionales; no provienen de entrevistas ni de datos financieros reales. |
| PROC-005 | Gestión financiera y pagos | Dirección Financiera | Cobros, conciliación y obligaciones financieras | Sistema financiero; identidad; banca | ACT-006; ACT-020 | 4 | 5 | 3 | 5 | 5 | 8 | 1 | 24 | Crítica | Errores o indisponibilidad afectan ingresos, conciliación y obligaciones regulatorias. | Supuestos académicos pendientes de validación y aprobación por responsables institucionales; no provienen de entrevistas ni de datos financieros reales. |
| PROC-006 | Servicios administrativos | Administración | RRHH, compras, expedientes y soporte administrativo | Identidad; sistemas administrativos; correo | ACT-006; ACT-021 | 3 | 3 | 3 | 3 | 4 | 24 | 8 | 72 | Alta | Tolera mayor demora fuera de cierres, pero maneja información confidencial. | Supuestos académicos pendientes de validación y aprobación por responsables institucionales; no provienen de entrevistas ni de datos financieros reales. |
| PROC-007 | Correo y comunicaciones | Comunicación Institucional | Avisos, coordinación y comunicaciones de emergencia | Correo; identidad; DNS; Internet | ACT-006; ACT-021 | 4 | 3 | 4 | 5 | 3 | 8 | 4 | 24 | Alta | Es canal operativo y de crisis; existen alternativas temporales limitadas. | Supuestos académicos pendientes de validación y aprobación por responsables institucionales; no provienen de entrevistas ni de datos financieros reales. |