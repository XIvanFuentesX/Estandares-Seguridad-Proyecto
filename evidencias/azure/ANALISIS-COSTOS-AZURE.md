# Análisis de costos Azure — SGSI UVCG

**Fuente única de precios**: API pública oficial *Azure Retail Prices* (`https://prices.azure.com/api/retail/prices`,
sin autenticación), consultada el **2026-10-24 16:52:23 UTC** con `azure/scripts/consultar_precios_azure.py`
(filtros `$filter` por servicio y región; sólo medidores `Consumption`). Respuesta filtrada:
`precios-azure-20261024.json`. Cálculo reproducible: `azure/scripts/calcular_costos_escenarios.py` →
`costos-escenarios-20261024.md/.json` (desglose renglón por renglón con fórmula y medidor exacto).

Advertencias: precios minoristas en USD, sin impuestos, sin descuentos educativos/EA/CSP ni créditos; mes = 730 h.
No es una cotización. La API respondió para todos los servicios consultados; ningún renglón quedó sin precio.

## 1. Precios unitarios obtenidos (eastus2, salvo indicación)

| Servicio solicitado | SKU / medidor | Precio | Observación |
|---|---|---:|---|
| VPN Gateway | Basic | 0.036 USD/h | SKU Basic sin IKEv2 personalizado ni BGP; no recomendado |
| VPN Gateway | VpnGw1 / VpnGw1AZ | 0.19 / 0.21 USD/h | El código usa VpnGw1AZ |
| VPN Gateway | Conexión S2S | 0.015 USD/h | Se suma de forma conservadora (ver §3) |
| Azure Firewall | Basic: despliegue / datos | 0.395 USD/h / 0.065 USD/GB | |
| Azure Firewall | Standard: despliegue / datos | 1.25 USD/h / 0.016 USD/GB | |
| Azure Bastion | Basic / Standard | 0.19 / 0.29 USD/h | Salida: 0–5 GB a 0 USD; luego 0.087 USD/GB |
| Azure Bastion | Developer | **no aparece en la API** | Precio y disponibilidad regional **no verificados** |
| Log Analytics | Ingesta (Analytics Logs) | 0 USD/GB (0–5 GB) ; 2.76 USD/GB (>5 GB) | Retención 0.12 USD/GB-mes |
| Microsoft Sentinel | Pago por uso (Analysis) | 4.76 USD/GB (southcentralus 5.16) | Niveles de compromiso desde 100 GB/día |
| Storage blob | Hot LRS / Hot GRS | 0.0184 / 0.0368 USD/GB-mes | Primer tramo (<50 TB) |
| Storage blob | Cool LRS / Cool GRS | 0.01 / 0.02 USD/GB-mes | Escrituras Cool LRS 0.10 USD/10K |
| Key Vault | Standard: operaciones | 0.03 USD/10K | Rotación automática 1 USD/rotación |
| Backup (Recovery Services) | Servidor local / blob protegido | 10 USD/instancia-mes | Almacenamiento LRS 0.0224 / GRS 0.0448 USD/GB-mes |
| IP pública | Standard IPv4 estática | 0.005 USD/h | ≈ 3.65 USD/mes |
| Private Endpoint | Standard | 0.01 USD/h + 0.01 USD/GB | Medidor en región lógica `Global` |
| DNS privado | Zona / consultas | 0.50 USD/zona-mes / 0.40 USD/millón | Medidor en `Zone 1` |
| Transferencia de salida | Red de Microsoft | 0 USD (primeros 100 GB) ; 0.087 USD/GB | Tramos decrecientes |
| App Gateway WAF_v2 | Fijo / unidad de capacidad | 0.36 USD/h / 0.0144 USD/CU-h | southcentralus 0.432 USD/h |
| Defender for Servers | P1 / P2 | 0.00672 / 0.02 USD/servidor-h | ≈ 4.91 / 14.60 USD/mes |
| Defender for Storage | Por cuenta | 0.0134 USD/h | Escaneo de malware 0.15 USD/GB aparte |
| Azure Arc (servidores) | Plano de control | 0 USD/h | Extensiones y Defender se cobran aparte |
| Alertas Azure Monitor | Log alert 15 min | 0.50 USD/regla-mes | Métricas: 10 series gratis, luego 0.10 |

## 2. Escenarios (totales calculados con los precios anteriores)

| Escenario | tfvars | Componentes principales | Horas supuestas | Total USD/mes |
|---|---|---|---|---:|
| 1. Mínimo académico | `dev.tfvars.example` | Red, políticas, Defender Free, presupuesto, KV, Storage LRS privado, 2 PE, 2 zonas DNS, LAW ≤ 5 GB, alertas | 730 h | **16.90** |
| 2. Académico recomendado | `demo.tfvars.example` | Escenario 1 + LAW 15 GB/90 d, Recovery Services (1 servidor MARS, 50 GB), Defender for Servers P1 (host Arc), VPN VpnGw1AZ sólo 40 h de demostración | 730 h + 40 h VPN | **73.88** |
| 3. Institucional de referencia | `inst.tfvars.example` | VPN 24x7, Firewall Standard, Bastion Basic, App Gateway WAF_v2, Sentinel 5 GB/día, Storage GRS 2.5 TB, 4 servidores en backup GRS, Defender P2/Storage/KV/ARM | 730 h | **2,962.96** |

Fórmulas (detalle completo en `costos-escenarios-20261024.md`):

- Escenario 1: `2 PE × 730 h × 0.01` (14.60) + `10 GB × 0.01` PE (0.10) + `2 zonas × 0.50` (1.00) + `0.1 M × 0.40` DNS (0.04)
  + `20 GB × 0.0184` (0.37) + `2 × 0.05` escrituras (0.10) + `5 × 0.004` lecturas (0.02) + `5 × 0.03` KV (0.15)
  + `1 regla × 0.50` (0.50) + `2 GB × 0.01` peering (0.02) + LAW `5 GB × 0` + Arc `730 × 0` + salida `10 GB × 0` = **16.90**.
- Escenario 2: base 1 con 50 GB (17.45) + LAW `10 GB × 2.76` (27.60) + retención `30 GB-mes × 0.12` (3.60) + backup `1 × 10 + 50 × 0.0224` (11.12)
  + Defender P1 `730 × 0.00672` (4.91) + VPN `40 h × (0.21 + 0.015 + 0.005)` (9.20) = **73.88**.
- Escenario 3: dominado por Sentinel `152 GB × 4.76` (723.52), Firewall Standard `730 × 1.25` (912.50), LAW `147 GB × 2.76` (405.72),
  App Gateway `730 × 0.36 + 1460 CU-h × 0.0144` (283.82), VPN `730 × 0.21` (153.30) y Bastion `730 × 0.19` (138.70).

Supuestos marcados como **no verificados** (no se pueden confirmar con la API de precios):
- Retención incluida de 31 días en Log Analytics (sólo se cobra el excedente).
- Sentinel pago por uso se suma a la ingesta de Log Analytics (modelo clásico); con precios simplificados puede diferir.
- Túneles S2S incluidos en el SKU del gateway: se cobran 0.015 USD/h igualmente (cálculo conservador).
- Las 8 alertas del registro de actividad y el grupo de acciones (correo) no tienen medidor en la API: se consideran 0 USD.
- Presupuestos (Cost Management) y Azure Policy (definiciones integradas) no tienen medidor: 0 USD.

## 3. Gratuidades verificadas y no verificadas

| Gratuidad | Estado | Fuente y condiciones |
|---|---|---|
| Ingesta Log Analytics 0–5 GB | **Verificada (API)** | Medidor `Analytics Logs Data Ingestion`, tramo 0 = 0 USD; el alcance (por cuenta de facturación/mes) **no verificado** |
| Salida de datos 0–100 GB/mes | **Verificada (API)** | `Standard Data Transfer Out` tramo 0 = 0 USD (preferencia de red de Microsoft) |
| Salida de Bastion 0–5 GB | **Verificada (API)** | `Basic/Standard Data Transfer Out` tramo 0 = 0 USD |
| Alertas de métricas: 10 series | **Verificada (API)** | `Alerts Metric Monitored` tramo 0–10 = 0 USD |
| Registros DNS privados (tramo inicial) | **Verificada (API)** | `Private Record Set` tramo 0 = 0 USD |
| Azure Arc servidores (plano de control) | **Verificada (API)** | `Azure Arc Enabled Servers (VMs)` = 0 USD/h |
| Defender for Cloud nivel Free (CSPM básico) | No verificado | No es un medidor; documentado por Microsoft |
| Pruebas de Sentinel/Defender (medidores `Free Trial`/`Trial` a 0 USD) | Parcial | El medidor existe a 0 USD; duración y límites **no verificados** |
| Bastion Developer gratuito | No verificado | No aparece en la API |
| Cuenta gratuita / Azure for Students (créditos) | No verificado | Requiere elegibilidad; no consultable por la API |
| Activity log alerts y correos del grupo de acciones | No verificado | Sin medidor en la API |

## 4. Dependencias de licencias (fuera de la API de precios de Azure)

| Control | Licencia requerida | Estado |
|---|---|---|
| Acceso Condicional (exigir MFA, ubicación, dispositivo) para administradores de Azure | Microsoft Entra ID P1 | Precio **no verificado** (no está en la API); puede estar incluido en planes educativos A3/A5 (**no verificado**) |
| PIM (activación justo a tiempo de Owner/RBAC Admin), Identity Protection | Microsoft Entra ID P2 | **No verificado** |
| Cumplimiento de dispositivos para Acceso Condicional, MDM | Microsoft Intune | **No verificado**; el laboratorio sigue sin MDM (R-013) |
| MFA básico (valores predeterminados de seguridad) | Incluido en Entra ID Free | No verificado; sin Acceso Condicional |

Sin P1 el diseño no puede imponer Acceso Condicional: la mitigación disponible es *Security defaults* + MFA en Keycloak para la
aplicación local. Este hueco se registra como RC-15.

## 5. Costos activos vs. inactivos y cómo reducirlos

| Recurso | ¿Cobra sin uso? | Cómo detener el cobro | Efecto |
|---|---|---|---|
| VPN Gateway | **Sí, por hora mientras exista** | `enable_vpn_gateway = false` + apply aprobado (destruye gateway e IP) | Recrear tarda decenas de minutos (no medido) y cambia la IP pública |
| Azure Firewall | **Sí, por hora** | `enable_firewall = false`; alternativa documentada por Microsoft: desasignar (`Stop`/`Deallocate`) — **no probado** | Las UDR se eliminan con la bandera; sin firewall se pierde inspección central |
| Application Gateway WAF_v2 | **Sí, cargo fijo** | `enable_app_gateway = false`; o detener el gateway (`Stop-AzApplicationGateway`, **no probado**) | Sin publicación web |
| Bastion Basic/Standard | **Sí, por hora** | `enable_bastion = false` | Sin acceso administrativo por Bastion |
| IP públicas Standard | **Sí, por hora** | Se eliminan con su recurso | — |
| Private Endpoints | **Sí, por hora** | `enable_private_endpoints = false` (requiere apagar antes KV/Storage fuera de dev, precondición) | Sin acceso privado a PaaS |
| Log Analytics / Sentinel | Sólo por GB ingerido/retenido | Bajar `log_daily_quota_gb`, `enable_sentinel = false` | Tope diario corta registros (RC-08) |
| Storage / Backup | Por GB almacenado | Ciclo de vida, borrar copias vencidas | Inmutabilidad y borrado suave retienen datos (y costo) durante su periodo |
| Defender Standard | Por recurso-hora | Volver a `Free` en `defender_plans` | Se pierde protección de carga |
| Red, NSG, UDR, políticas, identidades, presupuesto | No | — | — |

El **presupuesto no bloquea el gasto**: sólo envía notificaciones al 50/80/100 % real y 100 % pronosticado. El control
efectivo es: banderas en `false`, revisión del plan con `revisar_plan.py`, autorización previa y desactivación segura
(`DESACTIVACION-SEGURA-AZURE.md`).
