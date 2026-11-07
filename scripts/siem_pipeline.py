"""Ciclo SIEM integrado sobre eventos reales del laboratorio.

Ingiere logs Docker (Nginx, Flask, Keycloak, PostgreSQL, schedulers), la bitácora de backups
y las alertas Suricata; correlaciona, consulta y verifica que las reglas esperadas generen
alertas a partir de eventos realmente observados (no sintéticos).
"""

import argparse
import datetime as dt
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIEM = ROOT / "scripts" / "siem_ligero.py"
OUT = ROOT / "evidencias" / "siem"
DB = OUT / "eventos.db"
SOURCES_REQUIRED = {"proxy-1", "api-1", "keycloak-1", "db-1", "identity-db-1", "backup-scheduler", "controles", "disponibilidad"}


def run(*args):
    result = subprocess.run([sys.executable, str(SIEM), "--db", str(DB), *args],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise SystemExit(f"ERROR: {' '.join(args[:1])}: {result.stderr.strip()[-400:]}")
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default="60m")
    parser.add_argument("--expect", nargs="*", default=["SIEM-AUTH-001", "SIEM-RBAC-001", "SIEM-DB-001", "SIEM-IDS-001", "SIEM-BACKUP-001",
                                                        "SIEM-WAL-001", "SIEM-CFG-001", "SIEM-EDR-001"])
    args = parser.parse_args()
    stamp = dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    steps = [
        run("ingest-docker", "--since", args.since),
        run("ingest-file", str(ROOT / "local" / "backups" / "execution.log"), "--source", "backup-scheduler"),
    ]
    for path, source in ((ROOT / "local" / "monitoring" / "controles.log", "controles"),
                         (ROOT / "local" / "monitoring" / "disponibilidad" / "disponibilidad.log", "disponibilidad")):
        if path.exists():
            steps.append(run("ingest-file", str(path), "--source", source))
    eve = ROOT / "evidencias" / "ids" / "eve.json"
    if eve.exists():
        steps.append(run("ingest-file", str(eve), "--source", "suricata"))
    steps.append(run("correlate"))
    steps.append(run("seal"))
    steps.append(run("verify"))
    queries = {
        "auth-denied": ["--category", "authentication", "--outcome", "denied"],
        "rbac-denied": ["--category", "authorization", "--outcome", "denied"],
        "db-auth-denied": ["--category", "database_authentication"],
        "backup-failure": ["--category", "backup", "--outcome", "failure"],
        "wal": ["--category", "wal_archiving"],
        "config-integrity-failure": ["--category", "config_integrity", "--outcome", "failure"],
        "container-monitoring-failure": ["--category", "container_monitoring", "--outcome", "failure"],
        "availability": ["--category", "availability"],
        "suricata": ["--source", "suricata"],
    }
    query_counts = {}
    for name, filters in queries.items():
        target = OUT / f"consulta-{name}-{stamp}.json"
        run("search", *filters, "--limit", "100", "--output", str(target))
        query_counts[name] = len(json.loads(target.read_text(encoding="utf-8")))
    run("alerts", "--output", str(OUT / f"alertas-{stamp}.json"))
    run("dashboard", "--output", str(OUT / f"tablero-siem-{stamp}.html"))
    run("report", "--output", str(OUT / f"reporte-integrado-{stamp}.json"))
    retention = run("retention", "--days", "30")

    db = sqlite3.connect(DB)
    sources = {row[0] for row in db.execute("SELECT DISTINCT source FROM events")}
    fired = {row[0] for row in db.execute("SELECT DISTINCT rule_id FROM alerts")}
    # Comprueba que las alertas esperadas se apoyan en eventos reales y no en la prueba sintética.
    real_support = {}
    for rule_id in args.expect:
        row = db.execute("SELECT evidence_event_ids FROM alerts WHERE rule_id=? ORDER BY id DESC LIMIT 1", (rule_id,)).fetchone()
        if row:
            ids = [int(value) for value in row[0].split(",") if value]
            marks = ",".join("?" * len(ids))
            real_support[rule_id] = sorted({r[0] for r in db.execute(f"SELECT source FROM events WHERE id IN ({marks})", ids)})
    secrets_found = db.execute(
        "SELECT count(*) FROM events WHERE message LIKE '%eyJhbGci%' OR message LIKE '%KEYCLOAK_SESSION=%' OR lower(message) LIKE '%password=%' AND message NOT LIKE '%[REDACTED]%'"
    ).fetchone()[0]
    db.close()

    missing_sources = sorted(SOURCES_REQUIRED - sources)
    missing_rules = sorted(set(args.expect) - fired)
    synthetic_only = sorted(rule for rule, srcs in real_support.items() if set(srcs) <= {"synthetic-control"})
    result = {
        "timestamp": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "result": "success" if not (missing_sources or missing_rules or synthetic_only or secrets_found) else "failure",
        "steps": steps,
        "sources_present": sorted(sources),
        "missing_required_sources": missing_sources,
        "rules_fired": sorted(fired),
        "missing_expected_rules": missing_rules,
        "alert_sources_by_rule": real_support,
        "query_result_counts": query_counts,
        "unredacted_secret_patterns": secrets_found,
        "retention": retention,
        "artifacts": [f"alertas-{stamp}.json", f"tablero-siem-{stamp}.html", f"reporte-integrado-{stamp}.json"],
    }
    (OUT / f"pipeline-siem-{stamp}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if result["result"] != "success":
        raise SystemExit(f"ERROR: fuentes={missing_sources} reglas={missing_rules} solo_sinteticas={synthetic_only} secretos={secrets_found}")
    print(f"OK: fuentes={len(sources)} reglas_disparadas={len(fired)} esperadas={len(args.expect)} secretos=0 evidencia=pipeline-siem-{stamp}.json")


if __name__ == "__main__":
    main()
