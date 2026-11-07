"""Compuerta DLP de transferencia (aplicación real de la política sobre archivos del laboratorio).

Copia archivos de un origen hacia `local/dlp/salida/<canal>/` sólo si la política lo permite:
  - Restringida: bloqueada en cualquier canal no aprobado.
  - Confidencial: permitida al canal `interno`, bloqueada al `externo`.
  - Datos sensibles (DPI de 13 dígitos, tarjeta válida por Luhn): bloqueados al `externo`.
  - Credenciales/secretos asignados: bloqueados en todos los canales.
Cada bloqueo abre un incidente (gestion_sgsi) y registra `target=dlp-<canal> result=blocked` para el SIEM.
Nunca guarda el valor detectado: sólo el tipo y un prefijo de hash. No es DLP de endpoint ni de red.
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gestion_sgsi import open_incident  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTBOX = ROOT / "local" / "dlp" / "salida"
CONTROL_LOG = ROOT / "local" / "monitoring" / "controles.log"
EVIDENCE = ROOT / "evidencias" / "dlp"
LABEL = re.compile(r"CLASIFICACION\s*:\s*(PUBLICA|INTERNA|CONFIDENCIAL|RESTRINGIDA)", re.I)
DETECTORS = {
    "GT-DPI-13": re.compile(r"(?<!\d)\d{13}(?!\d)"),
    "TARJETA-PAGO": re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
    "CREDENCIAL": re.compile(r"(?i)\b(password|secret|token|api[_-]?key)\s*[:=]\s*\S+"),
}


def luhn(number):
    digits = [int(d) for d in re.sub(r"\D", "", number)][::-1]
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(digits))
    return len(digits) >= 13 and total % 10 == 0


def inspect(text):
    label = (LABEL.search(text).group(1).upper() if LABEL.search(text) else "SIN-ETIQUETA")
    found = []
    for rule, pattern in DETECTORS.items():
        for match in pattern.finditer(text):
            value = match.group(0)
            if rule == "TARJETA-PAGO" and (not luhn(value) or len(re.sub(r"\D", "", value)) == 13):
                continue  # 13 dígitos sin separadores se tratan como DPI
            found.append({"rule": rule, "value_sha256_prefix": hashlib.sha256(value.encode()).hexdigest()[:12]})
    return label, found


def decide(label, found, channel):
    rules = {f["rule"] for f in found}
    if "CREDENCIAL" in rules:
        return "blocked", "credencial o secreto en el contenido"
    if label == "RESTRINGIDA":
        return "blocked", "información restringida fuera de canal aprobado"
    if channel == "externo" and label == "CONFIDENCIAL":
        return "blocked", "información confidencial hacia canal externo"
    if channel == "externo" and rules & {"GT-DPI-13", "TARJETA-PAGO"}:
        return "blocked", "dato personal o de pago hacia canal externo"
    if label == "SIN-ETIQUETA" and channel == "externo":
        return "blocked", "archivo sin clasificar hacia canal externo"
    return "allowed", "conforme a la política de clasificación"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--canal", choices=["interno", "externo"], required=True)
    parser.add_argument("--origen", default="ejercicio", help="ejercicio (muestras sintéticas) o real-laboratorio")
    parser.add_argument("--validacion", action="store_true", help="no abre incidentes (uso en validar_sgsi.ps1)")
    parser.add_argument("--esperado", help="decisiones esperadas, p. ej. publico.txt=allowed,restringido-ficticio.txt=blocked")
    args = parser.parse_args()
    results = []
    for path in args.files:
        text = path.read_text(encoding="utf-8")
        label, found = inspect(text)
        decision, reason = decide(label, found, args.canal)
        entry = {"file": path.name, "label": label, "detections": found, "channel": args.canal, "decision": decision, "reason": reason}
        if decision == "allowed":
            destination = OUTBOX / args.canal
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination / path.name)
            entry["copied_to"] = f"local/dlp/salida/{args.canal}/{path.name}"
        elif not args.validacion:
            entry["incident"] = open_incident(f"DLP: transferencia bloqueada de {path.name} ({label}) al canal {args.canal}", "media",
                                              args.origen, evidencia="evidencias/dlp/compuerta-*.json", riesgo="R-003",
                                              contencion="Transferencia bloqueada automáticamente; archivo no copiado")
        with CONTROL_LOG.open("a", encoding="utf-8") as handle:
            handle.write(f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ} target=dlp-{args.canal} result={decision} "
                         f"file={path.name} label={label} rules={','.join(sorted({f['rule'] for f in found})) or 'none'}\n")
        results.append(entry)
        print(f"{decision.upper()}: {path.name} [{label}] -> {args.canal}: {reason}" + (f" ({entry['incident']})" if "incident" in entry else ""))
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    (EVIDENCE / f"compuerta-{args.canal}-{stamp}.json").write_text(json.dumps(
        {"timestamp": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "synthetic_data_only": args.origen == "ejercicio",
         "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.esperado:
        expected = dict(item.split("=") for item in args.esperado.split(","))
        wrong = [r["file"] for r in results if r["file"] in expected and expected[r["file"]] != r["decision"]]
        if wrong:
            print(f"ERROR: decisiones inesperadas en {wrong}")
            sys.exit(1)
        print(f"OK: decisiones_esperadas={len(expected)} canal={args.canal}")


if __name__ == "__main__":
    main()
