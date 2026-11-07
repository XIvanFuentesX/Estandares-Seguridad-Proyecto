"""SIMULACIÓN de evaluación de cumplimiento MDM y decisión de acceso condicional.

NO es un MDM: no inscribe dispositivos, no recibe telemetría real, no aplica configuraciones ni ejecuta
borrados. Evalúa un inventario FICTICIO contra la política propuesta y produce la decisión de acceso
que una plataforma real (p. ej. Intune + Entra ID Acceso Condicional) tomaría, con el mapeo de cada
requisito a su configuración en Intune.
"""

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MDM = ROOT / "local" / "mdm"
OUT = ROOT / "evidencias" / "mdm"


def version_tuple(value):
    return tuple(int(p) for p in str(value).split("."))


def evaluate(device, policy):
    req = policy["requisitos"]
    failures = []
    if req["cifrado_disco"]["requerido"] and not device["cifrado_disco"]:
        failures.append("cifrado_disco")
    if device["bloqueo_min"] > req["bloqueo_pantalla_max_min"]["valor"]:
        failures.append("bloqueo_pantalla")
    if device["pin_longitud"] < req["pin_min_longitud"]["valor"]:
        failures.append("pin_min_longitud")
    if version_tuple(device["version"]) < version_tuple(req["so_minimo"][device["so"]]):
        failures.append("so_minimo")
    if req["antimalware_activo"]["requerido"] and not device["antimalware_activo"]:
        failures.append("antimalware_activo")
    if req["sin_root_jailbreak"]["requerido"] and device["root_jailbreak"]:
        failures.append("sin_root_jailbreak")
    if req["borrado_selectivo"]["requerido"] and not device["borrado_selectivo"]:
        failures.append("borrado_selectivo")
    if device["tipo"] == "byod" and req["perfil_trabajo_separado"]["requerido_byod"] and not device["perfil_trabajo"]:
        failures.append("perfil_trabajo_separado")
    compliant = not failures
    return {
        "id": device["id"], "propietario": device["propietario"], "tipo": device["tipo"], "so": f"{device['so']} {device['version']}",
        "conforme": compliant, "incumplimientos": failures,
        "acceso": {
            "confidencial_restringida": "permitido (MFA)" if compliant else "denegado",
            "interna": "permitido (MFA)" if compliant else "sólo navegador sin descargas (MFA)",
            "publica": "permitido",
        },
        "accion_recomendada": "ninguna" if compliant else
            ("borrado selectivo del perfil de trabajo y bloqueo" if "sin_root_jailbreak" in failures else
             f"notificar y corregir en {policy['periodo_gracia_dias']} días; bloquear al vencer"),
    }


def main():
    policy = json.loads((MDM / "politica-cumplimiento.json").read_text(encoding="utf-8"))
    devices = json.loads((MDM / "dispositivos-ficticios.json").read_text(encoding="utf-8"))["dispositivos"]
    results = [evaluate(d, policy) for d in devices]
    report = {
        "timestamp": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "naturaleza": "SIMULACIÓN con inventario ficticio; no existe plataforma MDM ni dispositivos inscritos",
        "politica": policy["nombre"], "dispositivos": len(results),
        "conformes": sum(r["conforme"] for r in results), "no_conformes": sum(not r["conforme"] for r in results),
        "resultados": results,
        "mapeo_intune": {k: v.get("intune") for k, v in policy["requisitos"].items()},
        "dependencias": ["Microsoft Intune (licencia Intune Plan 1 o M365 A3/A5)", "Entra ID P1 para Acceso Condicional",
                         "Microsoft Defender for Endpoint para riesgo del dispositivo"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    name = f"cumplimiento-mdm-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    (OUT / name).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in results:
        print(f"{r['id']} {r['tipo']:<13} {'CONFORME' if r['conforme'] else 'NO CONFORME'} {','.join(r['incumplimientos'])}")
    print(f"OK: simulacion=true conformes={report['conformes']}/{report['dispositivos']} evidencia=evidencias/mdm/{name}")


if __name__ == "__main__":
    main()
