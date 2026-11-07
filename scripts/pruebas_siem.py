"""Prueba controlada del SIEM ligero sin credenciales ni datos reales."""

import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "siem_ligero.py"
OUT = ROOT / "evidencias" / "siem"
OUT.mkdir(parents=True, exist_ok=True)
stamp = dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
db = OUT / f"prueba-siem-{stamp}.db"
report = OUT / f"resultado-siem-{stamp}.json"
base = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
events = []
for offset in range(3):
    events.append(json.dumps({
        "timestamp": (base + dt.timedelta(seconds=offset)).isoformat(),
        "event": "authentication", "outcome": "denied", "reason": "invalid_token",
        "authorization": "Bearer eyJ123456789.abcdefghijk.zyxwvutsrq"
    }))
events.append(json.dumps({
    "timestamp": (base + dt.timedelta(seconds=4)).isoformat(),
    "event": "authorization", "outcome": "denied", "reason": "insufficient_permissions",
    "password": "SYNTHETIC-MUST-NOT-PERSIST"
}))
events.append(json.dumps({
    "timestamp": (base + dt.timedelta(seconds=5)).isoformat(),
    "event": "backup", "message": "target=academic result=failure"
}))

with tempfile.TemporaryDirectory() as temp:
    source = Path(temp) / "synthetic.jsonl"
    source.write_text("\n".join(events), encoding="utf-8")
    commands = [
        [sys.executable, str(SCRIPT), "--db", str(db), "ingest-file", str(source), "--source", "synthetic-control"],
        [sys.executable, str(SCRIPT), "--db", str(db), "correlate"],
        [sys.executable, str(SCRIPT), "--db", str(db), "report", "--output", str(report)],
    ]
    for command in commands:
        subprocess.run(command, check=True)

data = json.loads(report.read_text(encoding="utf-8"))
rule_ids = {item["rule_id"] for item in data["rules"]}
assert "SIEM-AUTH-001" in rule_ids
assert "SIEM-RBAC-001" in rule_ids
assert "SIEM-BACKUP-001" in rule_ids
raw_db = db.read_bytes()
assert b"SYNTHETIC-MUST-NOT-PERSIST" not in raw_db
assert b"eyJ123456789" not in raw_db
summary = {
    "timestamp": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    "result": "success",
    "synthetic_events": len(events),
    "rules_verified": sorted(rule_ids),
    "secret_redaction_verified": True,
    "database": db.name,
    "report": report.name,
}
(OUT / f"prueba-controlada-{stamp}.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"OK: eventos={len(events)} reglas={len(rule_ids)} redaction=true")
