"""Registro operativo del SGSI: incidentes, cambios, solicitudes de acceso, activos y evaluación de controles.

Base SQLite en evidencias/gestion/registro-sgsi.db con bitácora de auditoría encadenada (SHA-256).
Cada registro indica su origen: `real-laboratorio` (hecho ocurrido en este laboratorio) o
`ejercicio` (caso de práctica con identidades ficticias). No representa aprobaciones institucionales.

Ejemplos:
  python scripts/gestion_sgsi.py incidente abrir --titulo "..." --severidad alta --origen real-laboratorio --evidencia ruta
  python scripts/gestion_sgsi.py incidente cerrar INC-001 --resolucion "..." --leccion "..."
  python scripts/gestion_sgsi.py cambio registrar --titulo "..." --tipo normal --riesgo R-009 --aprobado-por "usuario del laboratorio" --estado implementado
  python scripts/gestion_sgsi.py acceso solicitar --solicitante docente01 --recurso /administracion --rol administrativo --justificacion "..."
  python scripts/gestion_sgsi.py acceso resolver ACC-001 --decision denegada --motivo "..."
  python scripts/gestion_sgsi.py evaluacion importar            # importa la última validación integral
  python scripts/gestion_sgsi.py exportar                       # genera governance/registros-operativos.md
"""

import argparse
import datetime as dt
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "evidencias" / "gestion" / "registro-sgsi.db"
EXPORT = ROOT / "governance" / "registros-operativos.md"
TABLES = {
    "incidentes": ("INC", "titulo, severidad, origen, estado, detectado, contencion, resolucion, leccion, riesgo, evidencia, cerrado"),
    "cambios": ("CHG", "titulo, tipo, riesgo, descripcion, rollback, aprobado_por, estado, ejecutado, evidencia, origen"),
    "accesos": ("ACC", "solicitante, recurso, rol, justificacion, origen, estado, decision, motivo, resuelto"),
    "activos": ("AST", "activo_id, evento, detalle, responsable, origen"),
    "evaluaciones": ("EVA", "control, resultado, detalle, fuente"),
}


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    for table, (_, cols) in TABLES.items():
        db.execute(f"CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, creado TEXT NOT NULL, {', '.join(c + ' TEXT' for c in cols.split(', '))})")
    db.execute("CREATE TABLE IF NOT EXISTS auditoria (n INTEGER PRIMARY KEY, fecha TEXT, tabla TEXT, registro TEXT, accion TEXT, datos TEXT, hash_prev TEXT, hash TEXT)")
    return db


def audit(db, table, record_id, action, data):
    prev = db.execute("SELECT hash FROM auditoria ORDER BY n DESC LIMIT 1").fetchone()
    prev_hash = prev[0] if prev else "GENESIS"
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True)
    stamp = now()
    digest = hashlib.sha256(f"{prev_hash}|{stamp}|{table}|{record_id}|{action}|{payload}".encode()).hexdigest()
    db.execute("INSERT INTO auditoria(fecha,tabla,registro,accion,datos,hash_prev,hash) VALUES(?,?,?,?,?,?,?)",
               (stamp, table, record_id, action, payload, prev_hash, digest))


def insert(db, table, values):
    prefix = TABLES[table][0]
    count = db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    record_id = f"{prefix}-{count + 1:03d}"
    values = {k: v for k, v in values.items() if v is not None}
    cols = ["id", "creado", *values]
    db.execute(f"INSERT INTO {table}({', '.join(cols)}) VALUES({', '.join('?' * len(cols))})", [record_id, now(), *values.values()])
    audit(db, table, record_id, "crear", values)
    db.commit()
    return record_id


def update(db, table, record_id, values):
    values = {k: v for k, v in values.items() if v is not None}
    if not db.execute(f"SELECT 1 FROM {table} WHERE id=?", (record_id,)).fetchone():
        raise SystemExit(f"ERROR: {record_id} no existe")
    db.execute(f"UPDATE {table} SET {', '.join(k + '=?' for k in values)} WHERE id=?", [*values.values(), record_id])
    audit(db, table, record_id, "actualizar", values)
    db.commit()


def verify_audit(db):
    prev = "GENESIS"
    for n, fecha, tabla, registro, accion, datos, hash_prev, digest in db.execute("SELECT * FROM auditoria ORDER BY n"):
        expected = hashlib.sha256(f"{prev}|{fecha}|{tabla}|{registro}|{accion}|{datos}".encode()).hexdigest()
        if hash_prev != prev or digest != expected:
            return f"auditoría alterada en la entrada {n}"
        prev = digest
    return None


def open_incident(titulo, severidad, origen, evidencia=None, riesgo=None, contencion=None):
    """API usada por otros scripts (p. ej. la compuerta DLP)."""
    db = connect()
    try:
        return insert(db, "incidentes", {"titulo": titulo, "severidad": severidad, "origen": origen, "estado": "abierto",
                                          "detectado": now(), "evidencia": evidencia, "riesgo": riesgo, "contencion": contencion})
    finally:
        db.close()


def export(db):
    lines = ["# Registros operativos del SGSI (laboratorio)", "",
             f"Exportado: {now()} desde `evidencias/gestion/registro-sgsi.db`. Origen `real-laboratorio` = hecho ocurrido en este laboratorio; "
             "`ejercicio` = caso de práctica con identidades ficticias. Ninguna entrada representa una aprobación institucional; "
             "\"aprobado_por\" refleja la autorización dada por el usuario del laboratorio en la conversación de trabajo.", ""]
    problem = verify_audit(db)
    lines += [f"Integridad de la bitácora de auditoría: {'**ALTERADA** — ' + problem if problem else 'verificada (cadena SHA-256)'}; "
              f"entradas: {db.execute('SELECT count(*) FROM auditoria').fetchone()[0]}.", ""]
    for table in TABLES:
        rows = [dict(r) for r in db.execute(f"SELECT * FROM {table} ORDER BY id")]
        lines += [f"## {table.capitalize()} ({len(rows)})", ""]
        if not rows:
            lines += ["Sin registros.", ""]
            continue
        cols = list(rows[0])
        lines += ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
        lines += ["| " + " | ".join(str(r[c] or "").replace("|", "\\|").replace("\n", " ") for c in cols) + " |" for r in rows]
        lines.append("")
    EXPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="area", required=True)
    inc = sub.add_parser("incidente").add_subparsers(dest="accion", required=True)
    a = inc.add_parser("abrir")
    for f in ("titulo", "severidad", "origen"):
        a.add_argument(f"--{f}", required=True)
    for f in ("evidencia", "riesgo", "contencion", "detectado"):
        a.add_argument(f"--{f}")
    c = inc.add_parser("cerrar")
    c.add_argument("id")
    c.add_argument("--resolucion", required=True)
    c.add_argument("--leccion")
    c.add_argument("--contencion")
    chg = sub.add_parser("cambio").add_subparsers(dest="accion", required=True)
    r = chg.add_parser("registrar")
    for f in ("titulo", "tipo", "riesgo", "estado"):
        r.add_argument(f"--{f}", required=True)
    for f in ("descripcion", "rollback", "aprobado-por", "ejecutado", "evidencia"):
        r.add_argument(f"--{f}")
    r.add_argument("--origen", default="real-laboratorio")
    u = chg.add_parser("actualizar")
    u.add_argument("id")
    for f in ("estado", "ejecutado", "evidencia", "aprobado-por"):
        u.add_argument(f"--{f}")
    acc = sub.add_parser("acceso").add_subparsers(dest="accion", required=True)
    s = acc.add_parser("solicitar")
    for f in ("solicitante", "recurso", "rol", "justificacion"):
        s.add_argument(f"--{f}", required=True)
    s.add_argument("--origen", default="ejercicio")
    rs = acc.add_parser("resolver")
    rs.add_argument("id")
    rs.add_argument("--decision", required=True, choices=["aprobada", "denegada"])
    rs.add_argument("--motivo", required=True)
    ast = sub.add_parser("activo")
    ast.add_argument("--activo-id", required=True)
    ast.add_argument("--evento", required=True)
    ast.add_argument("--detalle", required=True)
    ast.add_argument("--responsable", required=True)
    ast.add_argument("--origen", default="real-laboratorio")
    ev = sub.add_parser("evaluacion").add_subparsers(dest="accion", required=True)
    ev.add_parser("importar")
    sub.add_parser("exportar")
    sub.add_parser("verificar")
    args = parser.parse_args()
    db = connect()
    try:
        if args.area == "incidente" and args.accion == "abrir":
            print("OK:", insert(db, "incidentes", {"titulo": args.titulo, "severidad": args.severidad, "origen": args.origen, "estado": "abierto",
                                                   "detectado": args.detectado or now(), "evidencia": args.evidencia, "riesgo": args.riesgo, "contencion": args.contencion}))
        elif args.area == "incidente":
            update(db, "incidentes", args.id, {"estado": "cerrado", "resolucion": args.resolucion, "leccion": args.leccion,
                                               "contencion": args.contencion, "cerrado": now()})
            print("OK: cerrado", args.id)
        elif args.area == "cambio" and args.accion == "registrar":
            print("OK:", insert(db, "cambios", {"titulo": args.titulo, "tipo": args.tipo, "riesgo": args.riesgo, "descripcion": args.descripcion,
                                                "rollback": args.rollback, "aprobado_por": args.aprobado_por, "estado": args.estado,
                                                "ejecutado": args.ejecutado, "evidencia": args.evidencia, "origen": args.origen}))
        elif args.area == "cambio":
            update(db, "cambios", args.id, {"estado": args.estado, "ejecutado": args.ejecutado, "evidencia": args.evidencia, "aprobado_por": args.aprobado_por})
            print("OK: actualizado", args.id)
        elif args.area == "acceso" and args.accion == "solicitar":
            print("OK:", insert(db, "accesos", {"solicitante": args.solicitante, "recurso": args.recurso, "rol": args.rol,
                                                "justificacion": args.justificacion, "origen": args.origen, "estado": "pendiente"}))
        elif args.area == "acceso":
            update(db, "accesos", args.id, {"estado": "resuelta", "decision": args.decision, "motivo": args.motivo, "resuelto": now()})
            print("OK: resuelto", args.id)
        elif args.area == "activo":
            print("OK:", insert(db, "activos", {"activo_id": args.activo_id, "evento": args.evento, "detalle": args.detalle,
                                                "responsable": args.responsable, "origen": args.origen}))
        elif args.area == "evaluacion":
            latest = sorted((ROOT / "evidencias" / "automatizacion").glob("validacion-sgsi-*.json"), key=lambda p: p.stat().st_mtime)[-1]
            data = json.loads(latest.read_text(encoding="utf-8-sig"))
            for item in data["resultados"]:
                insert(db, "evaluaciones", {"control": item["control"], "resultado": item["estado"],
                                            "detalle": item["detalle"].strip().splitlines()[-1][:300] if item["detalle"].strip() else "", "fuente": latest.name})
            print(f"OK: evaluaciones_importadas={len(data['resultados'])} fuente={latest.name}")
        elif args.area == "verificar":
            problem = verify_audit(db)
            print(("ERROR: " + problem) if problem else f"OK: auditoria_verificada entradas={db.execute('SELECT count(*) FROM auditoria').fetchone()[0]}")
            raise SystemExit(1 if problem else 0)
        if args.area != "verificar":
            export(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
