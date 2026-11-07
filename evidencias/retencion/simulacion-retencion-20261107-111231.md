# Simulación de retención de respaldos (dry-run)

Generado: 2026-11-07T11:12:31-06:00. **No se eliminó ningún archivo.** Política propuesta pendiente de validación institucional: diaria 7 días, semanal 4 semanas, mensual 3 meses, y siempre la copia más reciente por base. Las duraciones no garantizan por sí solas el cumplimiento institucional o regulatorio.

| Métrica | Valor |
|---|---|
| sets_total | 26 |
| conservar | 4 |
| protegido | 16 |
| candidato | 6 |
| bytes_candidatos | 907210 |
| bytes_total | 3643143 |

Excluidos de la política (protegidos): `local/rollback`, `evidencias`. Las evidencias se conservan durante el desarrollo y evaluación del proyecto.

Archivos fuera del patrón de copias: .gitkeep, execution.log, universidad-20261024-084707.dump, universidad-20261024-084707.dump.sha256, universidad-20261024-084707.dump.toc (no evaluados).

**Hallazgo:** Copia sin cifrar fuera de la política: universidad-20261024-084707.dump. Contiene datos académicos sin cifrar en el directorio de copias; se recomienda cifrarla o eliminarla con autorización.

SIEM (30 días): {'retention_days': 30, 'events_total': 3446, 'candidates': 0}.

| Base | Copia | Creada (UTC) | Antigüedad (h) | Decisión | Motivo | Bytes |
|---|---|---|---|---|---|---|
| academic | `academic-20261024-153259.dump.enc` | 2026-10-24T15:32:59+00:00 | 337.7 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-153444.dump.enc` | 2026-10-24T15:34:44+00:00 | 337.6 | candidato | copia intradía o fuera de las ventanas diaria/semanal/mensual (no es la última de su periodo) | 2600 |
| academic | `academic-20261024-154629.dump.enc` | 2026-10-24T15:46:29+00:00 | 337.4 | candidato | copia intradía o fuera de las ventanas diaria/semanal/mensual (no es la última de su periodo) | 2600 |
| academic | `academic-20261024-155231.dump.enc` | 2026-10-24T15:52:31+00:00 | 337.3 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-160159.dump.enc` | 2026-10-24T16:01:59+00:00 | 337.2 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-161153.dump.enc` | 2026-10-24T16:11:53+00:00 | 337.0 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-162047.dump.enc` | 2026-10-24T16:20:47+00:00 | 336.9 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-162333.dump.enc` | 2026-10-24T16:23:33+00:00 | 336.8 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-163544.dump.enc` | 2026-10-24T16:35:44+00:00 | 336.6 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-165047.dump.enc` | 2026-10-24T16:50:47+00:00 | 336.4 | candidato | copia intradía o fuera de las ventanas diaria/semanal/mensual (no es la última de su periodo) | 2600 |
| academic | `academic-20261024-171402.dump.enc` | 2026-10-24T17:14:02+00:00 | 336.0 | protegido | usada en una restauración o en la actualización (evidencia) | 2600 |
| academic | `academic-20261024-173321.dump.enc` | 2026-10-24T17:33:21+00:00 | 335.7 | conservar | última copia semanal (≤ 4 semanas); última copia mensual (≤ 3 meses) (usada en una restauración o en la actualización (evidencia)) | 2600 |
| academic | `academic-20261107-170858.dump.enc` | 2026-11-07T17:08:58+00:00 | 0.1 | conservar | más reciente de la base; última copia diaria (≤ 7 días); última copia semanal (≤ 4 semanas); última copia mensual (≤ 3 meses) | 2600 |
| identity | `identity-20261024-153300.dump.enc` | 2026-10-24T15:33:00+00:00 | 337.7 | protegido | usada en una restauración o en la actualización (evidencia) | 299110 |
| identity | `identity-20261024-153444.dump.enc` | 2026-10-24T15:34:44+00:00 | 337.6 | candidato | copia intradía o fuera de las ventanas diaria/semanal/mensual (no es la última de su periodo) | 298774 |
| identity | `identity-20261024-154629.dump.enc` | 2026-10-24T15:46:29+00:00 | 337.4 | candidato | copia intradía o fuera de las ventanas diaria/semanal/mensual (no es la última de su periodo) | 299222 |
| identity | `identity-20261024-155231.dump.enc` | 2026-10-24T15:52:31+00:00 | 337.3 | protegido | usada en una restauración o en la actualización (evidencia) | 300070 |
| identity | `identity-20261024-160159.dump.enc` | 2026-10-24T16:01:59+00:00 | 337.2 | protegido | usada en una restauración o en la actualización (evidencia) | 300470 |
| identity | `identity-20261024-161154.dump.enc` | 2026-10-24T16:11:54+00:00 | 337.0 | protegido | usada en una restauración o en la actualización (evidencia) | 300998 |
| identity | `identity-20261024-162048.dump.enc` | 2026-10-24T16:20:48+00:00 | 336.9 | protegido | usada en una restauración o en la actualización (evidencia) | 300662 |
| identity | `identity-20261024-162333.dump.enc` | 2026-10-24T16:23:33+00:00 | 336.8 | protegido | usada en una restauración o en la actualización (evidencia) | 300662 |
| identity | `identity-20261024-163544.dump.enc` | 2026-10-24T16:35:44+00:00 | 336.6 | protegido | usada en una restauración o en la actualización (evidencia) | 301894 |
| identity | `identity-20261024-165048.dump.enc` | 2026-10-24T16:50:48+00:00 | 336.4 | candidato | copia intradía o fuera de las ventanas diaria/semanal/mensual (no es la última de su periodo) | 301414 |
| identity | `identity-20261024-171403.dump.enc` | 2026-10-24T17:14:03+00:00 | 336.0 | protegido | usada en una restauración o en la actualización (evidencia) | 301830 |
| identity | `identity-20261024-173322.dump.enc` | 2026-10-24T17:33:22+00:00 | 335.7 | conservar | más reciente de la base; última copia semanal (≤ 4 semanas); última copia mensual (≤ 3 meses) (usada en una restauración o en la actualización (evidencia)) | 302374 |
| universidad | `universidad-20261024-084707.dump.enc` | 2026-10-24T08:47:07+00:00 | 344.4 | conservar | más reciente de la base; última copia semanal (≤ 4 semanas); última copia mensual (≤ 3 meses) (conjunto incompleto: requiere revisión manual, no se propone borrar) | 1863 |

Antes de aplicar cualquier borrado se requiere autorización expresa y revisión de este reporte.