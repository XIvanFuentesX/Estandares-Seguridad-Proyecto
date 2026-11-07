"""Valida la trazabilidad entre inventario, BIA, riesgos, matriz de calor, tratamiento, SoA y evidencias."""

import csv
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOV = ROOT / "governance"
OUT = ROOT / "evidencias" / "gobernanza"


def load(name):
    with (GOV / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def split_ids(value):
    return [item.strip() for item in re.split(r"[;,]", value) if item.strip()]


def level(score):
    return "Bajo" if score <= 4 else "Moderado" if score <= 9 else "Alto" if score <= 15 else "Crítico"


def evidence_exists(reference):
    path = reference.split("#")[0].strip()
    if not path or " " in path:
        return True  # texto descriptivo, no ruta
    return any(ROOT.glob(path)) if "*" in path else (ROOT / path).exists()


assets, bia, risks = load("inventario-activos.csv"), load("bia.csv"), load("matriz-riesgos.csv")
treatment, soa = load("plan-tratamiento.csv"), load("declaracion-aplicabilidad.csv")
heat = (GOV / "matriz-calor.md").read_text(encoding="utf-8")
asset_ids, process_ids = {a["id"] for a in assets}, {p["id"] for p in bia}
risk_ids, control_ids = {r["id"] for r in risks}, {c["control_id"] for c in soa}
checks = []


def check(name, ok, detail=""):
    checks.append({"check": name, "result": "success" if ok else "failure", "detail": detail})


for label, rows in (("activos", assets), ("procesos", bia), ("riesgos", risks), ("controles", soa)):
    ids = [row.get("id") or row.get("control_id") for row in rows]
    check(f"ids_unicos_{label}", len(ids) == len(set(ids)), f"{len(ids)} registros")

bad = [p["id"] for p in bia if not (float(p["rpo_horas"]) <= float(p["rto_horas"]) < float(p["mtpd_horas"]))]
check("bia_rpo_rto_mtpd", not bad, f"incoherentes={bad}")
bad = [p["id"] for p in bia if not set(split_ids(p["activos"])) <= asset_ids]
check("bia_activos_en_inventario", not bad, f"con_activos_inexistentes={bad}")

bad = [r["id"] for r in risks if not set(split_ids(r["activo"])) <= asset_ids]
check("riesgos_activos_en_inventario", not bad, f"{bad}")
bad = [r["id"] for r in risks if r["proceso"] != "Todos" and not set(split_ids(r["proceso"])) <= process_ids]
check("riesgos_procesos_en_bia", not bad, f"{bad}")
bad = [r["id"] for r in risks if int(r["riesgo_inherente"]) != int(r["probabilidad_1_5"]) * int(r["impacto_1_5"])
       or int(r["riesgo_residual"]) != int(r["probabilidad_residual_1_5"]) * int(r["impacto_residual_1_5"])
       or r["nivel_inherente"] != level(int(r["riesgo_inherente"])) or r["nivel_residual"] != level(int(r["riesgo_residual"]))]
check("riesgos_calculo_y_nivel", not bad, f"{bad}")
bad = [r["id"] for r in risks if int(r["riesgo_residual"]) > int(r["riesgo_inherente"])]
check("residual_no_mayor_que_inherente", not bad, f"{bad}")
known = {"vulnerabilidades PostgreSQL": "R-009", "vulnerabilidades Keycloak": "R-010", "fallos de autenticación": "R-002",
         "acceso no autorizado": "R-001", "exposición de información": "R-003", "interrupción de servicios": "R-004",
         "pérdida de datos": "R-005", "fallo de respaldos": "R-007", "configuración insegura": "R-008",
         "dependencia del equipo local": "R-011", "ausencia de despliegue híbrido": "R-017"}
check("riesgos_conocidos_cubiertos", set(known.values()) <= risk_ids, json.dumps(known, ensure_ascii=False))

in_heat = set(re.findall(r"R-\d{3}", heat))
check("matriz_calor_contiene_todos", in_heat == risk_ids, f"faltan={sorted(risk_ids - in_heat)} sobran={sorted(in_heat - risk_ids)}")
check("matriz_calor_dos_vistas", heat.count("R-001") == 2, "inherente y residual")

treated = {t["riesgo_id"] for t in treatment}
check("tratamiento_cubre_riesgos", treated == risk_ids, f"sin_tratamiento={sorted(risk_ids - treated)}")
bad = sorted({ref for t in treatment for ref in split_ids(t["referencia_iso_27001_27002_2022"]) if ref not in control_ids})
check("tratamiento_controles_en_soa", not bad, f"inexistentes={bad}")
check("estrategias_validas", all(any(s in t["estrategia"] for s in ("Mitigar", "Aceptar", "Evitar", "Transferir")) for t in treatment))

check("soa_93_controles", len(soa) == 93, f"{len(soa)}")
check("soa_formato_ids", all(re.fullmatch(r"A\.[5-8]\.\d{1,2}", c["control_id"]) for c in soa))
bad = sorted({rid for c in soa for rid in split_ids(c["related_risks"]) if rid.startswith("R-") and rid not in risk_ids})
check("soa_riesgos_existentes", not bad, f"{bad}")
implemented = [c for c in soa if c["implementation_status"].startswith("Implementado")]
bad = [c["control_id"] for c in implemented if c["evidence"].startswith("Sin evidencia")]
check("soa_implementados_con_evidencia", not bad, f"{bad}")

missing = []
for label, rows, field in (("riesgo", risks, "evidencia"), ("tratamiento", treatment, "evidencia"), ("soa", implemented, "evidence")):
    for row in rows:
        for ref in split_ids(row[field]):
            if not evidence_exists(ref):
                missing.append(f"{label}:{row.get('id') or row.get('riesgo_id') or row.get('control_id')}:{ref}")
check("evidencias_referenciadas_existen", not missing, f"faltantes={missing}")

now = dt.datetime.now().astimezone()
OUT.mkdir(parents=True, exist_ok=True)
failed = [c["check"] for c in checks if c["result"] != "success"]
report = {"timestamp": now.isoformat(timespec="seconds"), "result": "failure" if failed else "success",
          "counts": {"activos": len(assets), "procesos": len(bia), "riesgos": len(risks), "tratamientos": len(treatment), "controles_soa": len(soa)},
          "checks": checks}
(OUT / f"trazabilidad-{now.strftime('%Y%m%d-%H%M%S')}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
if failed:
    raise SystemExit(f"ERROR: verificaciones fallidas={failed}; " + "; ".join(c["detail"] for c in checks if c["result"] != "success"))
print(f"OK: verificaciones={len(checks)} fallidas=0 riesgos={len(risks)} controles={len(soa)}")
