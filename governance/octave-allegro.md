# Evaluación OCTAVE Allegro — ejercicio de escritorio

Generado: 2026-11-07T13:09:47-06:00.

> **Naturaleza:** evaluación de escritorio realizada por el equipo del proyecto con base en el laboratorio y en supuestos del escenario. **No se realizaron entrevistas ni talleres**, por lo que no hay resultados de participantes. Una evaluación organizacional real requiere talleres con Registro, Dirección Académica, Finanzas, Legal, RRHH y TI, y validación de los propietarios.

## Variante metodológica

Se seleccionó **OCTAVE Allegro** (SEI/CERT, 2007) porque se centra en activos de información y sus contenedores, puede ejecutarse con un equipo reducido y no requiere el inventario exhaustivo de OCTAVE original ni la escala de OCTAVE-S. Se aplican sus ocho pasos y sus hojas de trabajo de forma resumida.

## Paso 1 — Criterios de medición del riesgo

Áreas de impacto priorizadas (supuesto académico; 6 = más importante). Cada escenario recibe Alto = 3, Medio = 2 o Bajo = 1 por área; puntaje relativo = Σ(valor × prioridad), mínimo 21 y máximo 63. Pools: 1 ≥ 50; 2 = 40–49; 3 < 40.

| area_impacto | prioridad |
|---|---|
| Académico | 6 |
| Reputación y confianza | 5 |
| Legal/regulatorio | 4 |
| Financiero | 3 |
| Productividad/operación | 2 |
| Seguridad y salud | 1 |

Las definiciones de Alto/Medio/Bajo se alinean con las escalas del BIA (`bia.md`): Alto ≈ 4–5, Medio ≈ 3, Bajo ≈ 1–2.

## Pasos 2 y 3 — Perfiles de activos críticos y contenedores

| id | activo | contenedores_tecnicos | contenedores_personas | propietario | C | I | A | requisito_principal |
|---|---|---|---|---|---|---|---|---|
| IA-01 | Expedientes y gestión académica | ACT-003; ACT-005; ACT-010 | Registro Académico, docentes | Dirección Académica | Sólo personal con rol docente/administrativo | Calificaciones sólo modificables por rol autorizado | RTO 8 h (PROC-002) | Integridad |
| IA-02 | Identidades, credenciales y roles | ACT-006; ACT-007; ACT-011; ACT-013 | Administradores IAM | Seguridad TI | Hashes y secretos nunca expuestos | Roles alterados sólo con MFA y registro | RTO 2 h (PROC-004) | Confidencialidad |
| IA-03 | Copias de respaldo | ACT-010; ACT-011; ACT-016 | DBA/Continuidad | TI UVCG | Cifradas con clave separada | SHA-256 verificado antes de restaurar | Disponibles fuera del host (pendiente) | Disponibilidad |
| IA-04 | Registros y alertas de seguridad | ACT-008; ACT-009; ACT-014 | Analista de seguridad | Seguridad TI | Sin secretos ni datos personales | Eventos con hash y deduplicación | Retención 30 días | Integridad |
| IA-05 | Información financiera y de pagos (escenario) | ACT-020; ACT-006 | Finanzas, proveedor bancario | Dirección Financiera | Datos de pago protegidos | Conciliación exacta | RTO 8 h (PROC-005) | Integridad |

## Paso 4 — Áreas de preocupación

Acceso indebido a expedientes; toma de cuentas; vulnerabilidades de imágenes; pérdida o inutilización de copias; robo de la clave de cifrado; detección insuficiente; pérdida del único host; dependencia de terceros sin contrato evaluado.

## Pasos 5 a 7 — Escenarios de amenaza, consecuencias y análisis

| escenario | activo_info | actor | medio | resultado | probabilidad_subjetiva | Académico | Reputación y confianza | Legal/regulatorio | Financiero | Productividad/operación | Seguridad y salud | puntaje_relativo | pool | enfoque | riesgos_vinculados |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OS-03 | IA-02 | Atacante externo | Explotación de vulnerabilidad en imagen | Interrupción/divulgación | Media | 3 | 3 | 3 | 2 | 3 | 1 | 58 | Pool 1 (≥ 50) | Mitigar | R-009; R-010 |
| OS-04 | IA-03 | Fallo técnico o ransomware | Corrupción/borrado de copias en el mismo host | Destrucción | Media | 3 | 3 | 2 | 3 | 3 | 1 | 57 | Pool 1 (≥ 50) | Mitigar | R-007; R-011; R-019 |
| OS-07 | IA-01 | Evento físico/ambiental | Pérdida del único host | Interrupción | Media | 3 | 3 | 2 | 3 | 3 | 1 | 57 | Pool 1 (≥ 50) | Mitigar | R-004; R-014 |
| OS-02 | IA-02 | Atacante externo | Credential stuffing contra Keycloak | Divulgación | Alta | 2 | 3 | 3 | 2 | 3 | 1 | 52 | Pool 1 (≥ 50) | Mitigar | R-002 |
| OS-01 | IA-01 | Usuario interno con token válido | Abuso de rol/API | Modificación | Media | 3 | 2 | 3 | 1 | 2 | 1 | 48 | Pool 2 (40–49) | Mitigar | R-001 |
| OS-05 | IA-03 | Insider/robo de equipo | Obtención de la clave de cifrado | Divulgación | Baja | 2 | 3 | 3 | 2 | 1 | 1 | 48 | Pool 2 (40–49) | Mitigar | R-015 |
| OS-08 | IA-05 | Proveedor externo | Falla o brecha del tercero | Divulgación/interrupción | Media | 1 | 3 | 3 | 3 | 2 | 1 | 47 | Pool 2 (40–49) | Transferir | R-018 |
| OS-06 | IA-04 | Atacante que evade detección | Ausencia de agentes y HA | Interrupción de la detección | Media | 2 | 2 | 2 | 1 | 2 | 1 | 38 | Pool 3 (< 40) | Diferir/mitigar | R-012 |

## Paso 8 — Enfoque de mitigación

- **Pool 1 (mitigar de inmediato):** OS-03, OS-04, OS-07, OS-02.
- **Pool 2 (mitigar o diferir con justificación):** OS-01, OS-05, OS-08.
- **Pool 3 (diferir/aceptar con seguimiento):** OS-06.

Las acciones concretas están en `plan-tratamiento.md` mediante los riesgos vinculados.

## Resultados

Los escenarios de mayor puntaje se concentran en la credencial/identidad (IA-02), las copias de respaldo en el mismo host (IA-03) y la pérdida del host (IA-01). Esto coincide con los riesgos críticos residuales de `matriz-riesgos.md` (R-011, R-013) y con la brecha de RPO medida (R-019). Fortalezas comprobadas en laboratorio: MFA/RBAC, segmentación, TLS, backups cifrados de ambas bases, restauración aislada periódica, correlación SIEM e IDS offline.

## Recomendaciones

1. Validar en talleres las prioridades del Paso 1 y los requisitos del Paso 2.
2. Aprobar repositorio offsite/inmutable y WAL/PITR (OS-04, R-011, R-019).
3. Mantener el reescaneo mensual de la imagen PostgreSQL sin gosu ya aplicada (OS-03, R-009).
4. Definir MDM/EDR y SIEM institucional con presupuesto (OS-06, R-012, R-013).
5. Repetir la evaluación anualmente y tras cambios mayores.
