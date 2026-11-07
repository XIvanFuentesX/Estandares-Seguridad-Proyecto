"""Resume resultados reales de seguridad sin copiar secretos ni fragmentos sensibles."""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "evidencias" / "security"


def read(name):
    path = REPORTS / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


bandit = read("bandit.json") or {}
audit = read("pip-audit.json") or {"dependencies": []}
trivy_fs = read("trivy-fs.json") or {}

bandit_results = bandit.get("results", [])
python_vulns = []
for dependency in audit.get("dependencies", []):
    for vuln in dependency.get("vulns", []):
        python_vulns.append(
            {
                "component": dependency.get("name"),
                "installed_version": dependency.get("version"),
                "id": vuln.get("id"),
                "fix_versions": vuln.get("fix_versions", []),
                "status": "pending_review",
            }
        )

misconfigurations = 0
secret_findings = 0
for result in trivy_fs.get("Results") or []:
    misconfigurations += len(result.get("Misconfigurations") or [])
    secret_findings += len(result.get("Secrets") or [])

image_summaries = {}
for name in (
    "trivy-python-image.json",
    "trivy-nginx-image.json",
    "trivy-postgres-image.json",
    "trivy-postgres-hardened-image.json",
    "trivy-keycloak-image.json",
    "trivy-keycloak-full-image.json",
):
    report = read(name)
    if report is None:
        image_summaries[name] = {"present": False}
        continue
    vulnerabilities = [
        vuln
        for result in report.get("Results", [])
        for vuln in (result.get("Vulnerabilities") or [])
    ]
    severities = Counter(v.get("Severity", "UNKNOWN") for v in vulnerabilities)
    image_summaries[name] = {
        "present": True,
        "high": severities.get("HIGH", 0),
        "critical": severities.get("CRITICAL", 0),
        "fixable": sum(bool(v.get("FixedVersion")) for v in vulnerabilities),
        # Alcance real según las clases de resultado del reporte (os-pkgs, lang-pkgs).
        "scope": sorted({result.get("Class", "unknown") for result in report.get("Results", [])}),
    }

summary = {
    "bandit_findings": len(bandit_results),
    "python_dependency_vulnerabilities": python_vulns,
    "trivy_misconfigurations": misconfigurations,
    "trivy_secret_findings": secret_findings,
    "image_reports": image_summaries,
    "notes": "Los valores de secretos y coincidencias sensibles no se copian a este resumen.",
}
(REPORTS / "registro-vulnerabilidades.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(
    "OK: bandit={} dependencias_vulnerables={} misconfig={} secretos={}".format(
        len(bandit_results), len(python_vulns), misconfigurations, secret_findings
    )
)
