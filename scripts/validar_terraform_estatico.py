"""Verificacion ESTATICA de la estructura modular Terraform de Azure.

No equivale a `terraform validate`, a `terraform plan` ni a un despliegue: solo revisa texto.
La validacion completa (fmt, validate, test con mock, tflint, trivy) esta en
azure/scripts/validar_terraform.sh. Imprime lineas `OK: ...`/`ERROR: ...` y termina con
codigo 0 solo si todas las comprobaciones pasan (lo usa scripts/validar_sgsi.ps1).
"""
import re
import sys
from pathlib import Path

AZ = Path(__file__).resolve().parents[1] / "azure"
MODULOS = ["networking", "identity", "security", "monitoring", "storage", "backup", "hybrid-connectivity", "policies"]


def leer(rel):
    p = AZ / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def todo_tf():
    return "\n".join(p.read_text(encoding="utf-8") for p in AZ.rglob("*.tf") if ".terraform" not in p.parts)


raiz_vars = leer("variables.tf")
raiz_main = leer("main.tf")
locs = leer("locals.tf")
net = leer("modules/networking/main.tf")
sec = leer("modules/security/main.tf")
sto = leer("modules/storage/main.tf")
mon = leer("modules/monitoring/main.tf")
pol = leer("modules/policies/main.tf")
idn = leer("modules/identity/main.tf")
hyb = leer("modules/hybrid-connectivity/main.tf")
bkp = leer("modules/backup/main.tf")
versiones = leer("versions.tf")
backend = leer("backend.tf")
lock = leer(".terraform.lock.hcl")
tf = todo_tf()


def default_false(nombre):
    m = re.search(r'variable "%s" \{(.*?)\n\}' % re.escape(nombre), raiz_vars, flags=re.S)
    return bool(m) and re.search(r"default\s*=\s*false", m.group(1)) is not None


COSTOSAS = ["enable_monitoring", "enable_sentinel", "enable_alerts", "enable_key_vault", "enable_storage",
            "enable_private_endpoints", "enable_backup", "enable_vpn_gateway", "enable_firewall",
            "enable_bastion", "enable_app_gateway"]

archivos_estado = [p for p in AZ.rglob("*") if p.is_file() and ".terraform" not in p.parts and
                   (p.suffix == ".tfstate" or p.name.endswith(".tfstate.backup") or
                    (p.suffix == ".tfvars") or p.name.endswith(".tfvars.json"))]

checks = {
    "modulos presentes (8)": all((AZ / "modules" / m / "main.tf").exists() for m in MODULOS),
    "raiz con variables, outputs, locals, versions y providers": all(
        (AZ / f).exists() for f in ["variables.tf", "outputs.tf", "locals.tf", "versions.tf", "providers.tf", "main.tf"]),
    "proveedor azurerm 4.x compatible con lock 4.81.0": '"~> 4.0"' in versiones and 'version     = "4.81.0"' in lock,
    "region restringida por validacion": 'contains(["eastus2", "southcentralus"], var.location)' in raiz_vars,
    "ambientes dev/demo/inst de ejemplo": all((AZ / "environments" / f"{e}.tfvars.example").exists() for e in ["dev", "demo", "inst"]),
    "cinco zonas spoke + endpoints privados": all(f"{z} " in locs or f"{z}=" in locs.replace(" ", "")
                                                 for z in ["dmz", "apps", "datos", "gestion", "seguridad", "privateendpoints"]),
    "topologia hub-spoke": 'azurerm_virtual_network" "hub' in net and 'azurerm_virtual_network" "spoke' in net,
    "peering bidireccional": "hub_to_spoke" in net and "spoke_to_hub" in net,
    "NSG vinculados a subredes": "azurerm_subnet_network_security_group_association" in net,
    "bloqueo de trafico lateral (deny 4096)": "denegar-resto-entrante" in net and "priority                    = 4096" in net,
    "UDR hacia Azure Firewall": "VirtualAppliance" in net and "firewall_private_ip" in net,
    "DNS privado blob y vault": "privatelink.blob.core.windows.net" in net and "privatelink.vaultcore.azure.net" in net,
    "Key Vault RBAC, privado y purge protection": all(s in sec for s in [
        "rbac_authorization_enabled    = true", "public_network_access_enabled = false", "purge_protection_enabled      = true"]),
    "Storage privado, sin anonimo, TLS1.2, sin shared keys, versionado": all(s in sto for s in [
        "public_network_access_enabled     = false", "allow_nested_items_to_be_public   = false",
        'min_tls_version                   = "TLS1_2"', "shared_access_key_enabled         = false",
        "versioning_enabled            = true", "delete_retention_policy"]),
    "endpoints privados (blob y vault)": 'subresource_names              = ["blob"]' in sto and 'subresource_names              = ["vault"]' in sec,
    "identidades administradas": "azurerm_user_assigned_identity" in idn,
    "RBAC con separacion de funciones": "sod_matrix" in idn and "setintersection" in raiz_vars,
    "roles privilegiados bloqueados": '"Owner", "Contributor", "User Access Administrator"' in raiz_vars,
    "Azure Policy (ubicaciones, NIC sin IP publica, etiquetas, storage)": all(g in pol for g in [
        "e56962a6-4747-49cd-b67b-bf8b01975c4c", "83a86a26-fd1f-447c-b59d-e51f44264114",
        "871b6d14-10aa-478d-b590-94f262ecfa99", "404c3081-a854-4457-ae30-26a93ef643f9"]),
    "Defender for Cloud Free por defecto": 'VirtualMachines = "Free"' in raiz_vars and "azurerm_security_center_subscription_pricing" in sec,
    "firewall, bastion y WAF opcionales": all(r in sec for r in ["azurerm_firewall\"", "azurerm_bastion_host", "azurerm_application_gateway"]),
    "Log Analytics, actividad, alertas y action group": all(r in mon for r in [
        "azurerm_log_analytics_workspace", "activity_log", "azurerm_monitor_action_group", "azurerm_monitor_activity_log_alert"]),
    "Sentinel opcional": "azurerm_sentinel_log_analytics_workspace_onboarding" in mon,
    "presupuesto con alertas": "azurerm_consumption_budget_resource_group" in mon,
    "diagnostic settings": tf.count("azurerm_monitor_diagnostic_setting") >= 6,
    "Recovery Services Vault opcional": "azurerm_recovery_services_vault" in bkp,
    "VPN S2S opcional con IPsec explicito": "azurerm_virtual_network_gateway_connection" in hyb and "AES256" in hyb,
    "Azure Arc (alternativa de bajo costo)": "Azure Connected Machine Onboarding" in hyb,
    "funciones con costo apagadas por defecto": all(default_false(v) for v in COSTOSAS),
    "backend remoto solo documentado (comentado)": "backend \"azurerm\"" in backend and not re.search(r'^\s*backend\s+"azurerm"', backend, flags=re.M),
    "sin estado ni tfvars reales en el repositorio": not archivos_estado,
    "sin claves IPsec ni secretos literales": not re.search(r'shared_key\s*=\s*"', tf) and "client_secret" not in tf,
}
for k, v in checks.items():
    print(("OK" if v else "ERROR") + ": " + k)
if archivos_estado:
    print("Archivos prohibidos:", [str(p.relative_to(AZ)) for p in archivos_estado])
sys.exit(0 if all(checks.values()) else 1)
