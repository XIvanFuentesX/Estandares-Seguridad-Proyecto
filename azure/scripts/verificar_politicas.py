"""Verifica GUID, nombre y parámetros de las definiciones integradas de Azure Policy usadas por
modules/policies contra el repositorio público oficial github.com/Azure/azure-policy (sin credenciales).
Uso: python -I azure/scripts/verificar_politicas.py > evidencias/azure/politicas-integradas-verificadas-<fecha>.txt
"""
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://raw.githubusercontent.com/Azure/azure-policy/master/built-in-policies/policyDefinitions/"
ARCHIVOS = [
    "General/AllowedLocations_Deny.json",
    "Network/NetworkPublicIPNic_Deny.json",
    "Tags/RequireTag_Deny.json",
    "Storage/Storage_AuditForHTTPSEnabled_Audit.json",
    "Storage/ASC_Storage_DisallowPublicBlobAccess_Audit.json",
    "Storage/StorageAccountAllowSharedKeyAccess_Audit.json",
    "Storage/StorageAccountMinimumTLSVersion_Audit.json",
    "Storage/StoragePublicNetworkAccess_AuditDeny.json",
    "Key%20Vault/Recoverable_Audit.json",
    "Key%20Vault/PublicNetworkAccess_Audit.json",
    "Key%20Vault/Should_Use_RBAC.json",
]

codigo = (Path(__file__).resolve().parents[1] / "modules" / "policies" / "main.tf").read_text(encoding="utf-8")
usados = set(re.findall(r'"([0-9a-f-]{36})"', codigo))
print(f"Verificación de definiciones integradas — {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
print(f"Fuente: {BASE}")
print(f"GUID referenciados en modules/policies/main.tf: {len(usados)}")
encontrados = set()
for a in ARCHIVOS:
    with urllib.request.urlopen(BASE + a, timeout=30) as r:
        d = json.loads(r.read().decode("utf-8-sig"))
    p = d.get("properties", d)
    efecto = p.get("parameters", {}).get("effect", {})
    ok = d.get("name") in usados
    encontrados.add(d.get("name"))
    print(f"{'OK' if ok else 'NO-USADO'}: {d.get('name')} | {p['displayName']} | parámetros={list(p.get('parameters', {}).keys())}"
          f" | efectos={efecto.get('allowedValues')} | archivo={a}")
faltan = usados - encontrados
print("GUID sin verificar:", sorted(faltan) if faltan else "ninguno")
