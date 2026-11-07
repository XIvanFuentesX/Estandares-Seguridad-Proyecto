"""Calcula los tres escenarios de costo con precios REALES de la API pública de Azure.

Entrada : evidencias/azure/precios-azure-<fecha>.json (consultar_precios_azure.py)
Salida  : evidencias/azure/costos-escenarios-<fecha>.json y .md
Uso     : python -I azure/scripts/calcular_costos_escenarios.py [precios.json] [region]

Reglas: cada precio unitario se toma del JSON (si falta, el renglón queda "NO DISPONIBLE" y no se
suma); no se inventan cifras. Precios minoristas USD sin impuestos ni descuentos.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EV = RAIZ / "evidencias" / "azure"
PRECIOS = Path(sys.argv[1]) if len(sys.argv) > 1 else EV / "precios-azure-20261024.json"
REGION = sys.argv[2] if len(sys.argv) > 2 else "eastus2"
HORAS_MES = 730  # convención de la calculadora de Azure (24 x 365 / 12)

datos = json.loads(PRECIOS.read_text(encoding="utf-8"))
R = datos["resultados"]


def precio(clave, sku, medidor, tramo=0.0, producto=None, regional=True):
    """Devuelve (precio, unidad, ref) del medidor exacto o (None, None, ref)."""
    k = f"{clave}@{REGION}" if regional else clave
    for i in R.get(k, {}).get("items", []):
        if i["skuName"] == sku and i["meterName"] == medidor and float(i["tierMinimumUnits"]) == tramo:
            if producto and i["productName"] != producto:
                continue
            return i["retailPrice"], i["unitOfMeasure"], f'{i["productName"]} / {sku} / {medidor} (tramo ≥{tramo:g}) [{k}]'
    return None, None, f"NO DISPONIBLE: {k} {producto or ''} {sku} {medidor} tramo {tramo}"


# Catálogo de precios usados (todos desde la API).
P = {
    "pe_hora": precio("private_link_global", "Standard", "Standard Private Endpoint", regional=False),
    "pe_gb_in": precio("private_link_global", "Standard", "Standard Data Processed - Ingress", regional=False),
    "pe_gb_out": precio("private_link_global", "Standard", "Standard Data Processed - Egress", regional=False),
    "dns_zona": precio("dns_zona1", "Private", "Private Zone", regional=False),
    "dns_consultas_1M": precio("dns_zona1", "Private", "Private Queries", regional=False),
    "st_hot_lrs_gb": precio("storage_blob", "Hot LRS", "Hot LRS Data Stored", producto="General Block Blob v2"),
    "st_hot_grs_gb": precio("storage_blob", "Hot GRS", "Hot GRS Data Stored", producto="General Block Blob v2"),
    "st_cool_grs_gb": precio("storage_blob", "Cool GRS", "Cool GRS Data Stored", producto="General Block Blob v2"),
    "st_hot_lrs_esc_10k": precio("storage_blob", "Hot LRS", "Hot LRS Write Operations", producto="General Block Blob v2"),
    "st_hot_grs_esc_10k": precio("storage_blob", "Hot GRS", "Hot GRS Write Operations", producto="General Block Blob v2"),
    "st_hot_lect_10k": precio("storage_blob", "Hot LRS", "Hot Read Operations", producto="General Block Blob v2"),
    "kv_ops_10k": precio("key_vault", "Standard", "Operations", producto="Key Vault"),
    "law_ingesta_gratis": precio("log_analytics", "Analytics Logs", "Analytics Logs Data Ingestion", 0.0),
    "law_ingesta_gb": precio("log_analytics", "Analytics Logs", "Analytics Logs Data Ingestion", 5.0),
    "law_retencion_gb_mes": precio("log_analytics", "Analytics Logs", "Analytics Logs Data Retention"),
    "sentinel_gb": precio("sentinel", "Pay-as-you-go", "Pay-as-you-go Analysis"),
    "alerta_log_15min": precio("azure_monitor", "Alerts", "Alerts System Log Monitored at 15 Minute Frequency"),
    "rsv_instancia_onprem": precio("backup", "On Premises Server", "On Premises Server Protected Instance"),
    "rsv_lrs_gb": precio("backup", "Standard", "Standard LRS Data Stored"),
    "rsv_grs_gb": precio("backup", "Standard", "Standard GRS Data Stored"),
    "vpn_vpngw1az_h": precio("vpn_gateway", "VpnGw1AZ", "VpnGw1AZ"),
    "vpn_s2s_h": precio("vpn_gateway", "VpnGw1AZ", "S2S Connection"),
    "vpn_basic_h": precio("vpn_gateway", "Basic", "Basic Gateway"),
    "vpn_vpngw1_h": precio("vpn_gateway", "VpnGw1", "VpnGw1"),
    "ip_std_h": precio("ip_publica", "Standard", "Standard IPv4 Static Public IP"),
    "afw_basic_h": precio("azure_firewall", "Basic", "Basic Deployment"),
    "afw_basic_gb": precio("azure_firewall", "Basic", "Basic Data Processed"),
    "afw_std_h": precio("azure_firewall", "Standard", "Standard Deployment"),
    "afw_std_gb": precio("azure_firewall", "Standard", "Standard Data Processed"),
    "bastion_basic_h": precio("bastion", "Basic", "Basic Gateway"),
    "bastion_std_h": precio("bastion", "Standard", "Standard Gateway"),
    "agw_waf_fijo_h": precio("app_gateway", "Standard", "Standard Fixed Cost", producto="Application Gateway WAF v2"),
    "agw_waf_cu_h": precio("app_gateway", "Standard", "Standard Capacity Units", producto="Application Gateway WAF v2"),
    "def_servers_p1_h": precio("defender", "Standard P1", "Standard P1 Node", producto="Microsoft Defender for Servers"),
    "def_servers_p2_h": precio("defender", "Standard P2", "Standard P2 Node", producto="Microsoft Defender for Servers"),
    "def_storage_h": precio("defender", "Standard", "Standard Node", producto="Microsoft Defender for Storage"),
    "def_kv_h": precio("defender", "Per node Std", "Per node Std Node", producto="Microsoft Defender for Key Vault"),
    "def_arm_h": precio("defender", "Per node Std", "Per node Std Node", producto="Microsoft Defender for Resource Manager"),
    "egreso_gratis": precio("transferencia_salida", "Standard", "Standard Data Transfer Out", 0.0, producto="Rtn Preference: MGN"),
    "egreso_gb": precio("transferencia_salida", "Standard", "Standard Data Transfer Out", 100.0, producto="Rtn Preference: MGN"),
    "peering_gb": precio("vnet_peering_global", "Intra-Region", "Intra-Region Egress", regional=False),
    "arc_servidor_h": precio("azure_arc_global", "Azure Arc Enabled Servers (VMs)", "Azure Arc Enabled Servers (VMs)", regional=False),
}


def L(concepto, sku, cant, unidad_cant, clave, factor=1.0, nota=""):
    """Renglón: costo = cant x factor x precio_unitario."""
    pu, um, ref = P[clave]
    costo = None if pu is None else round(cant * factor * pu, 4)
    formula = f"{cant:g} {unidad_cant}" + (f" x {factor:g}" if factor != 1 else "") + (f" x ${pu:g}/{um}" if pu is not None else "")
    return {"concepto": concepto, "sku": sku, "cantidad": cant, "unidad": unidad_cant, "precio_unitario": pu,
            "unidad_precio": um, "formula": formula, "costo_mensual_usd": costo, "fuente": ref, "nota": nota}


def base_minima(gb_storage, horas_pe=HORAS_MES):
    return [
        L("Private Endpoint (blob + vault)", "Standard", 2 * horas_pe, "PE-hora", "pe_hora", nota="2 PE activos"),
        L("Datos procesados por PE (entrada)", "Standard", 5, "GB", "pe_gb_in"),
        L("Datos procesados por PE (salida)", "Standard", 5, "GB", "pe_gb_out"),
        L("Zonas DNS privadas", "Private Zone", 2, "zona", "dns_zona"),
        L("Consultas DNS privadas", "Private Queries", 0.1, "millón", "dns_consultas_1M"),
        L("Storage blob Hot LRS (evidencias + intercambio)", "Hot LRS", gb_storage, "GB-mes", "st_hot_lrs_gb"),
        L("Storage escrituras", "Hot LRS", 2, "x10K", "st_hot_lrs_esc_10k", nota="20 000 escrituras/mes"),
        L("Storage lecturas", "Hot LRS", 5, "x10K", "st_hot_lect_10k", nota="50 000 lecturas/mes"),
        L("Key Vault operaciones", "Standard", 5, "x10K", "kv_ops_10k", nota="50 000 operaciones/mes"),
        L("Alerta de consulta (15 min)", "Log alert", 1, "regla", "alerta_log_15min",
          nota="Interpretación: medidor 'System Log Monitored at 15 Minute Frequency'"),
        L("Peering hub-spoke (intra-región)", "Intra-Region", 2, "GB", "peering_gb", nota="Ingreso y egreso se cobran; se toma egreso"),
        L("Azure Arc: servidor habilitado (host Docker)", "Arc Enabled Servers", HORAS_MES, "h", "arc_servidor_h",
          nota="Plano de control sin costo según API; extensiones/Defender se cobran aparte"),
        L("Transferencia de salida (≤100 GB)", "MGN tramo 0", 10, "GB", "egreso_gratis"),
    ]


ESC = {
    "minimo": {
        "nombre": "Escenario 1 — Mínimo académico (environments/dev.tfvars.example)",
        "horas": "730 h/mes para recursos siempre activos",
        "lineas": base_minima(20) + [
            L("Log Analytics ingesta (tope 0.16 GB/día)", "PerGB2018 tramo 0-5 GB", 5, "GB", "law_ingesta_gratis",
              nota="Retención 30 días; franja 0-5 GB a $0 según API"),
        ],
    },
    "recomendado": {
        "nombre": "Escenario 2 — Académico recomendado (environments/demo.tfvars.example)",
        "horas": "730 h/mes siempre activos; VPN sólo 40 h/mes de ventana de demostración",
        "lineas": base_minima(50) + [
            L("Log Analytics ingesta franja gratuita", "PerGB2018 tramo 0-5 GB", 5, "GB", "law_ingesta_gratis"),
            L("Log Analytics ingesta sobre 5 GB", "PerGB2018 tramo >5 GB", 10, "GB", "law_ingesta_gb", nota="15 GB/mes (tope 0.5 GB/día)"),
            L("Log Analytics retención 90 días", "Data Retention", 30, "GB-mes", "law_retencion_gb_mes",
              nota="Supuesto: 31 días incluidos (no verificado vía API); ~2 meses de datos retenidos con cargo"),
            L("Recovery Services: servidor local (MARS)", "On Premises Server", 1, "instancia", "rsv_instancia_onprem"),
            L("Recovery Services: almacenamiento LRS", "Standard LRS", 50, "GB-mes", "rsv_lrs_gb"),
            L("Defender for Servers P1 (host Arc)", "Standard P1", HORAS_MES, "nodo-h", "def_servers_p1_h"),
            L("VPN Gateway VpnGw1AZ (ventana demo)", "VpnGw1AZ", 40, "h", "vpn_vpngw1az_h", nota="Se crea y destruye; no se puede detener"),
            L("Conexión S2S (ventana demo)", "S2S Connection", 40, "h", "vpn_s2s_h",
              nota="Conservador: la página de precios incluye túneles en el SKU (no verificado vía API)"),
            L("IP pública estándar del gateway (ventana demo)", "Standard IPv4", 40, "h", "ip_std_h"),
        ],
    },
    "institucional": {
        "nombre": "Escenario 3 — Institucional de referencia (environments/inst.tfvars.example)",
        "horas": "730 h/mes 24x7 para todos los componentes",
        "lineas": [
            L("Private Endpoint (blob + vault)", "Standard", 2 * HORAS_MES, "PE-hora", "pe_hora"),
            L("Datos procesados por PE (entrada+salida)", "Standard", 200, "GB", "pe_gb_in"),
            L("Zonas DNS privadas", "Private Zone", 2, "zona", "dns_zona"),
            L("Consultas DNS privadas", "Private Queries", 5, "millón", "dns_consultas_1M"),
            L("Storage Hot GRS", "Hot GRS", 500, "GB-mes", "st_hot_grs_gb"),
            L("Storage Cool GRS (evidencias > 30 días)", "Cool GRS", 2000, "GB-mes", "st_cool_grs_gb"),
            L("Storage escrituras", "Hot GRS", 100, "x10K", "st_hot_grs_esc_10k", nota="1 M escrituras/mes"),
            L("Storage lecturas", "Hot", 300, "x10K", "st_hot_lect_10k", nota="3 M lecturas/mes"),
            L("Key Vault operaciones", "Standard", 100, "x10K", "kv_ops_10k", nota="1 M operaciones/mes"),
            L("Log Analytics ingesta franja gratuita", "tramo 0-5 GB", 5, "GB", "law_ingesta_gratis"),
            L("Log Analytics ingesta sobre 5 GB", "tramo >5 GB", 147, "GB", "law_ingesta_gb", nota="5 GB/día ≈ 152 GB/mes"),
            L("Log Analytics retención 90 días", "Data Retention", 304, "GB-mes", "law_retencion_gb_mes", nota="Supuesto 31 días incluidos (no verificado)"),
            L("Microsoft Sentinel (pago por uso)", "Pay-as-you-go", 152, "GB", "sentinel_gb",
              nota="Supuesto: medidor de Sentinel adicional a la ingesta de LA (modelo clásico); verificar con la calculadora"),
            L("Alertas de consulta (15 min)", "Log alert", 5, "regla", "alerta_log_15min"),
            L("Recovery Services: servidores locales (MARS)", "On Premises Server", 4, "instancia", "rsv_instancia_onprem"),
            L("Recovery Services: almacenamiento GRS", "Standard GRS", 1000, "GB-mes", "rsv_grs_gb"),
            L("VPN Gateway VpnGw1AZ", "VpnGw1AZ", HORAS_MES, "h", "vpn_vpngw1az_h"),
            L("Conexión S2S", "S2S Connection", HORAS_MES, "h", "vpn_s2s_h", nota="Conservador (ver escenario 2)"),
            L("Azure Firewall Standard", "Standard", HORAS_MES, "h", "afw_std_h"),
            L("Azure Firewall datos procesados", "Standard", 500, "GB", "afw_std_gb"),
            L("Azure Bastion Basic", "Basic", HORAS_MES, "h", "bastion_basic_h"),
            L("Application Gateway WAF_v2 (fijo)", "WAF_v2", HORAS_MES, "h", "agw_waf_fijo_h"),
            L("Application Gateway WAF_v2 (unidades de capacidad)", "WAF_v2", 2 * HORAS_MES, "CU-h", "agw_waf_cu_h", nota="Promedio 2 CU"),
            L("IP públicas estándar (VPN, firewall, Bastion, App GW)", "Standard IPv4", 4 * HORAS_MES, "IP-h", "ip_std_h"),
            L("Defender for Servers P2", "Standard P2", 4 * HORAS_MES, "nodo-h", "def_servers_p2_h", nota="4 servidores (Arc o VM)"),
            L("Defender for Storage", "Standard", HORAS_MES, "cuenta-h", "def_storage_h", nota="1 cuenta; escaneo de malware aparte"),
            L("Defender for Key Vault", "Per node Std", HORAS_MES, "bóveda-h", "def_kv_h"),
            L("Defender for Resource Manager", "Per node Std", HORAS_MES, "suscripción-h", "def_arm_h"),
            L("Peering hub-spoke", "Intra-Region", 500, "GB", "peering_gb"),
            L("Transferencia de salida (primeros 100 GB)", "MGN tramo 0", 100, "GB", "egreso_gratis"),
            L("Transferencia de salida (>100 GB)", "MGN tramo 100 GB+", 200, "GB", "egreso_gb"),
        ],
    },
}

resumen = {}
for k, e in ESC.items():
    total = round(sum(l["costo_mensual_usd"] for l in e["lineas"] if l["costo_mensual_usd"] is not None), 2)
    faltan = [l["concepto"] for l in e["lineas"] if l["costo_mensual_usd"] is None]
    e["total_mensual_usd"] = total
    e["renglones_sin_precio"] = faltan
    resumen[k] = total

salida = {
    "fuente_precios": datos["fuente"],
    "consulta_utc": datos["consulta_utc"],
    "region": REGION,
    "moneda": "USD",
    "horas_mes": HORAS_MES,
    "advertencia": "Estimación con precios minoristas públicos sin impuestos, descuentos educativos ni créditos. No es una cotización.",
    "escenarios": ESC,
    "totales": resumen,
}
fecha = PRECIOS.stem.split("-")[-1] + ("" if REGION == "eastus2" else f"-{REGION}")
(EV / f"costos-escenarios-{fecha}.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")

md = [f"# Costos estimados por escenario — {REGION}", "",
      f"Fuente: API pública oficial `{datos['fuente']}` (sin autenticación), consulta **{datos['consulta_utc']}** (UTC).",
      f"Precios minoristas en USD, tipo *Consumption*, sin impuestos, descuentos ni créditos. Mes = {HORAS_MES} h.",
      "Generado por `azure/scripts/calcular_costos_escenarios.py`; datos crudos filtrados en "
      f"`evidencias/azure/{PRECIOS.name}`.", ""]
for k, e in ESC.items():
    md += [f"## {e['nombre']}", "", f"Horas supuestas: {e['horas']}.", "",
           "| Concepto | SKU / medidor | Fórmula | USD/mes | Nota |", "|---|---|---|---:|---|"]
    for l in e["lineas"]:
        c = "NO DISPONIBLE" if l["costo_mensual_usd"] is None else f"{l['costo_mensual_usd']:.2f}"
        md.append(f"| {l['concepto']} | {l['sku']} | {l['formula']} | {c} | {l['nota']} |")
    md += [f"| **Total estimado** | | | **{e['total_mensual_usd']:.2f}** | |", ""]
    if e["renglones_sin_precio"]:
        md += ["Renglones sin precio en la API (no sumados): " + "; ".join(e["renglones_sin_precio"]), ""]
md += ["## Precios unitarios usados", "", "| Clave | Precio | Unidad | Medidor (fuente) |", "|---|---:|---|---|"]
for k, (pu, um, ref) in P.items():
    md.append(f"| {k} | {'—' if pu is None else pu} | {um or '—'} | {ref} |")
(EV / f"costos-escenarios-{fecha}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
for k, v in resumen.items():
    print(f"OK {k}: USD {v:.2f}/mes")
print("Precios no encontrados:", [k for k, v in P.items() if v[0] is None] or "ninguno")
