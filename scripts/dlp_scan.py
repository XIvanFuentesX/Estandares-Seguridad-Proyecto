"""Escáner DLP demostrativo: identifica y bloquea patrones ficticios sin mostrarlos."""

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT / "local" / "dlp" / "samples"
EVIDENCE = ROOT / "evidencias" / "dlp"

PATTERNS = {
    "GT-DPI-13": re.compile(r"(?<!\d)\d{13}(?!\d)"),
    "CLASS-RESTRICTED": re.compile(r"CLASIFICACION\s*:\s*RESTRINGIDA", re.I),
    "SECRET-ASSIGNMENT": re.compile(r"(?i)\b(password|secret|token|api[_-]?key)\s*[:=]\s*\S+"),
}


def scan(path):
    findings = []
    for file in path.rglob("*"):
        if not file.is_file() or file.stat().st_size > 1_000_000:
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for rule_id, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append(
                    {
                        "rule_id": rule_id,
                        "file": str(file.relative_to(ROOT)),
                        "line": text.count("\n", 0, match.start()) + 1,
                        "value_sha256_prefix": hashlib.sha256(match.group(0).encode()).hexdigest()[:12],
                        "action": "blocked",
                    }
                )
    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--expect-findings", action="store_true")
    args = parser.parse_args()
    findings = scan(args.path.resolve())
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now().astimezone()
    output = EVIDENCE / f"dlp-{now.strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(
        json.dumps(
            {
                "timestamp": now.isoformat(timespec="seconds"),
                "scope": str(args.path),
                "synthetic_data_only": True,
                "findings": findings,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    if args.expect_findings and findings:
        print(f"OK: hallazgos_sinteticos={len(findings)} action=blocked")
        return 0
    if findings:
        print(f"BLOCKED: hallazgos={len(findings)}")
        return 2
    print("OK: sin hallazgos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
