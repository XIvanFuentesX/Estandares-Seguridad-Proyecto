# Índice de evidencias Azure (2026-10-24)

Estado global: **Terraform preparado y validado de forma estática; nada desplegado en Azure.**

| Archivo | Tipo | Contenido |
|---|---|---|
| `ARQUITECTURA-AZURE.md` | Documento | Región, estructura, topología y grafo Mermaid generados del código, seguridad por diseño |
| `diagrama-topologia.mmd`, `diagrama-dependencias.mmd` | Generado | Mermaid desde `terraform console` y `terraform graph` |
| `inventario-recursos-escenarios.md/.json` | Generado | Recursos del plan simulado por escenario (63/100/103/139) |
| `validacion-terraform-20261024.txt` | Salida real | fmt, init, validate, test (20/20), intento de plan, TFLint, resumen Trivy |
| `trivy-config-azure.json` y `trivy-config-azure-{dev,demo,inst}.json` | Salida real | Escaneo IaC por escenario |
| `HALLAZGOS-VALIDACION-IAC.md` | Documento | Resultados, correcciones y hallazgos aceptados |
| `politicas-integradas-verificadas-20261024.txt` | Salida real | 11 GUID de Azure Policy verificados |
| `precios-azure-20261024.json` | Salida real | API de precios minoristas (eastus2, southcentralus, Global, Zone 1) |
| `comparacion-regiones-20261024.txt` | Generado | Comparación de 703 medidores comunes |
| `costos-escenarios-20261024.md/.json` | Generado | Escenarios con fórmula y medidor (eastus2) |
| `costos-escenarios-20261024-southcentralus.md/.json` | Generado | Mismos escenarios en la región alternativa |
| `ANALISIS-COSTOS-AZURE.md` | Documento | Precios, escenarios, gratuidades, licencias, costos activos/inactivos |
| `MATRIZ-CONTROLES-AZURE.md` | Documento | ISO 27001/27002:2022, NIST CSF 2.0, Zero Trust, ISO 22301, COBIT 2019, ITIL 4, TIA-942 |
| `INTEGRACION-HIBRIDA.md` | Documento | VPN S2S vs. Arc vs. Storage con identidad |
| `PLAN-DESPLIEGUE-AZURE.md` | Documento | Pasos 0–14 con criterios de salida |
| `PLAN-PRUEBAS-POST-DESPLIEGUE.md` | Plantilla | 25 pruebas PT-AZ con plantillas vacías |
| `RIESGOS-CLOUD.md` | Documento | RC-01 a RC-16 |
| `DESACTIVACION-SEGURA-AZURE.md` | Documento | Orden y procedimiento para reducir costos |
| `REGISTRO-CAMBIOS-AZURE.md` | Registro | CAM-AZ-001…005 y plantilla |
| `APORTES-SGSI-AZURE.md` | Propuesta | Filas para inventario, riesgos, tratamiento, SoA, BIA/BCP/DRP |

Reproducción: `bash azure/scripts/validar_terraform.sh 20261024` y luego
`python -X utf8 -I azure/scripts/generar_inventario_diagrama.py`; precios: `consultar_precios_azure.py` → `calcular_costos_escenarios.py`.
