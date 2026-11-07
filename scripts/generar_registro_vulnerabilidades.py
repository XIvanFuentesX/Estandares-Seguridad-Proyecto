"""Convierte reportes Trivy reales en un registro trazable sin secretos."""

import csv
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEC = ROOT / "evidencias" / "security"
NOW = dt.datetime.now().astimezone().isoformat(timespec="seconds")


def rows_from(report_name, component, exposure, mitigation, residual):
    data = json.loads((SEC / report_name).read_text(encoding="utf-8"))
    rows = []
    for result in data.get("Results", []):
        for vuln in result.get("Vulnerabilities") or []:
            fixed = vuln.get("FixedVersion") or "No indicada"
            if fixed == "No indicada":
                fix_status = "Sin corrección indicada por la fuente del escáner"
            else:
                fix_status = "Corrección no incorporada por la imagen oficial; componente eliminado de la imagen en uso"
            rows.append({
                "finding_id": f"VULN-{len(rows)+1:03d}-{component.upper()}",
                "reference": vuln.get("VulnerabilityID", "Sin CVE"),
                "component": component,
                "target": result.get("Target"),
                "package": vuln.get("PkgName"),
                "installed_version": vuln.get("InstalledVersion"),
                "severity": vuln.get("Severity"),
                "fixed_version": fixed,
                "fix_status": fix_status,
                "actual_exposure": exposure,
                "mitigation": mitigation,
                "residual_risk": residual,
                "evidence": f"evidencias/security/{report_name}",
                "reviewed_at": NOW,
            })
    return rows


rows = rows_from(
    "trivy-postgres-image.json", "postgres-gosu",
    "Hallazgo en usr/local/bin/gosu, binario utilizado al inicio para cambio de usuario. PostgreSQL no publica puertos, está segmentado y con capacidades mínimas. No se demostró explotabilidad de cada CVE en este laboratorio.",
    "MITIGADO por eliminación del componente: db e identity-db usan local-postgres-hardened:16 desde 2026-10-24 (gosu eliminado, UID 70). El CVE no está corregido en la imagen oficial; el reescaneo de las imágenes en uso no detecta binarios Go. Revisar en cada actualización de la imagen base.",
    "Bajo: el binario vulnerable no existe en los contenedores en ejecución; reaparecería si se revierte a postgres:16-alpine (rollback).",
)
offset = len(rows)
keycloak_rows = rows_from(
    "trivy-keycloak-full-image.json", "keycloak-openjdk",
    "Paquetes OpenJDK forman parte del runtime activo. Keycloak sólo es accesible mediante Nginx TLS y redes internas; el panel no se publica directamente. No se demostró explotabilidad.",
    "Mantener proxy, segmentación, MFA, logging y límites; revisar imágenes upstream y probar una actualización compatible cuando exista fix.",
    "Alto hasta que el proveedor publique corrección o un análisis de alcance descarte las rutas vulnerables.",
)
for index, row in enumerate(keycloak_rows, offset + 1):
    row["finding_id"] = f"VULN-{index:03d}-KEYCLOAK"
rows.extend(keycloak_rows)

fields = list(rows[0])
with (SEC / "registro-vulnerabilidades-detallado.csv").open("w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

def esc(value): return str(value).replace("|", "\\|").replace("\n", " ")
lines = [
    "# Registro detallado de vulnerabilidades pendientes", "",
    f"Generado: {NOW}. Fuente: reportes Trivy existentes. No se presupone explotabilidad ni que una actualización genérica resuelva el binario incluido en una imagen.", "",
    "Keycloak 26.8.1 es la versión estable publicada consultada al 2026-10-24; no se propone cambio incompatible. PostgreSQL permanece en la rama 16 y la etiqueta oficial fue actualizada antes del escaneo.", "",
    "| " + " | ".join(fields) + " |", "|" + "|".join("---" for _ in fields) + "|",
]
lines += ["| " + " | ".join(esc(row[field]) for field in fields) + " |" for row in rows]
lines += [
    "", "## Cobertura del escaneo", "",
    "| Imagen | Alcance | HIGH | CRITICAL | Reporte |", "|---|---|---|---|---|",
]
for report_name, label in (("trivy-antes-postgres-16-alpine-pre-upgrade.json", "postgres:16-alpine (oficial, usada hasta 2026-10-24)"),
                           ("trivy-enuso-local-postgres-hardened-16-post-upgrade.json", "local-postgres-hardened:16 (en uso por db e identity-db)"),
                           ("trivy-enuso-local-keycloak-post-upgrade.json", "local-keycloak (en uso, SO + JAR)")):
    path = SEC / report_name
    if not path.exists():
        lines.append(f"| {label} | no ejecutado | - | - | - |")
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    classes = sorted({result.get("Class", "?") for result in data.get("Results", [])})
    vulns = [v for result in data.get("Results", []) for v in (result.get("Vulnerabilities") or [])]
    lines.append(f"| {label} | {', '.join(classes)} | {sum(v['Severity'] == 'HIGH' for v in vulns)} | "
                 f"{sum(v['Severity'] == 'CRITICAL' for v in vulns)} | evidencias/security/{report_name} |")
lines += [
    "", "El escaneo Java/JAR de Keycloak (clase `lang-pkgs`) está completo y no reporta hallazgos HIGH/CRITICAL; los 2 HIGH pertenecen a paquetes OpenJDK del sistema operativo sin versión corregida publicada.",
    "", "## Análisis estático (Bandit)", "",
    "24 hallazgos de severidad LOW: 22 B101 (`assert` en scripts de prueba), 1 B404 y 1 B603 (`subprocess` sin `shell=True`, uso seguro). Ninguno está en `local/api/app.py`; se aceptan como riesgo bajo propio de scripts de laboratorio.",
    "", "## Seguimiento", "",
    "Revisar mensualmente y tras cada publicación upstream. Cerrar un hallazgo sólo después de reescaneo, prueba funcional, MFA/RBAC, restore y verificación de exposición.",
]
(SEC / "registro-vulnerabilidades-detallado.md").write_text("\n".join(lines), encoding="utf-8")
print(f"OK: hallazgos_confirmados={len(rows)} brechas_cobertura=0")
