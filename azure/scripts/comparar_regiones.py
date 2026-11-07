"""Compara medidor por medidor eastus2 vs southcentralus usando el JSON de precios (sin red)."""
import collections
import json
import sys

d = json.load(open(sys.argv[1], encoding="utf-8"))
R = d["resultados"]
c = collections.Counter()
porserv = collections.defaultdict(collections.Counter)
ejemplos = []
for k in sorted({x.split("@")[0] for x in R if x.endswith("@eastus2")}):
    a = {(i["productName"], i["skuName"], i["meterName"], i["tierMinimumUnits"]): i["retailPrice"] for i in R[k + "@eastus2"]["items"]}
    b = {(i["productName"], i["skuName"], i["meterName"], i["tierMinimumUnits"]): i["retailPrice"] for i in R[k + "@southcentralus"]["items"]}
    for key in set(a) & set(b):
        r = "igual" if a[key] == b[key] else ("eastus2_menor" if a[key] < b[key] else "southcentralus_menor")
        c[r] += 1
        porserv[k][r] += 1
    c["solo_en_una_region"] += len(set(a) ^ set(b))
print(f"Consulta de precios: {d['consulta_utc']} (UTC) — fuente {d['fuente']}")
print("Totales:", dict(c))
for k, v in porserv.items():
    print(f"  {k:22} {dict(v)}")
CLAVE = [("sentinel", "Pay-as-you-go", "Pay-as-you-go Analysis"), ("app_gateway", "Standard", "Standard Fixed Cost"),
         ("vpn_gateway", "VpnGw1AZ", "VpnGw1AZ"), ("azure_firewall", "Basic", "Basic Deployment"),
         ("bastion", "Basic", "Basic Gateway"), ("log_analytics", "Analytics Logs", "Analytics Logs Data Ingestion"),
         ("backup", "On Premises Server", "On Premises Server Protected Instance")]
print("Medidores clave (eastus2 | southcentralus):")
for k, s, m in CLAVE:
    for reg in ("eastus2", "southcentralus"):
        v = [(i["productName"], i["retailPrice"], i["tierMinimumUnits"]) for i in R[f"{k}@{reg}"]["items"] if i["skuName"] == s and i["meterName"] == m]
        print(f"  {reg:15} {k}/{s}/{m}: {v}")
