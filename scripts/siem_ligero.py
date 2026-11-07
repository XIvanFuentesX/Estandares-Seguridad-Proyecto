"""SIEM ligero UVCG: ingesta, saneamiento, búsqueda, correlación y retención."""

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "local"
DEFAULT_DB = ROOT / "evidencias" / "siem" / "eventos.db"
RULES_PATH = LOCAL / "monitoring" / "rules.json"
UTC = dt.timezone.utc

REDACTIONS = [
    (re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[A-Za-z0-9._~-]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)((?:access_token|refresh_token|id_token|password|cookie|set-cookie)\s*[=:]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(\"(?:access_token|refresh_token|id_token|password|cookie|set-cookie)\"\s*:\s*\")[^\"]+"), r"\1[REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"), "[JWT_REDACTED]"),
]


def now_iso():
    return dt.datetime.now(UTC).isoformat(timespec="seconds")


def parse_time(value):
    if not value:
        return now_iso()
    value = value.strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat(timespec="seconds")
    except ValueError:
        return now_iso()


def redact(value):
    value = value.replace("\x00", "")[:8000]
    for pattern, replacement in REDACTIONS:
        value = pattern.sub(replacement, value)
    return value


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY, event_time TEXT NOT NULL, source TEXT NOT NULL,
          category TEXT NOT NULL, outcome TEXT, message TEXT NOT NULL,
          event_hash TEXT NOT NULL UNIQUE, ingested_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_events_time ON events(event_time);
        CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
        CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
        CREATE TABLE IF NOT EXISTS alerts (
          id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, rule_id TEXT NOT NULL,
          rule_name TEXT NOT NULL, severity TEXT NOT NULL, event_count INTEGER NOT NULL,
          first_event_time TEXT NOT NULL, last_event_time TEXT NOT NULL,
          evidence_event_ids TEXT NOT NULL, alert_hash TEXT NOT NULL UNIQUE
        );
        CREATE INDEX IF NOT EXISTS idx_alerts_rule ON alerts(rule_id, created_at);
        """
    )
    return db


def classify(source, message, record=None):
    lower = message.lower()
    if source == "suricata" or (record and record.get("event_type") == "alert"):
        return "ids_alert", "detected"
    if "login_error" in lower or ('"event": "authentication"' in lower and '"outcome": "denied"' in lower):
        return "authentication", "denied"
    if '"event": "authorization"' in lower and '"outcome": "denied"' in lower:
        return "authorization", "denied"
    if "password authentication failed" in lower or "no pg_hba.conf entry" in lower:
        return "database_authentication", "denied"
    control = re.search(r"target=(wal|config|avail|edr|dlp)-\S* result=(\w+)", lower)
    if control:
        kind = {"wal": "wal_archiving", "config": "config_integrity", "avail": "availability", "edr": "container_monitoring", "dlp": "dlp"}[control.group(1)]
        return kind, control.group(2)
    if "target=" in lower and "result=failure" in lower:
        return "backup", "failure"
    if re.search(r'http/[0-9.]+[" ]+(401|403)', lower):
        return "http_access", "denied"
    if any(word in lower for word in (" error ", "fatal", "traceback", "unhealthy")):
        return "service_error", "error"
    return "operational", "observed"


def normalize_line(raw, forced_source=None):
    raw = raw.strip()
    if not raw:
        return None
    record = None
    try:
        candidate = json.loads(raw)
        if isinstance(candidate, dict):
            record = candidate
    except json.JSONDecodeError:
        pass

    if record and record.get("event_type") == "alert":
        alert = record.get("alert", {})
        safe = {
            "event": "suricata_alert",
            "signature_id": alert.get("signature_id"),
            "signature": alert.get("signature"),
            "category": alert.get("category"),
            "severity": alert.get("severity"),
            "proto": record.get("proto"),
            "dest_port": record.get("dest_port"),
        }
        source = forced_source or "suricata"
        event_time = parse_time(record.get("timestamp"))
        message = json.dumps(safe, ensure_ascii=False, sort_keys=True)
    else:
        match = re.match(r"^([^|]{1,80})\s+\|\s+(\S+)\s+(.*)$", raw)
        if match:
            source = forced_source or match.group(1).strip()
            event_time = parse_time(match.group(2))
            message = match.group(3)
        else:
            source = forced_source or "file"
            timestamp = record.get("timestamp") if record else None
            leading = re.match(r"^(\d{4}-\d{2}-\d{2}T\S+)\s+(.*)$", raw) if not record else None
            if leading:
                timestamp = leading.group(1)
            event_time = parse_time(timestamp)
            message = raw
    message = redact(message)
    category, outcome = classify(source, message, record)
    digest = hashlib.sha256(f"{event_time}|{source}|{message}".encode()).hexdigest()
    return event_time, source[:80], category, outcome, message, digest


def insert_lines(db, lines, source=None):
    inserted = duplicate = 0
    for raw in lines:
        event = normalize_line(raw, source)
        if not event:
            continue
        try:
            db.execute(
                "INSERT INTO events(event_time,source,category,outcome,message,event_hash,ingested_at) VALUES(?,?,?,?,?,?,?)",
                (*event, now_iso()),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            duplicate += 1
    db.commit()
    return inserted, duplicate


def docker_logs(since):
    base_services = ["db", "identity-db", "api", "proxy", "keycloak"]
    status = subprocess.run(
        ["docker", "compose", "-f", "compose.yaml", "--profile", "backup-scheduled", "ps", "--services", "--status", "running"],
        cwd=LOCAL, text=True, encoding="utf-8", errors="replace", capture_output=True,
    )
    running = set(status.stdout.split()) if status.returncode == 0 else set(base_services)
    services = [
        service for service in base_services + ["academic-backup-scheduler", "identity-backup-scheduler"]
        if service in running
    ]
    command = [
        "docker", "compose", "-f", "compose.yaml", "logs", "--no-color", "--timestamps",
        f"--since={since}", *services,
    ]
    result = subprocess.run(command, cwd=LOCAL, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if result.returncode:
        raise RuntimeError("No se pudieron obtener logs Docker: " + redact(result.stderr))
    return result.stdout.splitlines()


def correlate(db, rules_path):
    config = json.loads(rules_path.read_text(encoding="utf-8"))
    events = list(db.execute("SELECT id,event_time,message FROM events ORDER BY event_time"))
    created = 0
    for rule in config["rules"]:
        pattern = re.compile(rule["pattern"], re.I)
        matches = [row for row in events if pattern.search(row["message"])]
        window = dt.timedelta(seconds=int(rule["window_seconds"]))
        for index, start in enumerate(matches):
            start_time = dt.datetime.fromisoformat(start["event_time"])
            group = [
                row for row in matches[index:]
                if dt.datetime.fromisoformat(row["event_time"]) - start_time <= window
            ]
            if len(group) < int(rule["threshold"]):
                continue
            selected = group[: max(int(rule["threshold"]), 20)]
            ids = ",".join(str(row["id"]) for row in selected)
            alert_hash = hashlib.sha256(f'{rule["id"]}|{ids}'.encode()).hexdigest()
            try:
                db.execute(
                    "INSERT INTO alerts(created_at,rule_id,rule_name,severity,event_count,first_event_time,last_event_time,evidence_event_ids,alert_hash) VALUES(?,?,?,?,?,?,?,?,?)",
                    (now_iso(), rule["id"], rule["name"], rule["severity"], len(group),
                     group[0]["event_time"], group[-1]["event_time"], ids, alert_hash),
                )
                created += 1
            except sqlite3.IntegrityError:
                pass
            break
    db.commit()
    return created


def query(db, args):
    where, params = [], []
    for column, value in (("source", args.source), ("category", args.category), ("outcome", args.outcome)):
        if value:
            where.append(f"{column} = ?")
            params.append(value)
    if args.contains:
        where.append("message LIKE ?")
        params.append(f"%{args.contains}%")
    if args.since:
        where.append("event_time >= ?")
        params.append(parse_time(args.since))
    if args.until:
        where.append("event_time <= ?")
        params.append(parse_time(args.until))
    sql = "SELECT id,event_time,source,category,outcome,message FROM events"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY event_time DESC LIMIT ?"
    params.append(min(args.limit, 500))
    return [dict(row) for row in db.execute(sql, params)]


def write_report(db, output):
    stats = {
        "generated_at": now_iso(),
        "events": db.execute("SELECT count(*) FROM events").fetchone()[0],
        "alerts": db.execute("SELECT count(*) FROM alerts").fetchone()[0],
        "by_source": {r[0]: r[1] for r in db.execute("SELECT source,count(*) FROM events GROUP BY source")},
        "by_category": {r[0]: r[1] for r in db.execute("SELECT category,count(*) FROM events GROUP BY category")},
        "rules": [dict(r) for r in db.execute("SELECT rule_id,rule_name,severity,event_count,first_event_time,last_event_time FROM alerts ORDER BY created_at DESC")],
        "limitations": [
            "Sin alta disponibilidad ni almacenamiento inmutable.",
            "Sin agentes de endpoint, UEBA, inteligencia de amenazas ni respuesta automática.",
            "Búsqueda local SQLite; no equivale a Wazuh/OpenSearch/Sentinel empresarial."
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def seal(db):
    """Sella los eventos nuevos: hash encadenado (hash del lote + sello anterior)."""
    db.execute("CREATE TABLE IF NOT EXISTS seals (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, first_event_id INTEGER NOT NULL, "
               "last_event_id INTEGER NOT NULL, events_hash TEXT NOT NULL, prev_seal_hash TEXT NOT NULL, seal_hash TEXT NOT NULL)")
    last = db.execute("SELECT last_event_id, seal_hash FROM seals ORDER BY id DESC LIMIT 1").fetchone()
    start, prev = (last[0], last[1]) if last else (0, "GENESIS")
    rows = list(db.execute("SELECT id, event_hash FROM events WHERE id > ? ORDER BY id", (start,)))
    if not rows:
        return 0
    events_hash = hashlib.sha256("".join(r[1] for r in rows).encode()).hexdigest()
    seal_hash = hashlib.sha256(f"{prev}|{rows[0][0]}|{rows[-1][0]}|{events_hash}".encode()).hexdigest()
    db.execute("INSERT INTO seals(created_at,first_event_id,last_event_id,events_hash,prev_seal_hash,seal_hash) VALUES(?,?,?,?,?,?)",
               (now_iso(), rows[0][0], rows[-1][0], events_hash, prev, seal_hash))
    db.commit()
    return len(rows)


def verify(db):
    """Recalcula el hash de cada evento y la cadena de sellos; devuelve la lista de problemas."""
    problems = []
    for row in db.execute("SELECT id, event_time, source, message, event_hash FROM events"):
        if hashlib.sha256(f"{row[1]}|{row[2]}|{row[3]}".encode()).hexdigest() != row[4]:
            problems.append(f"evento {row[0]} alterado")
    if not db.execute("SELECT name FROM sqlite_master WHERE name='seals'").fetchone():
        return problems + ["sin sellos"]
    prev = "GENESIS"
    for s_id, first, last, events_hash, prev_hash, seal_hash in db.execute(
            "SELECT id, first_event_id, last_event_id, events_hash, prev_seal_hash, seal_hash FROM seals ORDER BY id"):
        hashes = "".join(r[0] for r in db.execute("SELECT event_hash FROM events WHERE id BETWEEN ? AND ? ORDER BY id", (first, last)))
        if hashlib.sha256(hashes.encode()).hexdigest() != events_hash:
            problems.append(f"sello {s_id}: lote de eventos modificado o eliminado")
        if prev_hash != prev or hashlib.sha256(f"{prev}|{first}|{last}|{events_hash}".encode()).hexdigest() != seal_hash:
            problems.append(f"sello {s_id}: cadena rota")
        prev = seal_hash
    return problems


def list_alerts(db, rule_id=None, limit=100):
    sql = "SELECT id,created_at,rule_id,rule_name,severity,event_count,first_event_time,last_event_time,evidence_event_ids FROM alerts"
    params = []
    if rule_id:
        sql += " WHERE rule_id = ?"
        params.append(rule_id)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(min(limit, 500))
    return [dict(row) for row in db.execute(sql, params)]


def write_dashboard(db, output):
    """Vista HTML estática de sólo lectura; no expone puertos ni ejecuta consultas remotas."""
    esc = html.escape
    by_source = list(db.execute("SELECT source,count(*) FROM events GROUP BY source ORDER BY 2 DESC"))
    by_category = list(db.execute("SELECT category,outcome,count(*) FROM events GROUP BY category,outcome ORDER BY 3 DESC"))
    alerts = list_alerts(db, limit=50)
    recent = list(db.execute(
        "SELECT event_time,source,category,outcome,message FROM events WHERE outcome IN ('denied','failure','detected','error') ORDER BY event_time DESC LIMIT 50"))

    def rows(items):
        return "".join("<tr>" + "".join(f"<td>{esc(str(v))}</td>" for v in item) + "</tr>" for item in items)

    page = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>SIEM ligero UVCG</title>
<style>body{{font-family:system-ui,sans-serif;margin:24px;background:#fff;color:#1d2433}}table{{border-collapse:collapse;margin:8px 0 24px;width:100%}}
td,th{{border:1px solid #ccd;padding:4px 8px;font-size:13px;text-align:left;vertical-align:top}}th{{background:#eef}}td:last-child{{word-break:break-all}}</style></head><body>
<h1>SIEM ligero UVCG — vista de consulta</h1><p>Generado {esc(now_iso())}. Datos saneados (sin contraseñas, JWT ni cookies). Laboratorio; no equivale a un SIEM empresarial.</p>
<h2>Alertas de correlación</h2><table><tr><th>ID</th><th>Creada</th><th>Regla</th><th>Nombre</th><th>Severidad</th><th>Eventos</th><th>Primer evento</th><th>Último evento</th><th>IDs evidencia</th></tr>{rows(tuple(a.values()) for a in alerts)}</table>
<h2>Eventos por origen</h2><table><tr><th>Origen</th><th>Eventos</th></tr>{rows(by_source)}</table>
<h2>Eventos por categoría</h2><table><tr><th>Categoría</th><th>Resultado</th><th>Eventos</th></tr>{rows(by_category)}</table>
<h2>Últimos eventos de seguridad</h2><table><tr><th>Hora UTC</th><th>Origen</th><th>Categoría</th><th>Resultado</th><th>Mensaje</th></tr>{rows(recent)}</table>
</body></html>"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    return len(alerts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest-docker")
    ingest.add_argument("--since", default="30m")
    ingest_file = sub.add_parser("ingest-file")
    ingest_file.add_argument("path", type=Path)
    ingest_file.add_argument("--source", required=True)
    sub.add_parser("correlate").add_argument("--rules", type=Path, default=RULES_PATH)
    search = sub.add_parser("search")
    search.add_argument("--source")
    search.add_argument("--category")
    search.add_argument("--outcome")
    search.add_argument("--contains")
    search.add_argument("--since", help="ISO 8601, p. ej. 2026-10-24T15:00:00Z")
    search.add_argument("--until")
    search.add_argument("--limit", type=int, default=50)
    search.add_argument("--output", type=Path)
    report = sub.add_parser("report")
    report.add_argument("--output", type=Path, required=True)
    alerts = sub.add_parser("alerts")
    alerts.add_argument("--rule")
    alerts.add_argument("--limit", type=int, default=100)
    alerts.add_argument("--output", type=Path)
    dashboard = sub.add_parser("dashboard")
    dashboard.add_argument("--output", type=Path, required=True)
    sub.add_parser("seal")
    sub.add_parser("verify")
    retention = sub.add_parser("retention")
    retention.add_argument("--days", type=int, default=30)
    retention.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    db = connect(args.db)
    try:
        if args.command == "ingest-docker":
            inserted, duplicate = insert_lines(db, docker_logs(args.since))
            print(f"OK: inserted={inserted} duplicate={duplicate} source=docker")
        elif args.command == "ingest-file":
            inserted, duplicate = insert_lines(db, args.path.read_text(encoding="utf-8").splitlines(), args.source)
            print(f"OK: inserted={inserted} duplicate={duplicate} source={args.source}")
        elif args.command == "correlate":
            print(f"OK: alerts_created={correlate(db, args.rules)}")
        elif args.command == "search":
            result = json.dumps(query(db, args), ensure_ascii=False, indent=2)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(result, encoding="utf-8")
                print(f"OK: query_results={len(json.loads(result))} output={args.output.name}")
            else:
                print(result)
        elif args.command == "report":
            stats = write_report(db, args.output)
            print(f'OK: events={stats["events"]} alerts={stats["alerts"]} report={args.output.name}')
        elif args.command == "alerts":
            result = json.dumps(list_alerts(db, args.rule, args.limit), ensure_ascii=False, indent=2)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(result, encoding="utf-8")
                print(f"OK: alerts={len(json.loads(result))} output={args.output.name}")
            else:
                print(result)
        elif args.command == "dashboard":
            print(f"OK: dashboard_alerts={write_dashboard(db, args.output)} output={args.output.name}")
        elif args.command == "seal":
            print(f"OK: eventos_sellados={seal(db)}")
        elif args.command == "verify":
            problems = verify(db)
            if problems:
                print("ERROR: " + "; ".join(problems[:20]))
                raise SystemExit(1)
            print(f"OK: integridad_eventos=verificada sellos={db.execute('SELECT count(*) FROM seals').fetchone()[0]}")
        elif args.command == "retention":
            cutoff = (dt.datetime.now(UTC) - dt.timedelta(days=args.days)).isoformat(timespec="seconds")
            count = db.execute("SELECT count(*) FROM events WHERE event_time < ?", (cutoff,)).fetchone()[0]
            if args.apply:
                db.execute("DELETE FROM events WHERE event_time < ?", (cutoff,))
                db.commit()
            print(f"OK: candidates={count} applied={args.apply} retention_days={args.days}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
