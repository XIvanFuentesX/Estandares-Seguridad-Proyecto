"""Valida que Suricata detecte cada escenario controlado y no alerte el tráfico benigno."""

import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = ROOT / "evidencias" / "ids"
eve = IDS / "eve.json"
if not eve.exists():
    raise SystemExit("ERROR: Suricata no generó eve.json")

scenarios = json.loads((IDS / "escenarios-pcap.json").read_text(encoding="utf-8"))
alerts = []
for line in eve.read_text(encoding="utf-8").splitlines():
    event = json.loads(line)
    if event.get("event_type") == "alert":
        alerts.append(event)

by_sid = collections.Counter(event.get("alert", {}).get("signature_id") for event in alerts)
results = []
for scenario in scenarios:
    expected = scenario["expected_sid"]
    if expected is None:
        hits = [event for event in alerts if event.get("src_ip") == scenario["src_ip"]]
        passed = not hits
        observed = f"{len(hits)} alertas (esperado 0)"
    else:
        passed = by_sid.get(expected, 0) > 0
        observed = f"{by_sid.get(expected, 0)} alertas sid {expected}"
    results.append({**scenario, "observed": observed, "result": "success" if passed else "failure"})

failed = [item["id"] for item in results if item["result"] != "success"]
summary = {
    "verified": not failed,
    "mode": "offline_pcap_detection",
    "rules_file": "local/ids/rules/uvcg.rules",
    "alert_count": len(alerts),
    "alerts_by_sid": {str(key): value for key, value in sorted(by_sid.items())},
    "scenarios": results,
    "true_positives": sum(1 for item in results if item["expected_sid"] and item["result"] == "success"),
    "false_positives_on_benign": sum(1 for item in results if item["expected_sid"] is None and item["result"] != "success"),
    "limitations": "Detección IDS offline sobre PCAP sintético; no captura tráfico en vivo, no es IPS ni EDR/XDR.",
}
(IDS / "resultado.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
if failed:
    raise SystemExit(f"ERROR: escenarios fallidos={failed}")
print(f"OK: escenarios={len(results)} verdaderos_positivos={summary['true_positives']} "
      f"falsos_positivos=0 total_alerts={len(alerts)} mode=offline")
