"""Línea base SHA-256 y verificación de integridad de configuraciones del laboratorio.

--baseline registra la línea base aprobada (archiva la anterior); --verify compara y falla ante
cambios, archivos faltantes o nuevos. Excluye secretos (.env, claves TLS): sólo se verifica su
presencia, nunca se registra su hash ni su contenido.
"""

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "local"
OUT = ROOT / "evidencias" / "integridad"
BASELINE = OUT / "linea-base-configuracion.json"
PATTERNS = [
    "compose.yaml", "compose.pitr.yaml", "init.sql", ".env.example", ".gitignore",
    "nginx/*", "api/app.py", "api/Dockerfile", "api/requirements.txt", "api/.dockerignore",
    "identity/*", "backup/*", "postgres-hardened/*", "ids/rules/*", "monitoring/*",
]
SECRETS_PRESENT_ONLY = [".env", "tls/uvcg-lab.key"]
CONTROL_LOG = LOCAL / "monitoring" / "controles.log"
SELF_TEST_FILE = LOCAL / "ids" / "rules" / "uvcg.rules"  # sólo lo usa el IDS offline


def control_event(result, detail):
    with CONTROL_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ} target=config-integrity result={result} {detail}\n")


def snapshot():
    files = {}
    for pattern in PATTERNS:
        for path in sorted(LOCAL.glob(pattern)):
            if path.is_file() and path.suffix != ".log":  # bitácoras cambian por diseño
                files[path.relative_to(LOCAL).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    secrets = {name: (LOCAL / name).exists() for name in SECRETS_PRESENT_ONLY}
    return files, secrets


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--baseline", action="store_true")
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--self-test", action="store_true", help="altera y restaura un archivo no operativo para probar la detección")
    parser.add_argument("--reason", default="Línea base tras cambios aprobados del laboratorio")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now().astimezone()
    files, secrets = snapshot()

    if args.baseline:
        if BASELINE.exists():
            archive = OUT / "historico"
            archive.mkdir(exist_ok=True)
            shutil.copy2(BASELINE, archive / f"linea-base-{now.strftime('%Y%m%d-%H%M%S')}.json")
        BASELINE.write_text(json.dumps({
            "created_at": now.isoformat(timespec="seconds"), "reason": args.reason,
            "algorithm": "SHA-256", "files": files, "secrets_excluded_from_hash": SECRETS_PRESENT_ONLY,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK: linea_base_archivos={len(files)}")
        return

    if args.self_test:
        original = SELF_TEST_FILE.read_bytes()
        try:
            SELF_TEST_FILE.write_bytes(original + b"# cambio no autorizado simulado (autoprueba)\n")
            detected = subprocess.run([sys.executable, __file__, "--verify"], capture_output=True, text=True).returncode != 0
        finally:
            SELF_TEST_FILE.write_bytes(original)
        restored_ok = subprocess.run([sys.executable, __file__, "--verify"], capture_output=True, text=True).returncode == 0
        print(f"{'OK' if detected and restored_ok else 'ERROR'}: autoprueba deteccion={detected} restaurado={restored_ok}")
        sys.exit(0 if detected and restored_ok else 1)

    if not BASELINE.exists():
        raise SystemExit("ERROR: no existe línea base; ejecute --baseline tras aprobar la configuración.")
    base = json.loads(BASELINE.read_text(encoding="utf-8"))["files"]
    changed = sorted(name for name in base.keys() & files.keys() if base[name] != files[name])
    missing = sorted(base.keys() - files.keys())
    added = sorted(files.keys() - base.keys())
    absent_secrets = sorted(name for name, present in secrets.items() if not present)
    ok = not (changed or missing or added or absent_secrets)
    report = {
        "timestamp": now.isoformat(timespec="seconds"), "result": "success" if ok else "failure",
        "files_verified": len(files), "changed": changed, "missing": missing, "added": added,
        "secrets_missing": absent_secrets,
    }
    (OUT / f"verificacion-{now.strftime('%Y%m%d-%H%M%S')}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    control_event(report["result"], f"changed={','.join(changed) or 'none'} missing={','.join(missing) or 'none'} added={','.join(added) or 'none'}")
    if not ok:
        print(f"ERROR: cambiados={changed} faltantes={missing} nuevos={added} secretos_ausentes={absent_secrets}")
        sys.exit(1)
    print(f"OK: archivos_verificados={len(files)} cambios=0")


if __name__ == "__main__":
    main()
