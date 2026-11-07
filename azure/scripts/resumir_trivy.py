"""Resume los JSON de `trivy config` generados por validar_terraform.sh (conteos por severidad y ID)."""
import collections
import json
import sys
from pathlib import Path

ev = Path(sys.argv[1] if len(sys.argv) > 1 else "evidencias/azure")
archivos = [("default", ev / "trivy-config-azure.json")] + [
    (e, ev / f"trivy-config-azure-{e}.json") for e in ("dev", "demo", "inst")
]
print("\n### Resumen Trivy (estado FAIL por escenario)")
for nombre, ruta in archivos:
    if not ruta.exists():
        print(f"{nombre}: archivo no encontrado ({ruta.name})")
        continue
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    exitos = fallos = 0
    sev = collections.Counter()
    ids = collections.Counter()
    for r in datos.get("Results", []) or []:
        s = r.get("MisconfSummary", {}) or {}
        exitos += s.get("Successes", 0)
        fallos += s.get("Failures", 0)
        for m in r.get("Misconfigurations", []) or []:
            if m.get("Status") == "FAIL":
                sev[m["Severity"]] += 1
                ids[f'{m["ID"]} ({m["Severity"]}) {m["Title"]}'] += 1
    print(f"{nombre}: exitosos={exitos} fallidos={fallos} por_severidad={dict(sev)}")
    for k, v in sorted(ids.items()):
        print(f"   {v} x {k}")
