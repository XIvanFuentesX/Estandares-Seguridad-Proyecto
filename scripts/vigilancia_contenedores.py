"""Vigilancia de contenedores sin agentes ni privilegios (demostración tipo EDR, NO es un EDR).

- Procesos: `docker top` frente a una lista de procesos permitidos por servicio (línea base aprobada).
- Deriva de archivos: `docker diff` (con raíz de sólo lectura no debería haber cambios fuera de tmpfs/volúmenes).
- Endurecimiento: `docker inspect` (raíz de sólo lectura, usuario no root, cap_drop ALL, no-new-privileges,
  sin modo privilegiado, sólo el proxy publica puertos y únicamente en 127.0.0.1, límite de memoria).
Cada hallazgo genera `target=edr-<servicio> result=failure` en local/monitoring/controles.log (regla SIEM-EDR-001).
Uso: --baseline (registra procesos actuales como permitidos) | --check
"""

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = ROOT / "local" / "monitoring" / "procesos-permitidos.json"
CONTROL_LOG = ROOT / "local" / "monitoring" / "controles.log"
OUT = ROOT / "evidencias" / "edr"
SERVICES = {"proxy": "local-proxy-1", "api": "local-api-1", "keycloak": "local-keycloak-1", "db": "local-db-1", "identity-db": "local-identity-db-1"}
EXPECTED_USER = {"proxy": "101:101", "api": "app", "keycloak": "1000", "db": "70:70", "identity-db": "70:70"}


def docker(*args):
    proc = subprocess.run(["docker", *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip()[-300:])
    return proc.stdout


def processes(container):
    lines = docker("top", container).splitlines()[1:]
    names = set()
    for line in lines:
        cmd = line.split(None, 7)[-1]
        exe = cmd.split()[0].rsplit("/", 1)[-1]
        names.add(exe.rstrip(":"))
    return sorted(names)


def hardening(service, container):
    info = json.loads(docker("inspect", container))[0]
    host = info["HostConfig"]
    ports = [(b.get("HostIp"), b.get("HostPort")) for bindings in (host.get("PortBindings") or {}).values() for b in bindings or []]
    checks = {
        "read_only_rootfs": host.get("ReadonlyRootfs") is True,
        "non_root_user": info["Config"].get("User") not in ("", "0", "root", None),
        "expected_user": info["Config"].get("User") == EXPECTED_USER[service],
        "cap_drop_all": "ALL" in (host.get("CapDrop") or []),
        "no_new_privileges": any("no-new-privileges" in opt for opt in host.get("SecurityOpt") or []),
        "not_privileged": host.get("Privileged") is False,
        "ports_only_loopback": all(ip == "127.0.0.1" for ip, _ in ports) and (service == "proxy" or not ports),
        "no_host_network": host.get("NetworkMode") != "host",
    }
    if service in ("api", "keycloak", "db", "identity-db"):
        checks["memory_limit"] = (host.get("Memory") or 0) > 0
    return checks


def emit(service, result, detail):
    with CONTROL_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ} target=edr-{service} result={result} {detail}\n")


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--baseline", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--label", default="")
    args = parser.parse_args()
    if args.baseline:
        data = {"created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                "note": "Procesos observados en estado sano tras validación; cambios requieren gestión de cambios.",
                "allowed": {service: processes(container) for service, container in SERVICES.items()}}
        ALLOWED.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("OK: linea_base_procesos=" + ", ".join(f"{k}:{'/'.join(v)}" for k, v in data["allowed"].items()))
        return
    allowed = json.loads(ALLOWED.read_text(encoding="utf-8"))["allowed"]
    report = {"timestamp": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "label": args.label, "services": {}}
    findings = 0
    for service, container in SERVICES.items():
        procs = processes(container)
        unexpected = sorted(set(procs) - set(allowed.get(service, [])))
        info = json.loads(docker("inspect", container))[0]
        mounts = [m["Destination"] for m in info.get("Mounts", [])] + list((info["HostConfig"].get("Tmpfs") or {}).keys())
        # Docker crea los puntos de montaje (y sus padres) en la capa del contenedor: no son deriva.
        drift = [line for line in docker("diff", container).splitlines()
                 if line.strip() and not any(m == line[2:] or m.startswith(line[2:].rstrip("/") + "/") for m in mounts)]
        hard = hardening(service, container)
        failed_hardening = [name for name, ok in hard.items() if not ok]
        issues = [f"proceso_inesperado:{p}" for p in unexpected] + [f"deriva:{d}" for d in drift[:10]] + [f"endurecimiento:{h}" for h in failed_hardening]
        findings += len(issues)
        report["services"][service] = {"processes": procs, "unexpected_processes": unexpected, "filesystem_drift": drift,
                                       "hardening": hard, "issues": issues, "result": "failure" if issues else "success"}
        emit(service, "failure" if issues else "success", ("issues=" + ",".join(issues)) if issues else "issues=none")
    report["result"] = "failure" if findings else "success"
    OUT.mkdir(parents=True, exist_ok=True)
    name = f"vigilancia-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}{'-' + args.label if args.label else ''}.json"
    (OUT / name).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{'OK' if not findings else 'ALERTA'}: servicios={len(SERVICES)} hallazgos={findings} evidencia=evidencias/edr/{name}")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
