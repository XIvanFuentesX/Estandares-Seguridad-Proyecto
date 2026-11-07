"""Simulación (dry-run) de la política de retención de respaldos. NO elimina nada.

Política GFS (local/backup/retention-policy.json): se conserva la última copia de cada día de los
últimos N días, de cada semana de las últimas N semanas y de cada mes de los últimos N meses,
además de la copia más reciente por base. El resto se marca como candidato, con el motivo.
Este script no contiene operaciones de borrado: sólo lee metadatos y escribe el reporte.
"""

import datetime as dt
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "local" / "backup" / "retention-policy.json").read_text(encoding="utf-8"))
BACKUPS = ROOT / POLICY["backups"]["path"]
OUT = ROOT / "evidencias" / "retencion"
NAME = re.compile(r"^(?P<target>[a-z]+)-(?P<stamp>\d{8}-\d{6})\.(?P<ext>dump\.enc\.sha256|dump\.enc|json|toc)$")


def referenced_backups():
    """Copias citadas por evidencias de restauración/actualización: se protegen para no romper la trazabilidad."""
    names = set()
    sources = [ROOT / "evidencias" / "recovery", ROOT / "evidencias" / "postgres-upgrade"]
    for path in (p for folder in sources if folder.exists() for p in folder.rglob("*.json")):
        try:
            names.update(re.findall(r"(?:academic|identity)-\d{8}-\d{6}\.dump\.enc", path.read_text(encoding="utf-8-sig")))
        except (UnicodeDecodeError, OSError):
            continue
    return names


def main():
    now = dt.datetime.now(dt.timezone.utc)
    cfg = POLICY["backups"]
    sets = defaultdict(lambda: {"files": [], "bytes": 0})
    unmatched = []
    for path in sorted(BACKUPS.iterdir()):
        if not path.is_file():
            continue
        match = NAME.match(path.name)
        if not match:
            unmatched.append(path.name)
            continue
        key = (match["target"], match["stamp"])
        sets[key]["files"].append(path.name)
        sets[key]["bytes"] += path.stat().st_size

    referenced = referenced_backups()
    keep = {}
    by_target = defaultdict(list)
    for (target, stamp) in sets:
        created = dt.datetime.strptime(stamp, "%Y%m%d-%H%M%S").replace(tzinfo=dt.timezone.utc)
        by_target[target].append((created, stamp))
    for target, items in by_target.items():
        items.sort(reverse=True)
        for created, stamp in items[: cfg["always_keep_latest_per_target"]]:
            keep.setdefault((target, stamp), []).append("más reciente de la base")
        seen = {"daily": set(), "weekly": set(), "monthly": set()}
        for created, stamp in items:  # de la más nueva a la más antigua: la primera de cada periodo es la última del periodo
            age = now - created
            buckets = [
                ("daily", created.date(), age <= dt.timedelta(days=cfg["daily_days"]), f"diaria (≤ {cfg['daily_days']} días)"),
                ("weekly", tuple(created.isocalendar()[:2]), age <= dt.timedelta(weeks=cfg["weekly_weeks"]), f"semanal (≤ {cfg['weekly_weeks']} semanas)"),
                ("monthly", (created.year, created.month), age <= dt.timedelta(days=31 * cfg["monthly_months"]), f"mensual (≤ {cfg['monthly_months']} meses)"),
            ]
            for tier, period, in_window, label in buckets:
                if in_window and period not in seen[tier]:
                    seen[tier].add(period)
                    keep.setdefault((target, stamp), []).append(f"última copia {label}")

    rows = []
    for (target, stamp), info in sorted(sets.items()):
        created = dt.datetime.strptime(stamp, "%Y%m%d-%H%M%S").replace(tzinfo=dt.timezone.utc)
        enc = f"{target}-{stamp}.dump.enc"
        complete = all(any(f.endswith(ext) for f in info["files"]) for ext in (".dump.enc", ".dump.enc.sha256", ".json"))
        reasons_keep = list(keep.get((target, stamp), []))
        protected = []
        if enc in referenced:
            protected.append("usada en una restauración o en la actualización (evidencia)")
        if not complete:
            protected.append("conjunto incompleto: requiere revisión manual, no se propone borrar")
        if reasons_keep:
            decision, reason = "conservar", "; ".join(reasons_keep)
        elif protected:
            decision, reason = "protegido", "; ".join(protected)
        else:
            decision = "candidato"
            reason = "copia intradía o fuera de las ventanas diaria/semanal/mensual (no es la última de su periodo)"
        rows.append({
            "base": target, "copia": enc, "creada_utc": created.isoformat(timespec="seconds"),
            "antiguedad_h": round((now - created).total_seconds() / 3600, 1),
            "politica": "GFS diaria/semanal/mensual", "decision": decision, "motivo": reason,
            "proteccion_adicional": "; ".join(protected) if reasons_keep and protected else "",
            "archivos": info["files"], "bytes": info["bytes"],
            "ruta": f"{POLICY['backups']['path']}/{enc}",
        })

    candidates = [r for r in rows if r["decision"] == "candidato"]
    siem_db = ROOT / "evidencias" / "siem" / "eventos.db"
    siem = None
    if siem_db.exists():
        cutoff = (now - dt.timedelta(days=30)).isoformat(timespec="seconds")
        with sqlite3.connect(f"file:{siem_db.as_posix()}?mode=ro", uri=True) as db:
            siem = {"retention_days": 30, "events_total": db.execute("SELECT count(*) FROM events").fetchone()[0],
                    "candidates": db.execute("SELECT count(*) FROM events WHERE event_time < ?", (cutoff,)).fetchone()[0]}

    report = {
        "timestamp": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "dry-run (simulación; no se eliminó ningún archivo)",
        "policy": POLICY,
        "summary": {
            "sets_total": len(rows),
            "conservar": sum(r["decision"] == "conservar" for r in rows),
            "protegido": sum(r["decision"] == "protegido" for r in rows),
            "candidato": len(candidates),
            "bytes_candidatos": sum(r["bytes"] for r in candidates),
            "bytes_total": sum(r["bytes"] for r in rows),
        },
        "rows": rows,
        "files_not_in_policy": unmatched,
        "findings": [f"Copia sin cifrar fuera de la política: {name}" for name in unmatched if name.endswith(".dump")],
        "excluded_paths": POLICY["protected_paths"],
        "siem_retention_simulation": siem,
        "not_evaluated": "Bases restauradas en volúmenes aislados: su eliminación no está autorizada; se inventarían aparte.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    (OUT / f"simulacion-retencion-{stamp}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Simulación de retención de respaldos (dry-run)", "",
        f"Generado: {report['timestamp']}. **No se eliminó ningún archivo.** Política propuesta pendiente de validación institucional: "
        f"diaria {cfg['daily_days']} días, semanal {cfg['weekly_weeks']} semanas, mensual {cfg['monthly_months']} meses, "
        "y siempre la copia más reciente por base. Las duraciones no garantizan por sí solas el cumplimiento institucional o regulatorio.", "",
        "| Métrica | Valor |", "|---|---|",
        *[f"| {k} | {v} |" for k, v in report["summary"].items()], "",
        "Excluidos de la política (protegidos): " + ", ".join(f"`{p}`" for p in POLICY["protected_paths"]) + ". "
        "Las evidencias se conservan durante el desarrollo y evaluación del proyecto.", "",
        f"Archivos fuera del patrón de copias: {', '.join(unmatched) or 'ninguno'} (no evaluados).", "",
        *[f"**Hallazgo:** {item}. Contiene datos académicos sin cifrar en el directorio de copias; se recomienda cifrarla o eliminarla con autorización." for item in report["findings"]], "",
        f"SIEM (30 días): {siem}.", "",
        "| Base | Copia | Creada (UTC) | Antigüedad (h) | Decisión | Motivo | Bytes |", "|---|---|---|---|---|---|---|",
        *[f"| {r['base']} | `{r['copia']}` | {r['creada_utc']} | {r['antiguedad_h']} | {r['decision']} | {r['motivo']}"
          + (f" ({r['proteccion_adicional']})" if r['proteccion_adicional'] else "") + f" | {r['bytes']} |" for r in rows],
        "", "Antes de aplicar cualquier borrado se requiere autorización expresa y revisión de este reporte.",
    ]
    (OUT / f"simulacion-retencion-{stamp}.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: dry_run=true conjuntos={len(rows)} conservar={report['summary']['conservar']} "
          f"protegidos={report['summary']['protegido']} candidatos={len(candidates)} bytes_candidatos={report['summary']['bytes_candidatos']} "
          f"evidencia=simulacion-retencion-{stamp}.json")


if __name__ == "__main__":
    main()
