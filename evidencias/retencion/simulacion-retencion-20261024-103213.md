# Simulación de retención de respaldos (dry-run)

Generado: 2026-10-24T10:32:13-06:00. **No se eliminó ningún archivo.** Política propuesta pendiente de validación institucional: diaria 7 días, semanal 4 semanas, mensual 3 meses, y siempre la copia más reciente por base. Las duraciones no garantizan por sí solas el cumplimiento institucional o regulatorio.

| Métrica | Valor |
|---|---|
| sets_total | 16 |
| conservar | 2 |
| protegido | 10 |
| candidato | 4 |
| bytes_candidatos | 603196 |
| bytes_total | 2420768 |

Excluidos de la política (protegidos): `local/rollback`, `evidencias`. Las evidencias se conservan durante el desarrollo y evaluación del proyecto.

Archivos fuera del patrón de copias: .gitkeep, execution.log, universidad-20261024-084707.dump, universidad-20261024-084707.dump.sha256, universidad-20261024-084707.dump.toc (no evaluados).

**Hallazgo:** Copia sin cifrar fuera de la política: universidad-20261024-084707.dump. Contiene datos académicos sin cifrar en el directorio de copias; se recomienda cifrarla o eliminarla con autorización.

SIEM (30 días): {'retention_days': 30, 'events_total': 903, 'candidates': 0}.

| Base | Copia | Creada (UTC) | Antigüedad (h) | Decisión | Motivo | Bytes |
|---|---|---|---|---|---|---|
| academic | `academic-20261024-153259.dump.enc` | 2026-10-24T15:32:59+00:00 | 1.0 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-153444.dump.enc` | 2026-10-24T15:34:44+00:00 | 1.0 | candidato | copia intradía o fuera de las ventanas diaria/semanal/mensual (no es la última de su periodo) | 2600 |
| academic | `academic-20261024-154629.dump.enc` | 2026-10-24T15:46:29+00:00 | 0.8 | candidato | copia intradía o fuera de las ventanas diaria/semanal/mensual (no es la última de su periodo) | 2600 |
| academic | `academic-20261024-155231.dump.enc` | 2026-10-24T15:52:31+00:00 | 0.7 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-160159.dump.enc` | 2026-10-24T16:01:59+00:00 | 0.5 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-161153.dump.enc` | 2026-10-24T16:11:53+00:00 | 0.3 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-162047.dump.enc` | 2026-10-24T16:20:47+00:00 | 0.2 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-162333.dump.enc` | 2026-10-24T16:23:33+00:00 | 0.1 | conservar | más reciente de la base; última copia diaria (≤ 7 días); última copia semanal (≤ 4 semanas); última copia mensual (≤ 3 meses) (usada en una restauración o en la actualización (evidencia)) | 2600 |
| identity | `identity-20261024-153300.dump.enc` | 2026-10-24T15:33:00+00:00 | 1.0 | protegido | usada en una restauración o en la actualización (evidencia) | 299110 |
| identity | `identity-20261024-153444.dump.enc` | 2026-10-24T15:34:44+00:00 | 1.0 | candidato | copia intradía o fuera de las ventanas diaria/semanal/mensual (no es la última de su periodo) | 298774 |
| identity | `identity-20261024-154629.dump.enc` | 2026-10-24T15:46:29+00:00 | 0.8 | candidato | copia intradía o fuera de las ventanas diaria/semanal/mensual (no es la última de su periodo) | 299222 |
| identity | `identity-20261024-155231.dump.enc` | 2026-10-24T15:52:31+00:00 | 0.7 | protegido | usada en una restauración o en la actualización (evidencia) | 300070 |
| identity | `identity-20261024-160159.dump.enc` | 2026-10-24T16:01:59+00:00 | 0.5 | protegido | usada en una restauración o en la actualización (evidencia) | 300470 |
| identity | `identity-20261024-161154.dump.enc` | 2026-10-24T16:11:54+00:00 | 0.3 | protegido | usada en una restauración o en la actualización (evidencia) | 300998 |
| identity | `identity-20261024-162048.dump.enc` | 2026-10-24T16:20:48+00:00 | 0.2 | protegido | usada en una restauración o en la actualización (evidencia) | 300662 |
| identity | `identity-20261024-162333.dump.enc` | 2026-10-24T16:23:33+00:00 | 0.1 | conservar | más reciente de la base; última copia diaria (≤ 7 días); última copia semanal (≤ 4 semanas); última copia mensual (≤ 3 meses) (usada en una restauración o en la actualización (evidencia)) | 300662 |

Antes de aplicar cualquier borrado se requiere autorización expresa y revisión de este reporte.