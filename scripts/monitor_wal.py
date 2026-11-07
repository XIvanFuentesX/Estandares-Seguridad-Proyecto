"""Monitor de archivado WAL: estado de archive_mode, fallos de archive_command, retraso y crecimiento.

Uso standalone (sólo lectura) sobre las bases principales:
    python scripts/monitor_wal.py --container local-db-1 --env-user DB_USER --env-db DB_NAME
Registra una línea `target=wal-<nombre> result=success|warning|failure ...` en local/backups/execution.log,
que alimenta la regla SIEM-WAL-001. Si archive_mode está desactivado, lo informa como brecha (no como éxito).
"""

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "local" / "backups" / "execution.log"


def _sql(container, user, db, sql):
    proc = subprocess.run(["docker", "exec", container, "psql", "-U", user, "-d", db, "-Atc", sql],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip()[-300:])
    return proc.stdout.strip()


def check_wal(container, user, db, archive_dir=None, warn_mb=512, max_lag_s=900, name=None, write_log=True):
    status = {"container": container, "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    settings = dict(line.split("|", 1) for line in _sql(container, user, db,
        "SELECT name||'|'||setting FROM pg_settings WHERE name IN ('archive_mode','wal_level','archive_timeout')").splitlines())
    status["settings"] = settings
    row = _sql(container, user, db, "SELECT archived_count, failed_count, coalesce(last_failed_wal,''), "
               "coalesce(extract(epoch FROM now()-last_archived_time)::int, -1), "
               "(SELECT coalesce(sum(size),0) FROM pg_ls_waldir()), "
               "coalesce(last_failed_time > coalesce(last_archived_time, 'epoch'::timestamptz), false) FROM pg_stat_archiver").split("|")
    status.update({"archived_count": int(row[0]), "failed_count": int(row[1]), "last_failed_wal": row[2],
                   "seconds_since_last_archive": int(row[3]), "pg_wal_mb": round(int(row[4]) / 1048576, 1),
                   "failure_active": row[5] == "t"})
    if archive_dir:
        size = subprocess.run(["docker", "exec", container, "du", "-sk", archive_dir], capture_output=True, text=True).stdout.split()
        status["archive_mb"] = round(int(size[0]) / 1024, 1) if size else None
    problems, warnings = [], []
    if settings.get("archive_mode") != "on":
        problems.append("archive_mode_off")
    if status["failure_active"]:
        problems.append(f"archive_command_failed({status['failed_count']})")
    if settings.get("archive_mode") == "on" and status["seconds_since_last_archive"] > max_lag_s:
        warnings.append(f"archive_lag_{status['seconds_since_last_archive']}s")
    if status["pg_wal_mb"] > warn_mb or (status.get("archive_mb") or 0) > warn_mb:
        warnings.append(f"wal_growth_over_{warn_mb}MB")
    status["result"] = "failure" if problems else "warning" if warnings else "success"
    status["issues"] = problems + warnings
    if write_log:
        with LOG.open("a", encoding="ascii", errors="replace") as handle:
            handle.write(f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ} target=wal-{name or container} "
                         f"result={status['result']} issues={','.join(status['issues']) or 'none'}\n")
    return status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--container", required=True)
    parser.add_argument("--env-user", required=True)
    parser.add_argument("--env-db", required=True)
    parser.add_argument("--name")
    parser.add_argument("--warn-mb", type=int, default=512)
    args = parser.parse_args()
    env = dict(line.split("=", 1) for line in (ROOT / "local" / ".env").read_text(encoding="utf-8").splitlines() if "=" in line and not line.startswith("#"))
    status = check_wal(args.container, env[args.env_user].strip(), env[args.env_db].strip(), warn_mb=args.warn_mb, name=args.name)
    print(json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
