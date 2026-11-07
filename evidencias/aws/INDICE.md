# Índice de evidencias AWS

Estado: **preparado, no desplegado** (sin sesión AWS para verificar la cuenta). Todas las evidencias son de validación estática o de diseño; no hay evidencias de recursos reales, capturas de consola ni facturación.

| Archivo | Contenido | Tipo |
|---|---|---|
| `validacion-terraform-aws-20261024.txt` | fmt, validate, test (mock), TFLint y Trivy | Real (estática) |
| `trivy-config-aws.json` | Análisis IaC: 58 OK, 3 hallazgos aceptados | Real (estática) |
| `prueba-compuerta-plan-20261024.json` | Compuerta de costo: aprueba el plan conforme y rechaza NAT Gateway | Real sobre planes **sintéticos** |
| `precios-s3-us-east-1-20261024.json` | Precios S3 de la API pública de AWS (publicación 2026-10-15) | Real (fuente oficial) |
| `COSTOS-AWS.md` | Condiciones del plan Free con fuentes, estimación y hallazgos aceptados | Documento |
| `ARQUITECTURA-AWS.md` | Diagrama híbrido e inventario proyectado | Documento |
| `RIESGOS-Y-RETIRADA-AWS.md` | Riesgos RA-01…08 y retirada segura | Documento |
| *(tras desplegar)* `verificacion-cuenta-*.json`, `plan-*.txt`, `revision-plan-*.json`, `apply-*.txt`, `pruebas-aws-*.json`, `retirada-*` | Generados por `aws/scripts/` | Pendiente |

Cierre: [`../../CIERRE_AWS.md`](../../CIERRE_AWS.md).
