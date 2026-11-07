# Costos estimados por escenario — southcentralus

Fuente: API pública oficial `https://prices.azure.com/api/retail/prices` (sin autenticación), consulta **2026-10-24T16:52:23+00:00** (UTC).
Precios minoristas en USD, tipo *Consumption*, sin impuestos, descuentos ni créditos. Mes = 730 h.
Generado por `azure/scripts/calcular_costos_escenarios.py`; datos crudos filtrados en `evidencias/azure/precios-azure-20261024.json`.

## Escenario 1 — Mínimo académico (environments/dev.tfvars.example)

Horas supuestas: 730 h/mes para recursos siempre activos.

| Concepto | SKU / medidor | Fórmula | USD/mes | Nota |
|---|---|---|---:|---|
| Private Endpoint (blob + vault) | Standard | 1460 PE-hora x $0.01/1 Hour | 14.60 | 2 PE activos |
| Datos procesados por PE (entrada) | Standard | 5 GB x $0.01/1 GB | 0.05 |  |
| Datos procesados por PE (salida) | Standard | 5 GB x $0.01/1 GB | 0.05 |  |
| Zonas DNS privadas | Private Zone | 2 zona x $0.5/1 | 1.00 |  |
| Consultas DNS privadas | Private Queries | 0.1 millón x $0.4/1M | 0.04 |  |
| Storage blob Hot LRS (evidencias + intercambio) | Hot LRS | 20 GB-mes x $0.0184/1 GB/Month | 0.37 |  |
| Storage escrituras | Hot LRS | 2 x10K x $0.05/10K | 0.10 | 20 000 escrituras/mes |
| Storage lecturas | Hot LRS | 5 x10K x $0.004/10K | 0.02 | 50 000 lecturas/mes |
| Key Vault operaciones | Standard | 5 x10K x $0.03/10K | 0.15 | 50 000 operaciones/mes |
| Alerta de consulta (15 min) | Log alert | 1 regla x $0.5/1/Month | 0.50 | Interpretación: medidor 'System Log Monitored at 15 Minute Frequency' |
| Peering hub-spoke (intra-región) | Intra-Region | 2 GB x $0.01/1 GB | 0.02 | Ingreso y egreso se cobran; se toma egreso |
| Azure Arc: servidor habilitado (host Docker) | Arc Enabled Servers | 730 h x $0/1 Hour | 0.00 | Plano de control sin costo según API; extensiones/Defender se cobran aparte |
| Transferencia de salida (≤100 GB) | MGN tramo 0 | 10 GB x $0/1 GB | 0.00 |  |
| Log Analytics ingesta (tope 0.16 GB/día) | PerGB2018 tramo 0-5 GB | 5 GB x $0/1 GB | 0.00 | Retención 30 días; franja 0-5 GB a $0 según API |
| **Total estimado** | | | **16.90** | |

## Escenario 2 — Académico recomendado (environments/demo.tfvars.example)

Horas supuestas: 730 h/mes siempre activos; VPN sólo 40 h/mes de ventana de demostración.

| Concepto | SKU / medidor | Fórmula | USD/mes | Nota |
|---|---|---|---:|---|
| Private Endpoint (blob + vault) | Standard | 1460 PE-hora x $0.01/1 Hour | 14.60 | 2 PE activos |
| Datos procesados por PE (entrada) | Standard | 5 GB x $0.01/1 GB | 0.05 |  |
| Datos procesados por PE (salida) | Standard | 5 GB x $0.01/1 GB | 0.05 |  |
| Zonas DNS privadas | Private Zone | 2 zona x $0.5/1 | 1.00 |  |
| Consultas DNS privadas | Private Queries | 0.1 millón x $0.4/1M | 0.04 |  |
| Storage blob Hot LRS (evidencias + intercambio) | Hot LRS | 50 GB-mes x $0.0184/1 GB/Month | 0.92 |  |
| Storage escrituras | Hot LRS | 2 x10K x $0.05/10K | 0.10 | 20 000 escrituras/mes |
| Storage lecturas | Hot LRS | 5 x10K x $0.004/10K | 0.02 | 50 000 lecturas/mes |
| Key Vault operaciones | Standard | 5 x10K x $0.03/10K | 0.15 | 50 000 operaciones/mes |
| Alerta de consulta (15 min) | Log alert | 1 regla x $0.5/1/Month | 0.50 | Interpretación: medidor 'System Log Monitored at 15 Minute Frequency' |
| Peering hub-spoke (intra-región) | Intra-Region | 2 GB x $0.01/1 GB | 0.02 | Ingreso y egreso se cobran; se toma egreso |
| Azure Arc: servidor habilitado (host Docker) | Arc Enabled Servers | 730 h x $0/1 Hour | 0.00 | Plano de control sin costo según API; extensiones/Defender se cobran aparte |
| Transferencia de salida (≤100 GB) | MGN tramo 0 | 10 GB x $0/1 GB | 0.00 |  |
| Log Analytics ingesta franja gratuita | PerGB2018 tramo 0-5 GB | 5 GB x $0/1 GB | 0.00 |  |
| Log Analytics ingesta sobre 5 GB | PerGB2018 tramo >5 GB | 10 GB x $2.76/1 GB | 27.60 | 15 GB/mes (tope 0.5 GB/día) |
| Log Analytics retención 90 días | Data Retention | 30 GB-mes x $0.12/1 GB/Month | 3.60 | Supuesto: 31 días incluidos (no verificado vía API); ~2 meses de datos retenidos con cargo |
| Recovery Services: servidor local (MARS) | On Premises Server | 1 instancia x $10/1/Month | 10.00 |  |
| Recovery Services: almacenamiento LRS | Standard LRS | 50 GB-mes x $0.0224/1 GB/Month | 1.12 |  |
| Defender for Servers P1 (host Arc) | Standard P1 | 730 nodo-h x $0.00672/1/Hour | 4.91 |  |
| VPN Gateway VpnGw1AZ (ventana demo) | VpnGw1AZ | 40 h x $0.21/1 Hour | 8.40 | Se crea y destruye; no se puede detener |
| Conexión S2S (ventana demo) | S2S Connection | 40 h x $0.015/1 Hour | 0.60 | Conservador: la página de precios incluye túneles en el SKU (no verificado vía API) |
| IP pública estándar del gateway (ventana demo) | Standard IPv4 | 40 h x $0.005/1 Hour | 0.20 |  |
| **Total estimado** | | | **73.88** | |

## Escenario 3 — Institucional de referencia (environments/inst.tfvars.example)

Horas supuestas: 730 h/mes 24x7 para todos los componentes.

| Concepto | SKU / medidor | Fórmula | USD/mes | Nota |
|---|---|---|---:|---|
| Private Endpoint (blob + vault) | Standard | 1460 PE-hora x $0.01/1 Hour | 14.60 |  |
| Datos procesados por PE (entrada+salida) | Standard | 200 GB x $0.01/1 GB | 2.00 |  |
| Zonas DNS privadas | Private Zone | 2 zona x $0.5/1 | 1.00 |  |
| Consultas DNS privadas | Private Queries | 5 millón x $0.4/1M | 2.00 |  |
| Storage Hot GRS | Hot GRS | 500 GB-mes x $0.0368/1 GB/Month | 18.40 |  |
| Storage Cool GRS (evidencias > 30 días) | Cool GRS | 2000 GB-mes x $0.02/1 GB/Month | 40.00 |  |
| Storage escrituras | Hot GRS | 100 x10K x $0.1/10K | 10.00 | 1 M escrituras/mes |
| Storage lecturas | Hot | 300 x10K x $0.004/10K | 1.20 | 3 M lecturas/mes |
| Key Vault operaciones | Standard | 100 x10K x $0.03/10K | 3.00 | 1 M operaciones/mes |
| Log Analytics ingesta franja gratuita | tramo 0-5 GB | 5 GB x $0/1 GB | 0.00 |  |
| Log Analytics ingesta sobre 5 GB | tramo >5 GB | 147 GB x $2.76/1 GB | 405.72 | 5 GB/día ≈ 152 GB/mes |
| Log Analytics retención 90 días | Data Retention | 304 GB-mes x $0.12/1 GB/Month | 36.48 | Supuesto 31 días incluidos (no verificado) |
| Microsoft Sentinel (pago por uso) | Pay-as-you-go | 152 GB x $5.16/1 GB | 784.32 | Supuesto: medidor de Sentinel adicional a la ingesta de LA (modelo clásico); verificar con la calculadora |
| Alertas de consulta (15 min) | Log alert | 5 regla x $0.5/1/Month | 2.50 |  |
| Recovery Services: servidores locales (MARS) | On Premises Server | 4 instancia x $10/1/Month | 40.00 |  |
| Recovery Services: almacenamiento GRS | Standard GRS | 1000 GB-mes x $0.0448/1 GB/Month | 44.80 |  |
| VPN Gateway VpnGw1AZ | VpnGw1AZ | 730 h x $0.21/1 Hour | 153.30 |  |
| Conexión S2S | S2S Connection | 730 h x $0.015/1 Hour | 10.95 | Conservador (ver escenario 2) |
| Azure Firewall Standard | Standard | 730 h x $1.25/1 Hour | 912.50 |  |
| Azure Firewall datos procesados | Standard | 500 GB x $0.016/1 GB | 8.00 |  |
| Azure Bastion Basic | Basic | 730 h x $0.19/1 Hour | 138.70 |  |
| Application Gateway WAF_v2 (fijo) | WAF_v2 | 730 h x $0.432/1/Hour | 315.36 |  |
| Application Gateway WAF_v2 (unidades de capacidad) | WAF_v2 | 1460 CU-h x $0.0144/1/Hour | 21.02 | Promedio 2 CU |
| IP públicas estándar (VPN, firewall, Bastion, App GW) | Standard IPv4 | 2920 IP-h x $0.005/1 Hour | 14.60 |  |
| Defender for Servers P2 | Standard P2 | 2920 nodo-h x $0.02/1/Hour | 58.40 | 4 servidores (Arc o VM) |
| Defender for Storage | Standard | 730 cuenta-h x $0.0134/1/Hour | 9.78 | 1 cuenta; escaneo de malware aparte |
| Defender for Key Vault | Per node Std | 730 bóveda-h x $0.00034/1/Hour | 0.25 |  |
| Defender for Resource Manager | Per node Std | 730 suscripción-h x $0.0069/1/Hour | 5.04 |  |
| Peering hub-spoke | Intra-Region | 500 GB x $0.01/1 GB | 5.00 |  |
| Transferencia de salida (primeros 100 GB) | MGN tramo 0 | 100 GB x $0/1 GB | 0.00 |  |
| Transferencia de salida (>100 GB) | MGN tramo 100 GB+ | 200 GB x $0.087/1 GB | 17.40 |  |
| **Total estimado** | | | **3076.32** | |

## Precios unitarios usados

| Clave | Precio | Unidad | Medidor (fuente) |
|---|---:|---|---|
| pe_hora | 0.01 | 1 Hour | Virtual Network Private Link / Standard / Standard Private Endpoint (tramo ≥0) [private_link_global] |
| pe_gb_in | 0.01 | 1 GB | Virtual Network Private Link / Standard / Standard Data Processed - Ingress (tramo ≥0) [private_link_global] |
| pe_gb_out | 0.01 | 1 GB | Virtual Network Private Link / Standard / Standard Data Processed - Egress (tramo ≥0) [private_link_global] |
| dns_zona | 0.5 | 1 | Azure DNS / Private / Private Zone (tramo ≥0) [dns_zona1] |
| dns_consultas_1M | 0.4 | 1M | Azure DNS / Private / Private Queries (tramo ≥0) [dns_zona1] |
| st_hot_lrs_gb | 0.0184 | 1 GB/Month | General Block Blob v2 / Hot LRS / Hot LRS Data Stored (tramo ≥0) [storage_blob@southcentralus] |
| st_hot_grs_gb | 0.0368 | 1 GB/Month | General Block Blob v2 / Hot GRS / Hot GRS Data Stored (tramo ≥0) [storage_blob@southcentralus] |
| st_cool_grs_gb | 0.02 | 1 GB/Month | General Block Blob v2 / Cool GRS / Cool GRS Data Stored (tramo ≥0) [storage_blob@southcentralus] |
| st_hot_lrs_esc_10k | 0.05 | 10K | General Block Blob v2 / Hot LRS / Hot LRS Write Operations (tramo ≥0) [storage_blob@southcentralus] |
| st_hot_grs_esc_10k | 0.1 | 10K | General Block Blob v2 / Hot GRS / Hot GRS Write Operations (tramo ≥0) [storage_blob@southcentralus] |
| st_hot_lect_10k | 0.004 | 10K | General Block Blob v2 / Hot LRS / Hot Read Operations (tramo ≥0) [storage_blob@southcentralus] |
| kv_ops_10k | 0.03 | 10K | Key Vault / Standard / Operations (tramo ≥0) [key_vault@southcentralus] |
| law_ingesta_gratis | 0.0 | 1 GB | Log Analytics / Analytics Logs / Analytics Logs Data Ingestion (tramo ≥0) [log_analytics@southcentralus] |
| law_ingesta_gb | 2.76 | 1 GB | Log Analytics / Analytics Logs / Analytics Logs Data Ingestion (tramo ≥5) [log_analytics@southcentralus] |
| law_retencion_gb_mes | 0.12 | 1 GB/Month | Log Analytics / Analytics Logs / Analytics Logs Data Retention (tramo ≥0) [log_analytics@southcentralus] |
| sentinel_gb | 5.16 | 1 GB | Sentinel / Pay-as-you-go / Pay-as-you-go Analysis (tramo ≥0) [sentinel@southcentralus] |
| alerta_log_15min | 0.5 | 1/Month | Azure Monitor / Alerts / Alerts System Log Monitored at 15 Minute Frequency (tramo ≥0) [azure_monitor@southcentralus] |
| rsv_instancia_onprem | 10.0 | 1/Month | Backup / On Premises Server / On Premises Server Protected Instance (tramo ≥0) [backup@southcentralus] |
| rsv_lrs_gb | 0.0224 | 1 GB/Month | Backup / Standard / Standard LRS Data Stored (tramo ≥0) [backup@southcentralus] |
| rsv_grs_gb | 0.0448 | 1 GB/Month | Backup / Standard / Standard GRS Data Stored (tramo ≥0) [backup@southcentralus] |
| vpn_vpngw1az_h | 0.21 | 1 Hour | VPN Gateway / VpnGw1AZ / VpnGw1AZ (tramo ≥0) [vpn_gateway@southcentralus] |
| vpn_s2s_h | 0.015 | 1 Hour | VPN Gateway / VpnGw1AZ / S2S Connection (tramo ≥0) [vpn_gateway@southcentralus] |
| vpn_basic_h | 0.036 | 1 Hour | VPN Gateway / Basic / Basic Gateway (tramo ≥0) [vpn_gateway@southcentralus] |
| vpn_vpngw1_h | 0.19 | 1 Hour | VPN Gateway / VpnGw1 / VpnGw1 (tramo ≥0) [vpn_gateway@southcentralus] |
| ip_std_h | 0.005 | 1 Hour | IP Addresses / Standard / Standard IPv4 Static Public IP (tramo ≥0) [ip_publica@southcentralus] |
| afw_basic_h | 0.395 | 1 Hour | Azure Firewall / Basic / Basic Deployment (tramo ≥0) [azure_firewall@southcentralus] |
| afw_basic_gb | 0.065 | 1 GB | Azure Firewall / Basic / Basic Data Processed (tramo ≥0) [azure_firewall@southcentralus] |
| afw_std_h | 1.25 | 1 Hour | Azure Firewall / Standard / Standard Deployment (tramo ≥0) [azure_firewall@southcentralus] |
| afw_std_gb | 0.016 | 1 GB | Azure Firewall / Standard / Standard Data Processed (tramo ≥0) [azure_firewall@southcentralus] |
| bastion_basic_h | 0.19 | 1 Hour | Azure Bastion / Basic / Basic Gateway (tramo ≥0) [bastion@southcentralus] |
| bastion_std_h | 0.29 | 1 Hour | Azure Bastion / Standard / Standard Gateway (tramo ≥0) [bastion@southcentralus] |
| agw_waf_fijo_h | 0.432 | 1/Hour | Application Gateway WAF v2 / Standard / Standard Fixed Cost (tramo ≥0) [app_gateway@southcentralus] |
| agw_waf_cu_h | 0.0144 | 1/Hour | Application Gateway WAF v2 / Standard / Standard Capacity Units (tramo ≥0) [app_gateway@southcentralus] |
| def_servers_p1_h | 0.00672 | 1/Hour | Microsoft Defender for Servers / Standard P1 / Standard P1 Node (tramo ≥0) [defender@southcentralus] |
| def_servers_p2_h | 0.02 | 1/Hour | Microsoft Defender for Servers / Standard P2 / Standard P2 Node (tramo ≥0) [defender@southcentralus] |
| def_storage_h | 0.0134 | 1/Hour | Microsoft Defender for Storage / Standard / Standard Node (tramo ≥0) [defender@southcentralus] |
| def_kv_h | 0.00034 | 1/Hour | Microsoft Defender for Key Vault / Per node Std / Per node Std Node (tramo ≥0) [defender@southcentralus] |
| def_arm_h | 0.0069 | 1/Hour | Microsoft Defender for Resource Manager / Per node Std / Per node Std Node (tramo ≥0) [defender@southcentralus] |
| egreso_gratis | 0.0 | 1 GB | Rtn Preference: MGN / Standard / Standard Data Transfer Out (tramo ≥0) [transferencia_salida@southcentralus] |
| egreso_gb | 0.087 | 1 GB | Rtn Preference: MGN / Standard / Standard Data Transfer Out (tramo ≥100) [transferencia_salida@southcentralus] |
| peering_gb | 0.01 | 1 GB | Virtual Network Peering / Intra-Region / Intra-Region Egress (tramo ≥0) [vnet_peering_global] |
| arc_servidor_h | 0.0 | 1 Hour | Azure Arc / Azure Arc Enabled Servers (VMs) / Azure Arc Enabled Servers (VMs) (tramo ≥0) [azure_arc_global] |
