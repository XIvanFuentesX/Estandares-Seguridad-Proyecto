"""Genera inventario por escenario y diagramas Mermaid A PARTIR DEL CÓDIGO TERRAFORM.

Entradas (producidas por validar_terraform.sh en azure/scripts/salidas/):
  - verbose-<escenario>.txt : salida de `terraform test -verbose` (plan simulado con mock_provider)
  - graph.dot               : salida de `terraform graph`
  - locals.json             : valores de local.* evaluados con `terraform console`
Salidas (evidencias/azure/):
  - inventario-recursos-escenarios.md / .json
  - diagrama-dependencias.mmd (grafo real de recursos por módulo)
  - diagrama-topologia.mmd    (topología con CIDR y nombres calculados por el código)
Uso: python -I azure/scripts/generar_inventario_diagrama.py
"""
import collections
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAL = RAIZ / "azure" / "scripts" / "salidas"
EV = RAIZ / "evidencias" / "azure"

ESCENARIOS = [
    ("default", "Valores por defecto (sin costo)"),
    ("dev", "Escenario 1 — Mínimo académico (dev)"),
    ("demo", "Escenario 2 — Académico recomendado (demo)"),
    ("inst", "Escenario 3 — Institucional de referencia (inst)"),
]

# Clasificación de costo por tipo de recurso (según medidores de la API de precios; ver costos-escenarios).
COSTO = {
    "azurerm_firewall": "Por hora (alto)",
    "azurerm_application_gateway": "Por hora + unidades de capacidad",
    "azurerm_virtual_network_gateway": "Por hora",
    "azurerm_virtual_network_gateway_connection": "Por hora (S2S)",
    "azurerm_bastion_host": "Por hora (Developer: no verificado)",
    "azurerm_public_ip": "Por hora (IP estándar)",
    "azurerm_private_endpoint": "Por hora + GB procesado",
    "azurerm_private_dns_zone": "Mensual por zona + consultas",
    "azurerm_log_analytics_workspace": "Por GB ingerido (5 GB/mes sin costo según API)",
    "azurerm_sentinel_log_analytics_workspace_onboarding": "Por GB analizado",
    "azurerm_storage_account": "Por GB + operaciones",
    "azurerm_key_vault": "Por operaciones",
    "azurerm_recovery_services_vault": "Por instancia protegida + GB",
    "azurerm_monitor_scheduled_query_rules_alert_v2": "Mensual por regla",
    "azurerm_security_center_subscription_pricing": "Free = 0; Standard = por recurso/hora",
    "azurerm_virtual_network_peering": "Por GB transferido (0 sin tráfico)",
}


def recursos_plan(ruta: Path):
    """Direcciones 'will be created' del primer run (plan_simulado)."""
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    bloque = texto.split('run "valores_por_defecto_sin_costo"')[0]
    direcciones = re.findall(r"^\s+# (\S+) will be created", bloque, flags=re.M)
    m = re.search(r"^Plan: (\d+) to add", bloque, flags=re.M)
    return direcciones, (int(m.group(1)) if m else None)


def tipo_y_modulo(direccion: str):
    partes = direccion.split(".")
    modulo = partes[1] if partes[0] == "module" else "raíz"
    tipo = partes[2] if partes[0] == "module" else partes[0]
    return modulo, tipo


def inventario():
    datos, filas_md = {}, []
    for clave, titulo in ESCENARIOS:
        ruta = SAL / f"verbose-{clave}.txt"
        if not ruta.exists():
            continue
        dirs, total = recursos_plan(ruta)
        conteo = collections.Counter(tipo_y_modulo(d) for d in dirs)
        datos[clave] = {
            "titulo": titulo,
            "total_plan_simulado": total,
            "recursos": sorted(dirs),
            "por_tipo": {f"{m}/{t}": n for (m, t), n in sorted(conteo.items())},
        }
    tipos = sorted({k for d in datos.values() for k in d["por_tipo"]})
    cab = "| Módulo | Tipo de recurso | Costo | " + " | ".join(k for k, _ in ESCENARIOS if k in datos) + " |"
    sep = "|---|---|---|" + "---:|" * len(datos)
    filas_md += [cab, sep]
    for mt in tipos:
        m, t = mt.split("/")
        celdas = [str(datos[k]["por_tipo"].get(mt, 0)) for k, _ in ESCENARIOS if k in datos]
        filas_md.append(f"| {m} | `{t}` | {COSTO.get(t, 'Sin costo directo')} | " + " | ".join(celdas) + " |")
    filas_md.append("| **Total** | | | " + " | ".join(f"**{datos[k]['total_plan_simulado']}**" for k, _ in ESCENARIOS if k in datos) + " |")

    md = [
        "# Inventario de recursos proyectados por escenario",
        "",
        "Generado por `azure/scripts/generar_inventario_diagrama.py` a partir del **plan simulado** de",
        "`terraform test -verbose` con `mock_provider` (Terraform 1.14.9, AzureRM 4.81.0). El plan simulado expande",
        "módulos, `count`/`for_each`, validaciones y precondiciones con los `.tfvars.example` de cada ambiente, pero",
        "**no** consulta Azure: no valida cuotas, disponibilidad de nombres globales, permisos ni políticas reales.",
        "Estado de todos los recursos: **PREPARADO / no desplegado**.",
        "",
        "Columnas: `default` = sin `-var-file`; `dev` = Escenario 1; `demo` = Escenario 2; `inst` = Escenario 3.",
        "",
        *filas_md,
        "",
        "## Recursos con costo por escenario (direcciones exactas)",
        "",
    ]
    for k, d in datos.items():
        con_costo = [r for r in d["recursos"] if tipo_y_modulo(r)[1] in COSTO and tipo_y_modulo(r)[1] not in (
            "azurerm_virtual_network_peering", "azurerm_security_center_subscription_pricing")]
        md.append(f"### {d['titulo']} — {len(con_costo)} recursos con cargo potencial")
        md.append("")
        md += [f"- `{r}`" for r in con_costo] or ["- (ninguno)"]
        md.append("")
    (EV / "inventario-recursos-escenarios.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (EV / "inventario-recursos-escenarios.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    return datos


def diagrama_dependencias():
    dot = (SAL / "graph.dot").read_text(encoding="utf-8")
    nodos, clusters, aristas = {}, collections.defaultdict(list), []
    actual = "raiz"
    for linea in dot.splitlines():
        m = re.match(r'\s*subgraph "cluster_module\.(\S+)"', linea)
        if m:
            actual = m.group(1)
            continue
        if linea.strip() == "}":
            actual = "raiz"
        m = re.match(r'\s*"([^"]+)" \[label="([^"]+)"\];', linea)
        if m:
            nid = re.sub(r"[^A-Za-z0-9_]", "_", m.group(1))
            nodos[m.group(1)] = nid
            clusters[actual].append((nid, m.group(2)))
            continue
        m = re.match(r'\s*"([^"]+)" -> "([^"]+)";', linea)
        if m:
            aristas.append((m.group(1), m.group(2)))
    out = ["%% Generado desde `terraform graph` (recursos reales del código). Flecha: A --> B = A depende de B.",
           "flowchart LR"]
    for cl, lista in clusters.items():
        if cl != "raiz":
            out.append(f'  subgraph {cl.replace("-", "_")}["module.{cl}"]')
        for nid, etiqueta in lista:
            tipo = etiqueta.split(".")[0] if not etiqueta.startswith("data.") else "data"
            clase = ":::costo" if tipo in COSTO and tipo not in ("azurerm_virtual_network_peering",) else ""
            out.append(f'    {nid}["{etiqueta}"]{clase}')
        if cl != "raiz":
            out.append("  end")
    for a, b in aristas:
        if a in nodos and b in nodos:
            out.append(f"  {nodos[a]} --> {nodos[b]}")
    out.append("  classDef costo fill:#fde2e1,stroke:#b42318,color:#000")
    (EV / "diagrama-dependencias.mmd").write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(nodos), len(aristas)


def diagrama_topologia():
    bruto = (SAL / "locals.json").read_text(encoding="utf-8").strip().splitlines()[-1]
    loc = json.loads(json.loads(bruto))
    h, s = loc["hub"], loc["spoke"]
    n = loc["name"]
    mmd = f"""%% Topología generada con valores calculados por el código (terraform console: local.*), ambiente dev por defecto.
%% Línea discontinua = opcional/desactivado por defecto. Ningún recurso está desplegado.
flowchart LR
  subgraph LOCAL["Laboratorio local UVCG (Docker Desktop) — prefijo ficticio 192.168.50.0/24"]
    NGINX["Nginx TLS 127.0.0.1:8443 (sólo localhost)"]
    API["API Flask"]
    KC["Keycloak OIDC + MFA TOTP"]
    PG["PostgreSQL 16 x2"]
    BK["Respaldos AES-256 + SHA-256"]
    SIEM["SIEM ligero + Suricata offline"]
    ARC["Agente Azure Arc (azcmagent) — opcional"]
    VPNDEV["Router/VPN local — opcional"]
  end
  subgraph AZ["Azure eastus2 — rg-{n}"]
    subgraph HUB["vnet-{n}-hub 10.20.0.0/16"]
      GW["GatewaySubnet {h['gateway']}<br/>VPN Gateway VpnGw1AZ (opcional)"]
      FW["AzureFirewallSubnet {h['firewall']}<br/>+ Mgmt {h['firewall_mgmt']}<br/>Azure Firewall (opcional)"]
      BAS["AzureBastionSubnet {h['bastion']}<br/>Bastion (opcional)"]
      MGMT["snet-management {h['management']}"]
    end
    subgraph SPOKE["vnet-{n}-spoke-academico 10.21.0.0/16"]
      DMZ["snet-dmz {s['dmz']}<br/>App Gateway WAF_v2 (opcional)"]
      APPS["snet-apps {s['apps']}"]
      DATOS["snet-datos {s['datos']}"]
      GES["snet-gestion {s['gestion']}"]
      SEG["snet-seguridad {s['seguridad']}"]
      PE["snet-privateendpoints {s['privateendpoints']}<br/>PE blob + PE vault"]
    end
    KV["Key Vault {loc['kv']}<br/>RBAC, sin acceso público, purge protection"]
    ST["Storage {loc['st']}<br/>privado, sin shared keys, TLS 1.2, versionado"]
    LAW["Log Analytics law-{n}<br/>+ Sentinel (opcional)"]
    RSV["Recovery Services Vault (opcional)"]
    POL["Azure Policy (15 asignaciones)"]
    DEF["Defender for Cloud (Free)"]
    BUD["Presupuesto + alertas (no bloquea gasto)"]
    DNS["DNS privado: privatelink.blob / privatelink.vaultcore"]
  end
  HUB <-->|peering| SPOKE
  DMZ -->|"TCP 443"| APPS
  APPS -->|"TCP 5432"| DATOS
  APPS -->|"HTTPS 443"| PE
  PE --- KV
  PE --- ST
  DNS -.-> PE
  FW -.->|"UDR 0.0.0.0/0 y entre zonas"| SPOKE
  BAS -.->|"SSH/RDP"| GES
  VPNDEV -.->|"IPsec IKEv2 AES-256 (opcional)"| GW
  ARC -.->|"HTTPS 443 saliente + identidad administrada"| AZ
  BK -.->|"blob privado (vía VPN+PE) o MARS (vault)"| ST
  BK -.-> RSV
  KV & ST & RSV & SPOKE -.->|"diagnósticos"| LAW
"""
    (EV / "diagrama-topologia.mmd").write_text(mmd, encoding="utf-8")


if __name__ == "__main__":
    EV.mkdir(parents=True, exist_ok=True)
    d = inventario()
    nn, na = diagrama_dependencias()
    diagrama_topologia()
    for k, v in d.items():
        print(f"OK inventario {k}: {v['total_plan_simulado']} recursos en plan simulado")
    print(f"OK diagrama de dependencias: {nn} nodos, {na} aristas")
    print("OK diagrama de topología generado")
