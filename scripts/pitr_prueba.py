"""Prueba PITR (WAL + respaldo base) en réplicas AISLADAS de las bases académica e identidad.

Flujo por base:
  1. Réplica fuente aislada (red interna `local_recovery`, imagen endurecida, UID 70) con
     wal_level=replica, archive_mode=on, archive_timeout y archive_command hacia un archivo WAL.
  2. Carga del respaldo cifrado real más reciente de la base (copia de producción).
  3. Respaldo base (pg_basebackup) + manifiesto SHA-256 de base y segmentos WAL.
  4. Filas ficticias ANTES del punto objetivo; marca de tiempo objetivo; filas DESPUÉS.
  5. Medición del RPO observado: tiempo desde el commit hasta que su segmento WAL queda archivado
     (sin forzar el cambio de segmento: lo determina archive_timeout).
  6. Recuperación en otra instancia aislada (sin red) a recovery_target_time; verificación:
     filas ANTES presentes, DESPUÉS ausentes, conteo del conjunto de datos real. Mide el RTO técnico.
No toca db ni identity-db, no restaura sobre bases principales y no elimina volúmenes:
cada ejecución usa subdirectorios nuevos dentro de los volúmenes sgsi_pitr_data/sgsi_pitr_archive.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from monitor_wal import check_wal  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "local"
OUT = ROOT / "evidencias" / "pitr"
IMAGE = "local-postgres-hardened:16"
TOOL = "local-backup-tool:latest"
NETWORK = "local_recovery"
DATA_VOL, ARCH_VOL = "sgsi_pitr_data", "sgsi_pitr_archive"
LOG = LOCAL / "backups" / "execution.log"
TARGETS = {
    "academic": {"prefix": "academic", "db": "universidad_pitr", "query": "SELECT count(*) FROM cursos", "minimum": 3, "rpo_objetivo_s": 4 * 3600},
    "identity": {"prefix": "identity", "db": "keycloak_pitr", "query": "SELECT count(*) FROM user_entity", "minimum": 4, "rpo_objetivo_s": 15 * 60},
}


def env_file():
    values = {}
    for line in (LOCAL / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def run(args, env=None, check=True, timeout=300):
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=timeout)
    if check and proc.returncode:
        raise RuntimeError(f"{' '.join(args[:4])}…: {proc.stderr.strip()[-500:]}")
    return proc.stdout.strip()


def psql(container, db, sql, user="pitr"):
    return run(["docker", "exec", container, "psql", "-U", user, "-d", db, "-Atc", sql])


def helper(cmd, user="70:70"):
    return run(["docker", "run", "--rm", "--network", "none", "--user", user, "-v", f"{DATA_VOL}:/data",
                "-v", f"{ARCH_VOL}:/pitr", "--entrypoint", "sh", IMAGE, "-ec", cmd])


def wait_ready(container, timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = run(["docker", "inspect", "-f", "{{.State.Running}}", container], check=False)
        if state != "true":
            logs = run(["docker", "logs", "--tail", "30", container], check=False)
            raise RuntimeError(f"{container} se detuvo: {logs[-400:]}")
        if subprocess.run(["docker", "exec", container, "pg_isready", "-q"], capture_output=True).returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(f"{container} no quedó listo")


def log_line(target, result, detail=""):
    with LOG.open("a", encoding="ascii", errors="replace") as handle:
        handle.write(f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ} target=wal-{target} result={result} {detail}\n")


def sha_manifest(container, path):
    out = run(["docker", "exec", container, "sh", "-c", f"cd {path} && find . -type f -exec sha256sum {{}} +"])
    return dict(reversed(line.split(None, 1)) for line in out.splitlines() if line)


def pitr(target, run_id, archive_timeout, secrets_env):
    cfg = TARGETS[target]
    base = f"/data/{run_id}/{target}"
    wal = f"/pitr/{run_id}/{target}/wal"
    bb = f"/pitr/{run_id}/{target}/base"
    src, rst = f"sgsi-pitr-src-{target}-{run_id}", f"sgsi-pitr-rst-{target}-{run_id}"
    result = {"target": target, "run_id": run_id, "archive_timeout_s": archive_timeout, "steps": []}
    env = dict(os.environ, POSTGRES_PASSWORD=secrets.token_urlsafe(24), BACKUP_ENCRYPTION_PASSWORD=secrets_env["BACKUP_ENCRYPTION_PASSWORD"])
    env["PGPASSWORD"] = env["POSTGRES_PASSWORD"]
    try:
        helper(f"mkdir -p {base}/src {base}/restore {wal} {bb} && chmod 700 {base}/src {base}/restore")
        archive_cmd = f"test ! -f {wal}/%f && cp %p {wal}/%f"
        run(["docker", "run", "-d", "--name", src, "--network", NETWORK, "--user", "70:70", "--read-only",
             "--tmpfs", "/tmp", "--tmpfs", "/var/run/postgresql:uid=70,gid=70", "--security-opt", "no-new-privileges:true",
             "--cap-drop", "ALL", "--memory", "256m", "-v", f"{DATA_VOL}:/data", "-v", f"{ARCH_VOL}:/pitr",
             "-e", f"PGDATA={base}/src", "-e", "POSTGRES_USER=pitr", "-e", "POSTGRES_PASSWORD", "-e", f"POSTGRES_DB={cfg['db']}",
             IMAGE, "postgres", "-c", "wal_level=replica", "-c", "archive_mode=on", "-c", f"archive_timeout={archive_timeout}",
             "-c", f"archive_command={archive_cmd}"], env=env)
        wait_ready(src)
        backups = sorted((LOCAL / "backups").glob(f"{cfg['prefix']}-*.dump.enc"), key=lambda p: p.stat().st_mtime)
        dump = backups[-1].name
        expected = (LOCAL / "backups" / f"{dump}.sha256").read_text().split()[0].lower()
        if hashlib.sha256((LOCAL / "backups" / dump).read_bytes()).hexdigest() != expected:
            raise RuntimeError("SHA-256 del respaldo lógico no coincide")
        run(["docker", "run", "--rm", "--network", NETWORK, "--read-only", "--tmpfs", "/tmp", "--cap-drop", "ALL",
             "-v", f"{LOCAL / 'backups'}:/backups:ro", "-e", "BACKUP_ENCRYPTION_PASSWORD", "-e", "PGPASSWORD",
             "-e", f"PGHOST={src}", "-e", "PGUSER=pitr", "-e", f"PGDATABASE={cfg['db']}", TOOL, "sh", "-ec",
             f"openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in /backups/{dump} -out /tmp/r.dump -pass env:BACKUP_ENCRYPTION_PASSWORD;"
             " pg_restore --exit-on-error --no-owner --no-acl -d \"$PGDATABASE\" /tmp/r.dump; rm -f /tmp/r.dump"], env=env, timeout=600)
        dataset = int(psql(src, cfg["db"], cfg["query"]))
        result["steps"].append({"step": "replica_cargada", "source_backup": dump, "sha256_verified": True, "dataset_count": dataset})

        t0 = time.time()
        run(["docker", "exec", src, "pg_basebackup", "-U", "pitr", "-D", bb, "-Ft", "-z", "-X", "fetch", "-c", "fast", "-l", f"pitr-{run_id}"], timeout=600)
        result["steps"].append({"step": "respaldo_base", "seconds": round(time.time() - t0, 2)})

        psql(src, cfg["db"], "CREATE TABLE IF NOT EXISTS pitr_marcas(id serial PRIMARY KEY, fase text NOT NULL, etiqueta text NOT NULL, creado timestamptz NOT NULL DEFAULT clock_timestamp())")
        for i in range(3):
            psql(src, cfg["db"], f"INSERT INTO pitr_marcas(fase, etiqueta) VALUES ('antes', 'registro-ficticio-antes-{i}')")
        psql(src, cfg["db"], "SELECT pg_switch_wal()")  # cierra el segmento de los datos ANTES
        time.sleep(2)
        target_time = psql(src, cfg["db"], "SELECT to_char(clock_timestamp() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS.US') || '+00'")
        time.sleep(2)
        for i in range(3):
            psql(src, cfg["db"], f"INSERT INTO pitr_marcas(fase, etiqueta) VALUES ('despues', 'registro-ficticio-despues-{i}')")
        commit_wall = time.time()
        segment = psql(src, cfg["db"], "SELECT pg_walfile_name(pg_current_wal_lsn())")
        # RPO observado: sin forzar el cambio de segmento; lo cierra archive_timeout.
        deadline = time.time() + archive_timeout * 3 + 60
        archived_after = None
        while time.time() < deadline:
            last = psql(src, cfg["db"], "SELECT coalesce(last_archived_wal,'') FROM pg_stat_archiver")
            if last and last >= segment:
                archived_after = round(time.time() - commit_wall, 1)
                break
            time.sleep(2)
        if archived_after is None:
            raise RuntimeError("El segmento con los datos recientes no se archivó en el tiempo esperado")
        stats = psql(src, cfg["db"], "SELECT archived_count||','||failed_count FROM pg_stat_archiver").split(",")
        result["steps"].append({"step": "archivado_wal", "segment": segment, "seconds_commit_to_archive": archived_after,
                                "archived_count": int(stats[0]), "failed_count": int(stats[1])})
        result["target_time_utc"] = target_time
        manifest = sha_manifest(src, f"/pitr/{run_id}/{target}")
        result["integrity_manifest"] = manifest

        # Monitoreo WAL: estado normal, crecimiento (umbral reducido a propósito) y fallo inyectado de archive_command.
        normal = check_wal(src, "pitr", cfg["db"], archive_dir=wal, name=f"{target}-pitr-lab")
        growth = check_wal(src, "pitr", cfg["db"], archive_dir=wal, warn_mb=1, name=f"{target}-pitr-lab-umbral-prueba")
        # Fallo realista: destino de archivado sin permiso de escritura (archive_command devuelve error).
        helper(f"chmod 500 {wal}")
        psql(src, cfg["db"], "INSERT INTO pitr_marcas(fase, etiqueta) VALUES ('monitor', 'prueba-fallo-archivado')")
        psql(src, cfg["db"], "SELECT pg_switch_wal()")
        deadline, failed = time.time() + 60, None
        while time.time() < deadline:
            failed = check_wal(src, "pitr", cfg["db"], archive_dir=wal, write_log=False)
            if failed["failure_active"]:
                break
            time.sleep(2)
        failed = check_wal(src, "pitr", cfg["db"], archive_dir=wal, name=f"{target}-pitr-lab-fallo-inyectado")
        helper(f"chmod 700 {wal}")
        result["wal_monitoring"] = {
            "normal": {k: normal[k] for k in ("result", "issues", "archived_count", "pg_wal_mb", "archive_mb")},
            "growth_threshold_test": {k: growth[k] for k in ("result", "issues")},
            "injected_archive_failure": {k: failed[k] for k in ("result", "issues", "failed_count")},
            "detected_ok": normal["result"] == "success" and growth["result"] == "warning" and failed["result"] == "failure",
        }

        # Integridad: el manifiesto SHA-256 se recalcula desde otro contenedor antes de restaurar.
        recheck = helper(f"cd /pitr/{run_id}/{target} && find ./base -type f -exec sha256sum {{}} + ; for f in $(cd /pitr/{run_id}/{target} && find ./wal -type f | sort); do sha256sum /pitr/{run_id}/{target}/$f | sed 's#/pitr/{run_id}/{target}/##'; done")
        recheck_map = dict(reversed(line.split(None, 1)) for line in recheck.splitlines() if line)
        mismatched = [name for name, digest in manifest.items() if recheck_map.get(name) != digest]
        result["integrity_verified_before_restore"] = not mismatched
        if mismatched:
            raise RuntimeError(f"Manifiesto SHA-256 no coincide: {mismatched}")

        # Recuperación aislada (sin red) al punto objetivo
        t_restore = time.time()
        helper(f"cd {base}/restore && tar -xzf {bb}/base.tar.gz && chmod 700 {base}/restore && touch recovery.signal && "
               f"printf \"restore_command = 'cp {wal}/%%f %%p'\\nrecovery_target_time = '{target_time}'\\nrecovery_target_action = 'promote'\\n\" >> postgresql.auto.conf")
        run(["docker", "run", "-d", "--name", rst, "--network", "none", "--user", "70:70", "--read-only", "--tmpfs", "/tmp",
             "--tmpfs", "/var/run/postgresql:uid=70,gid=70", "--security-opt", "no-new-privileges:true", "--cap-drop", "ALL",
             "--memory", "256m", "-v", f"{DATA_VOL}:/data", "-v", f"{ARCH_VOL}:/pitr:ro", "-e", f"PGDATA={base}/restore",
             IMAGE, "postgres"])
        deadline = time.time() + 180
        while time.time() < deadline:
            if subprocess.run(["docker", "exec", rst, "pg_isready", "-q"], capture_output=True).returncode == 0 and \
                    psql(rst, cfg["db"], "SELECT pg_is_in_recovery()") == "f":
                break
            time.sleep(1)
        else:
            raise RuntimeError("La instancia recuperada no se promovió")
        rto = round(time.time() - t_restore, 1)
        before = int(psql(rst, cfg["db"], "SELECT count(*) FROM pitr_marcas WHERE fase='antes'"))
        after = int(psql(rst, cfg["db"], "SELECT count(*) FROM pitr_marcas WHERE fase='despues'"))
        restored_dataset = int(psql(rst, cfg["db"], cfg["query"]))
        stop_line = next((l for l in subprocess.run(["docker", "logs", rst], capture_output=True, text=True).stderr.splitlines()
                          if "recovery stopping before" in l or "recovery stopping after" in l), "")
        ok = before == 3 and after == 0 and restored_dataset >= cfg["minimum"] and result["wal_monitoring"]["detected_ok"]
        result.update({
            "restore": {"rows_before_present": before, "rows_after_present": after, "dataset_count": restored_dataset,
                        "rto_technical_seconds": rto, "recovery_log": stop_line.split("LOG:")[-1].strip()},
            "rpo": {"objective_seconds": cfg["rpo_objetivo_s"], "observed_seconds_commit_to_archive": archived_after,
                    "worst_case_bound_seconds": archive_timeout, "meets_objective": archived_after <= cfg["rpo_objetivo_s"]},
            "result": "success" if ok else "failure",
        })
        log_line(target, "success" if ok else "failure", f"pitr_rto_s={rto} rpo_obs_s={archived_after}")
    except Exception as exc:  # noqa: BLE001 - se registra cualquier fallo como evidencia
        result.update({"result": "failure", "error": str(exc)[-600:]})
        log_line(target, "failure", "pitr_test_error")
    finally:
        for name in (src, rst):
            subprocess.run(["docker", "rm", "-f", name], capture_output=True)  # sólo contenedores efímeros; los volúmenes se conservan
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", nargs="+", default=["academic", "identity"], choices=list(TARGETS))
    parser.add_argument("--archive-timeout", type=int, default=60)
    args = parser.parse_args()
    run(["docker", "volume", "create", DATA_VOL])
    run(["docker", "volume", "create", ARCH_VOL])
    helper("chown 70:70 /data /pitr && chmod 700 /data /pitr", user="0:0")
    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    secrets_env = env_file()
    results = [pitr(t, run_id, args.archive_timeout, secrets_env) for t in args.targets]
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"timestamp": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "run_id": run_id,
              "scope": "Réplicas aisladas cargadas con los respaldos reales; bases principales sin cambios",
              "result": "success" if all(r["result"] == "success" for r in results) else "failure", "results": results}
    path = OUT / f"pitr-{run_id}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in results:
        print(f"{r['target']}: {r['result']} " + (f"rto_s={r['restore']['rto_technical_seconds']} rpo_obs_s={r['rpo']['observed_seconds_commit_to_archive']} antes={r['restore']['rows_before_present']} despues={r['restore']['rows_after_present']}" if 'restore' in r else r.get('error', '')))
    print(f"evidencia=evidencias/pitr/{path.name}")
    if report["result"] != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()
