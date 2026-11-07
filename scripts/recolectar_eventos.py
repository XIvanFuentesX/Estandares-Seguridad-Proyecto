"""Recolector y correlador ligero de logs Docker para el laboratorio UVCG."""

import argparse
import datetime as dt
import html
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "local"
OUTPUT = ROOT / "evidencias" / "monitoring"

REDACTIONS = [
    (re.compile(r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9._~-]+"), r"\1[REDACTED]"),
    (re.compile(r'(?i)("(?:access_token|refresh_token|password)"\s*:\s*")[^"]+'), r"\1[REDACTED]"),
]

RULES = [
    ("AUTH-DENIED", "media", re.compile(r'"event":\s*"auth(?:entication|orization)".*"outcome":\s*"denied"')),
    ("HTTP-DENIED", "baja", re.compile(r'"(?:POST|PUT|PATCH|DELETE|OPTIONS|GET) [^\"]+ HTTP/[^\"]+" (?:401|403) ')),
    ("DB-AUTH-FAIL", "alta", re.compile(r"password authentication failed", re.I)),
    ("KEYCLOAK-LOGIN-ERROR", "media", re.compile(r"LOGIN_ERROR")),
    ("SERVICE-ERROR", "media", re.compile(r"\b(?:Traceback|unhealthy|ERROR|FATAL)\b")),
]


def redact(value):
    for pattern, replacement in REDACTIONS:
        value = pattern.sub(replacement, value)
    return value


def run_logs(since):
    command = [
        "docker", "compose", "-f", "compose.yaml", "logs", "--no-color",
        "--timestamps", f"--since={since}", "db", "api", "proxy", "keycloak", "identity-db",
    ]
    result = subprocess.run(command, cwd=LOCAL, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError("No se pudieron recolectar logs Docker: " + redact(result.stderr.strip()))
    return redact(result.stdout)


def correlate(lines):
    alerts = []
    for number, line in enumerate(lines, 1):
        for rule_id, severity, pattern in RULES:
            if pattern.search(line):
                alerts.append(
                    {
                        "rule_id": rule_id,
                        "severity": severity,
                        "line": number,
                        "event": line[:500],
                    }
                )
    return alerts


def render_dashboard(timestamp, lines, alerts):
    counts = Counter(alert["rule_id"] for alert in alerts)
    rows = "".join(
        f"<tr><td>{html.escape(key)}</td><td>{value}</td></tr>"
        for key, value in sorted(counts.items())
    ) or "<tr><td>Sin alertas</td><td>0</td></tr>"
    recent = "\n".join(lines[-100:])
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Monitoreo SGSI UVCG</title>
<style>body{{font-family:system-ui;margin:2rem;background:#101820;color:#eef}}
table{{border-collapse:collapse}}td,th{{border:1px solid #667;padding:.5rem}}
pre{{white-space:pre-wrap;background:#172431;padding:1rem;max-height:40rem;overflow:auto}}</style></head>
<body><h1>Tablero ligero de eventos UVCG</h1>
<p>Generado: {html.escape(timestamp)}. Fuente: logs reales del laboratorio Docker.</p>
<p>Esto es correlación demostrativa; no sustituye un SIEM empresarial.</p>
<table><thead><tr><th>Regla</th><th>Coincidencias</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Últimos eventos saneados</h2><pre>{html.escape(recent)}</pre></body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default="30m", help="Ventana aceptada por docker compose logs")
    args = parser.parse_args()
    now = dt.datetime.now().astimezone()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    iso_time = now.isoformat(timespec="seconds")
    OUTPUT.mkdir(parents=True, exist_ok=True)

    log_text = run_logs(args.since)
    lines = [line for line in log_text.splitlines() if line.strip()]
    alerts = correlate(lines)

    log_path = OUTPUT / f"eventos-centralizados-{stamp}.log"
    alert_path = OUTPUT / f"alertas-{stamp}.json"
    html_path = OUTPUT / f"tablero-{stamp}.html"
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    alert_path.write_text(
        json.dumps({"generated_at": iso_time, "alerts": alerts}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    html_path.write_text(render_dashboard(iso_time, lines, alerts), encoding="utf-8")
    print(f"OK: eventos={len(lines)} alertas={len(alerts)} tablero={html_path.name}")


if __name__ == "__main__":
    main()
