"""Revisa la salida de `terraform show -json <plan>`: acciones, recursos con costo y alertas.

Uso: python -X utf8 -I azure/scripts/revisar_plan.py plan.json
Devuelve código 2 si el plan destruye o reemplaza recursos (requiere revisión reforzada).
"""
import collections
import json
import sys

CON_COSTO = {
    "azurerm_firewall": "ALTO (por hora)",
    "azurerm_application_gateway": "ALTO (por hora + CU)",
    "azurerm_virtual_network_gateway": "MEDIO (por hora; sólo se detiene eliminándolo)",
    "azurerm_bastion_host": "MEDIO (por hora; Developer no verificado)",
    "azurerm_sentinel_log_analytics_workspace_onboarding": "VARIABLE (por GB)",
    "azurerm_log_analytics_workspace": "VARIABLE (por GB > franja gratuita)",
    "azurerm_public_ip": "BAJO (por hora)",
    "azurerm_private_endpoint": "BAJO (por hora + GB)",
    "azurerm_private_dns_zone": "BAJO (por zona/mes)",
    "azurerm_storage_account": "BAJO (por GB/operación)",
    "azurerm_key_vault": "BAJO (por operación)",
    "azurerm_recovery_services_vault": "VARIABLE (por instancia + GB)",
    "azurerm_monitor_scheduled_query_rules_alert_v2": "BAJO (por regla)",
    "azurerm_security_center_subscription_pricing": "Free=0 / Standard=por recurso",
    "azurerm_virtual_network_gateway_connection": "BAJO (por hora)",
}

plan = json.load(open(sys.argv[1], encoding="utf-8-sig"))
acciones = collections.Counter()
costo = []
peligrosos = []
for rc in plan.get("resource_changes", []):
    act = "/".join(rc["change"]["actions"])
    acciones[act] += 1
    if "delete" in rc["change"]["actions"]:
        peligrosos.append(f'{act}: {rc["address"]}')
    if rc["type"] in CON_COSTO and rc["change"]["actions"] != ["no-op"]:
        extra = ""
        if rc["type"] == "azurerm_security_center_subscription_pricing":
            extra = f' tier={(rc["change"].get("after") or {}).get("tier")}'
        costo.append(f'{CON_COSTO[rc["type"]]:45} {act:8} {rc["address"]}{extra}')

print("Terraform:", plan.get("terraform_version"))
print("Acciones:", dict(acciones))
print("\nRecursos con costo potencial (comparar con evidencias/azure/costos-escenarios-*.md):")
print("\n".join(sorted(costo)) or "  (ninguno)")
if peligrosos:
    print("\nATENCIÓN — destrucciones/reemplazos (requieren autorización explícita):")
    print("\n".join(peligrosos))
    sys.exit(2)
print("\nSin destrucciones. Revise manualmente y obtenga autorización antes de cualquier apply.")
