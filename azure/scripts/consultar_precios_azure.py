"""Consulta la API pública de precios minoristas de Azure (sin autenticación).

Uso:
    python -I azure/scripts/consultar_precios_azure.py [salida.json] [region1,region2]

Fuente: https://prices.azure.com/api/retail/prices (API oficial "Azure Retail Prices").
No usa credenciales ni crea recursos. Los precios son minoristas, en USD y sin descuentos
(EA/CSP/educación/créditos). Guarda sólo los campos relevantes de cada medidor.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://prices.azure.com/api/retail/prices"
CAMPOS = [
    "serviceName", "productName", "skuName", "meterName", "armRegionName",
    "retailPrice", "unitPrice", "unitOfMeasure", "tierMinimumUnits", "type",
    "effectiveStartDate", "currencyCode", "meterId", "isPrimaryMeterRegion",
]

# (clave, filtro OData sin la región; "{r}" se sustituye por la región)
CONSULTAS = [
    ("vpn_gateway", "serviceName eq 'VPN Gateway' and armRegionName eq '{r}'"),
    ("azure_firewall", "serviceName eq 'Azure Firewall' and armRegionName eq '{r}'"),
    ("bastion", "serviceName eq 'Azure Bastion' and armRegionName eq '{r}'"),
    ("log_analytics", "serviceName eq 'Log Analytics' and armRegionName eq '{r}'"),
    ("sentinel", "serviceName eq 'Sentinel' and armRegionName eq '{r}'"),
    ("storage_blob", "serviceName eq 'Storage' and armRegionName eq '{r}' and (productName eq 'General Block Blob v2' or productName eq 'Blob Storage')"),
    ("key_vault", "serviceName eq 'Key Vault' and armRegionName eq '{r}'"),
    ("backup", "serviceName eq 'Backup' and armRegionName eq '{r}'"),
    ("ip_publica", "serviceName eq 'Virtual Network' and armRegionName eq '{r}' and productName eq 'IP Addresses'"),
    ("transferencia_salida", "serviceName eq 'Bandwidth' and armRegionName eq '{r}'"),
    ("app_gateway", "serviceName eq 'Application Gateway' and armRegionName eq '{r}'"),
    ("defender", "serviceName eq 'Microsoft Defender for Cloud' and armRegionName eq '{r}'"),
    ("azure_monitor", "serviceName eq 'Azure Monitor' and armRegionName eq '{r}'"),
]
# Algunos medidores se publican en regiones lógicas ('Global' o 'Zone 1'), no en la región física.
CONSULTAS_GLOBALES = [
    ("private_link_global", "serviceName eq 'Virtual Network' and productName eq 'Virtual Network Private Link' and armRegionName eq 'Global'"),
    ("vnet_peering_global", "serviceName eq 'Virtual Network' and productName eq 'Virtual Network Peering' and armRegionName eq 'Global'"),
    ("dns_zona1", "serviceName eq 'Azure DNS' and armRegionName eq 'Zone 1'"),
    ("azure_arc_global", "serviceName eq 'Azure Arc' and armRegionName eq 'Global'"),
]


def consultar(filtro: str):
    url = API + "?" + urllib.parse.urlencode({"$filter": filtro, "currencyCode": "USD"})
    items, paginas = [], 0
    while url and paginas < 30:
        req = urllib.request.Request(url, headers={"User-Agent": "sgsi-uvcg-precios/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
        items.extend(data.get("Items", []))
        url = data.get("NextPageLink")
        paginas += 1
        time.sleep(0.2)
    # Sólo consumo (pago por uso); se descartan reservas y planes de ahorro.
    return [{k: i.get(k) for k in CAMPOS} for i in items if i.get("type") == "Consumption"]


def main():
    salida = sys.argv[1] if len(sys.argv) > 1 else "precios-azure.json"
    regiones = (sys.argv[2] if len(sys.argv) > 2 else "eastus2,southcentralus").split(",")
    resultado = {
        "fuente": API,
        "consulta_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "moneda": "USD",
        "tipo_precio": "Retail / Consumption (pago por uso, sin descuentos)",
        "regiones": regiones,
        "advertencia": "Precios minoristas públicos; el costo real depende del contrato, impuestos y consumo medido.",
        "resultados": {},
        "errores": {},
    }
    trabajos = [(f"{k}@{r}", f.format(r=r)) for r in regiones for k, f in CONSULTAS]
    trabajos += [(k, f) for k, f in CONSULTAS_GLOBALES]
    for clave, filtro in trabajos:
        try:
            filas = consultar(filtro)
            resultado["resultados"][clave] = {"filtro": filtro, "conteo": len(filas), "items": filas}
            print(f"OK {clave}: {len(filas)} medidores")
        except Exception as exc:  # se documenta el error, no se inventan cifras
            resultado["errores"][clave] = {"filtro": filtro, "error": repr(exc)}
            print(f"ERROR {clave}: {exc!r}")
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump(resultado, fh, ensure_ascii=False, indent=1)
    print(f"Guardado en {salida}")


if __name__ == "__main__":
    main()
