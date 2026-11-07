"""Genera los diagramas del documento final (arquitectura híbrida objetivo y laboratorio implementado).

Uso: python documento/generar_diagramas.py  ->  documento/figuras/*.png
Convención visual: verde = implementado y probado; azul = preparado en Terraform (no desplegado);
gris punteado = diseñado (sólo documentado).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

OUT = Path(__file__).resolve().parent / "figuras"
OUT.mkdir(exist_ok=True)

IMPL = dict(fc="#DCEFD9", ec="#2E7D32", ls="-")
PREP = dict(fc="#DCE8F7", ec="#1F5FA8", ls="-")
DIS = dict(fc="#F1F1F1", ec="#6B6B6B", ls="--")
ZONE = dict(fc="none", ec="#333333", ls="-")


def box(ax, x, y, w, h, text, style, fs=7.2, bold=False, lw=1.2, round_=0.02):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.004,rounding_size={round_}",
                                fc=style["fc"], ec=style["ec"], ls=style["ls"], lw=lw))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, family="Arial",
                weight="bold" if bold else "normal")


def arrow(ax, p1, p2, text="", color="#333333", ls="-", fs=6.3, off=(0, 0.008), both=False):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="<|-|>" if both else "-|>", mutation_scale=9,
                                 color=color, lw=1.0, ls=ls, shrinkA=2, shrinkB=2))
    if text:
        ax.text((p1[0] + p2[0]) / 2 + off[0], (p1[1] + p2[1]) / 2 + off[1], text, fontsize=fs,
                ha="center", va="bottom", family="Arial", color=color,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


def label(ax, x, y, text, color="#333333", fs=5.8, ha="left"):
    ax.text(x, y, text, fontsize=fs, ha=ha, va="center", family="Arial", color=color,
            bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.95))


def zone(ax, x, y, w, h, title, style, right=False):
    box(ax, x, y, w, h, "", style, round_=0.01)
    ax.text(x + w - 0.008 if right else x + 0.008, y + h - 0.014, title, ha="right" if right else "left", va="center", fontsize=6.7, weight="bold", family="Arial")


def legend(ax, y=0.0):
    ax.legend(handles=[
        Patch(fc=IMPL["fc"], ec=IMPL["ec"], label="Implementado y probado (laboratorio local)"),
        Patch(fc=PREP["fc"], ec=PREP["ec"], label="Preparado en Terraform (AWS)"),
        Patch(fc=DIS["fc"], ec=DIS["ec"], ls="--", label="Diseñado (sólo documentado)"),
    ], loc="lower center", bbox_to_anchor=(0.5, y), ncol=3, frameon=False, prop={"family": "Arial", "size": 7})


def hibrida():
    fig, ax = plt.subplots(figsize=(11, 8.4), dpi=200)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.99, "Arquitectura híbrida objetivo — universidad ficticia UVCG (campus + AWS)",
            ha="center", va="top", fontsize=10, weight="bold", family="Arial")

    # Usuarios y dispositivos
    zone(ax, 0.01, 0.80, 0.27, 0.16, "Usuarios y dispositivos", DIS)
    box(ax, 0.018, 0.81, 0.08, 0.115, "Portátiles y PC\ninstitucionales\n(agente EDR,\ncifrado disco)", DIS, fs=5.9)
    box(ax, 0.105, 0.81, 0.08, 0.115, "Móviles y\ntabletas BYOD\n(MDM, perfil\nde trabajo)", DIS, fs=5.9)
    box(ax, 0.192, 0.81, 0.08, 0.115, "Estudiantes y\ndocentes remotos\n(navegador,\nOIDC + MFA)", DIS, fs=5.9)
    box(ax, 0.32, 0.86, 0.15, 0.075, "Internet — doble ISP\n(principal + respaldo)", DIS, fs=6.4)
    arrow(ax, (0.28, 0.89), (0.32, 0.895))
    label(ax, 0.282, 0.915, "HTTPS/TLS", fs=5.5)

    # Campus
    box(ax, 0.01, 0.04, 0.54, 0.745, "", ZONE, round_=0.01, lw=1.6)
    ax.text(0.02, 0.77, "Sitio principal: Data Center del campus (on-premises · 10.10.0.0/16)", fontsize=7.4,
            weight="bold", family="Arial")
    box(ax, 0.10, 0.665, 0.44, 0.07, "Clúster NGFW activo/pasivo + routers de borde redundantes\n"
        "(IPS en línea, filtrado de aplicaciones, terminación VPN IPsec)", DIS, fs=6.3)
    arrow(ax, (0.395, 0.86), (0.395, 0.735), both=True)

    zone(ax, 0.02, 0.50, 0.25, 0.145, "DMZ · VLAN 10 · 10.10.10.0/24", IMPL)
    box(ax, 0.03, 0.51, 0.105, 0.105, "WAF y balanceador\nHA (par\nactivo/pasivo)", DIS, fs=5.8)
    box(ax, 0.145, 0.51, 0.115, 0.105, "Proxy inverso\nNginx: TLS 1.2+,\ncabeceras, sólo\nGET/HEAD", IMPL, fs=5.8)
    zone(ax, 0.29, 0.50, 0.25, 0.145, "Monitoreo de red (SPAN)", IMPL)
    box(ax, 0.30, 0.51, 0.23, 0.105, "IDS/IPS Suricata\nlaboratorio: offline sobre PCAP\n(7 detecciones, 0 falsos positivos)", IMPL, fs=5.9)
    arrow(ax, (0.20, 0.665), (0.20, 0.615))
    arrow(ax, (0.505, 0.665), (0.505, 0.615), ls="--")

    zone(ax, 0.02, 0.32, 0.25, 0.16, "Apps · VLAN 20 · 10.10.20.0/24", IMPL)
    box(ax, 0.03, 0.33, 0.105, 0.12, "LMS, sistema\nfinanciero y\ncorreo (SaaS\nintegrados)", DIS, fs=5.8)
    box(ax, 0.145, 0.33, 0.115, 0.12, "API académica\nFlask/Gunicorn\nRBAC por ruta,\nvalida JWT", IMPL, fs=5.8)
    arrow(ax, (0.20, 0.51), (0.20, 0.45))
    label(ax, 0.207, 0.49, "TCP 8000", fs=5.4)

    zone(ax, 0.29, 0.32, 0.25, 0.16, "Identidad · VLAN 40 · 10.10.40.0/24", IMPL)
    box(ax, 0.30, 0.33, 0.115, 0.12, "Keycloak (IAM)\nOIDC, MFA TOTP\nobligatorio,\n4 roles", IMPL, fs=5.8)
    box(ax, 0.425, 0.33, 0.105, 0.12, "PostgreSQL\nde identidad\n(red interna)", IMPL, fs=5.8)
    arrow(ax, (0.26, 0.39), (0.30, 0.39), both=True)
    label(ax, 0.28, 0.41, "JWKS", fs=5.0, ha="center")

    zone(ax, 0.02, 0.15, 0.25, 0.15, "Seguridad y gestión · VLAN 50/60", IMPL)
    box(ax, 0.03, 0.16, 0.115, 0.11, "SIEM ligero\n12 fuentes,\n11 reglas, sellado\nSHA-256", IMPL, fs=5.8)
    box(ax, 0.155, 0.16, 0.105, 0.11, "Bastión de\ngestión con\nMFA (PAM)", DIS, fs=5.8)
    zone(ax, 0.29, 0.15, 0.25, 0.15, "Datos · VLAN 30 · 10.10.30.0/24", IMPL, right=True)
    box(ax, 0.30, 0.16, 0.105, 0.11, "PostgreSQL\nacadémico\n(imagen\nendurecida)", IMPL, fs=5.8)
    box(ax, 0.415, 0.16, 0.115, 0.11, "Respaldos cifrados\nAES-256 + SHA-256\ndiarios; PITR\ncon WAL", IMPL, fs=5.8)
    arrow(ax, (0.25, 0.33), (0.33, 0.27))
    label(ax, 0.27, 0.305, "TCP 5432", fs=5.4)

    box(ax, 0.02, 0.05, 0.52, 0.085, "Infraestructura base (referencia TIA-942 Rated 2): hosts de virtualización N+1 con contenedores · "
        "SAN/NAS RAID 10\nswitches core y de acceso apilados (VLAN, 802.1X) · UPS de doble conversión + generador · "
        "climatización redundante\ncontrol de acceso físico biométrico · detección temprana y extinción de incendios con agente limpio",
        DIS, fs=5.6)

    # AWS
    box(ax, 0.58, 0.04, 0.41, 0.92, "", ZONE, round_=0.01, lw=1.6)
    ax.text(0.59, 0.945, "Nube pública AWS — región us-east-1", fontsize=7.6, weight="bold", family="Arial")
    box(ax, 0.595, 0.80, 0.185, 0.12, "IAM: roles de mínimo\nprivilegio (uploader y\nauditor) asumidos con\ncredenciales temporales STS", PREP, fs=5.9)
    box(ax, 0.79, 0.80, 0.19, 0.12, "Guardrails: AWS Budgets\n(gasto cero) e historial\nde CloudTrail (90 días)", PREP, fs=5.9)
    arrow(ax, (0.47, 0.90), (0.595, 0.88), color="#1F5FA8")
    label(ax, 0.533, 0.915, "consola/CLI con MFA", color="#1F5FA8", fs=5.4, ha="center")

    box(ax, 0.595, 0.36, 0.385, 0.42, "", DIS, round_=0.01)
    ax.text(0.7875, 0.765, "VPC 10.30.0.0/16 — dos zonas de disponibilidad (diseño de DR)", ha="center", va="center",
            fontsize=6.6, weight="bold", family="Arial")
    for i, az in enumerate(["us-east-1a", "us-east-1b"]):
        x0 = 0.605 + i * 0.19
        ax.text(x0 + 0.0875, 0.74, az, ha="center", fontsize=6.0, family="Arial", style="italic")
        box(ax, x0, 0.635, 0.175, 0.09, f"Subred pública 10.30.{i}.0/24\nALB + AWS WAF", DIS, fs=5.8)
        box(ax, x0, 0.505, 0.175, 0.115, f"Subred apps 10.30.{10 + i}.0/24\nréplica DR de la API\n(ECS/EC2, Auto Scaling)", DIS, fs=5.8)
        box(ax, x0, 0.375, 0.175, 0.115, f"Subred datos 10.30.{20 + i}.0/24\nRDS PostgreSQL Multi-AZ\n(cifrado con KMS)", DIS, fs=5.8)

    box(ax, 0.595, 0.215, 0.385, 0.125, "Servicios regionales de seguridad: GuardDuty · Security Hub · AWS Config\n"
        "VPC Flow Logs · CloudWatch · KMS · Secrets Manager · IAM Identity Center (MFA)\n"
        "Grupos de seguridad + NACL por subred; sin IP públicas en apps y datos;\nhallazgos exportados al SIEM institucional",
        DIS, fs=5.8)
    box(ax, 0.595, 0.055, 0.185, 0.14, "Amazon S3 privado\nSSE-S3 (AES-256), sólo\nTLS ≥ 1.2, bloqueo de\nacceso público,\nexpiración 30 días", PREP, fs=5.8)
    box(ax, 0.79, 0.055, 0.19, 0.14, "Copia offsite inmutable\nS3 Object Lock +\nAWS Backup\n(retención WORM)", DIS, fs=5.8)

    # Enlaces híbridos (sólo cruzan el pasillo entre ambos sitios)
    arrow(ax, (0.54, 0.70), (0.605, 0.68), ls="--", color="#6B6B6B")
    label(ax, 0.563, 0.745, "Site-to-Site\nVPN IPsec\n(2 túneles)", color="#555555", fs=5.2, ha="center")
    arrow(ax, (0.53, 0.20), (0.595, 0.13), color="#1F5FA8")
    label(ax, 0.563, 0.245, "copia\ncifrada\nHTTPS+STS", color="#1F5FA8", fs=5.2, ha="center")
    legend(ax, y=-0.01)
    fig.savefig(OUT / "arquitectura-hibrida.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def laboratorio():
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=200)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.985, "Laboratorio implementado — Docker Desktop (host Windows 11, WSL2)", ha="center", va="top",
            fontsize=10, weight="bold", family="Arial")
    box(ax, 0.01, 0.80, 0.16, 0.12, "Navegador / scripts\nde prueba\n127.0.0.1:8080 → 301\n127.0.0.1:8443 (TLS)", IMPL, fs=6.6)

    box(ax, 0.20, 0.72, 0.30, 0.22, "", IMPL, round_=0.01)
    ax.text(0.35, 0.92, "Red dmz · 172.23.0.0/16 (no interna)", ha="center", fontsize=7, weight="bold", family="Arial")
    box(ax, 0.22, 0.74, 0.12, 0.15, "proxy (Nginx)\nTLS 1.2/1.3\nsólo GET/HEAD\npuertos sólo\nen loopback", IMPL, fs=6.2)
    box(ax, 0.36, 0.74, 0.12, 0.15, "uptime-monitor\nsondeo cada\n15 s", IMPL, fs=6.2)
    arrow(ax, (0.17, 0.86), (0.22, 0.83))

    box(ax, 0.20, 0.42, 0.42, 0.25, "", IMPL, round_=0.01)
    ax.text(0.41, 0.65, "Red apps · 172.24.0.0/16 (interna)", ha="center", fontsize=7, weight="bold", family="Arial")
    box(ax, 0.22, 0.44, 0.17, 0.18, "api (Flask/Gunicorn)\nvalida firma JWKS,\nemisor, expiración,\nMFA y rol", IMPL, fs=6.2)
    box(ax, 0.43, 0.44, 0.17, 0.18, "keycloak 26.8.1\nrealm uvcg: OIDC,\nTOTP obligatorio,\npolítica de contraseña", IMPL, fs=6.2)
    arrow(ax, (0.28, 0.74), (0.30, 0.62), "/ → api:8000", fs=6)
    arrow(ax, (0.32, 0.74), (0.50, 0.62), "/auth → keycloak:8080", fs=6, off=(0.04, 0.0))

    box(ax, 0.20, 0.08, 0.20, 0.30, "", IMPL, round_=0.01)
    ax.text(0.30, 0.36, "Red datos · 172.25.0.0/16 (interna)", ha="center", fontsize=6.8, weight="bold", family="Arial")
    box(ax, 0.215, 0.20, 0.17, 0.13, "db: PostgreSQL 16\nendurecido (sin gosu,\nUID 70, sólo lectura)", IMPL, fs=6.1)
    box(ax, 0.215, 0.095, 0.17, 0.09, "academic-backup-\nscheduler (diario)", IMPL, fs=6.1)
    arrow(ax, (0.30, 0.44), (0.30, 0.33), "5432", fs=6, off=(0.02, -0.01))

    box(ax, 0.43, 0.08, 0.20, 0.30, "", IMPL, round_=0.01)
    ax.text(0.53, 0.36, "Red identity · 172.26.0.0/16 (interna)", ha="center", fontsize=6.8, weight="bold", family="Arial")
    box(ax, 0.445, 0.20, 0.17, 0.13, "identity-db:\nPostgreSQL 16\nendurecido", IMPL, fs=6.1)
    box(ax, 0.445, 0.095, 0.17, 0.09, "identity-backup-\nscheduler (diario)", IMPL, fs=6.1)
    arrow(ax, (0.515, 0.44), (0.53, 0.33), "5432", fs=6, off=(0.02, -0.01))

    box(ax, 0.67, 0.42, 0.32, 0.50, "", IMPL, round_=0.01)
    ax.text(0.83, 0.90, "Perfiles bajo demanda", ha="center", fontsize=7, weight="bold", family="Arial")
    box(ax, 0.685, 0.74, 0.29, 0.13, "Red recovery · 172.27.0.0/16 (interna)\nrestore-db, identity-restore-db, réplicas PITR\n(nunca restaura sobre la base activa)", IMPL, fs=6.1)
    box(ax, 0.685, 0.59, 0.29, 0.13, "ids: Suricata 7.0 (network_mode: none)\nPCAP sintético: 7 detecciones, 0 falsos positivos", IMPL, fs=6.1)
    box(ax, 0.685, 0.44, 0.29, 0.13, "security: Trivy, Bandit, pip-audit\nescaneo de imágenes en uso", IMPL, fs=6.1)

    box(ax, 0.67, 0.08, 0.32, 0.30, "", IMPL, round_=0.01)
    ax.text(0.83, 0.36, "Host (scripts Python/PowerShell)", ha="center", fontsize=7, weight="bold", family="Arial")
    box(ax, 0.685, 0.10, 0.29, 0.24, "SIEM ligero (SQLite, sellado encadenado)\nvigilancia de contenedores (EDR demostrativo)\n"
        "compuerta DLP · simulación MDM\nlínea base de integridad SHA-256\nregistro operativo (INC/CHG/ACC/AST)\n"
        "tarea programada de recuperación semanal", IMPL, fs=6.1)
    ax.text(0.01, 0.03, "Todos los servicios: read_only, cap_drop ALL, no-new-privileges, usuario no root, límites de memoria. "
            "Sólo el proxy publica puertos y únicamente en 127.0.0.1.", fontsize=6.6, family="Arial", style="italic")
    fig.savefig(OUT / "laboratorio-implementado.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    hibrida()
    laboratorio()
    print("OK:", ", ".join(p.name for p in sorted(OUT.glob("*.png"))))
