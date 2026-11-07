"""Genera inventario, BIA, riesgos, matrices de calor, OCTAVE, tratamiento, SoA, BCP y DRP.

Los valores de negocio son supuestos académicos; los tiempos de laboratorio se leen de las
evidencias JSON más recientes, sin extrapolarlos a la universidad.
"""

import csv
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "governance"
EVID = ROOT / "evidencias"
OUT.mkdir(exist_ok=True)
STAMP = dt.datetime.now().astimezone().isoformat(timespec="seconds")
DISCLAIMER = "Supuestos académicos pendientes de validación y aprobación por responsables institucionales; no provienen de entrevistas ni de datos financieros reales."


def write_csv(name, rows):
    path = OUT / name
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def table(rows, fields=None):
    fields = fields or list(rows[0])
    def clean(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join("---" for _ in fields) + "|"]
    lines += ["| " + " | ".join(clean(row.get(field, "")) for field in fields) + " |" for row in rows]
    return "\n".join(lines)


def latest(folder, pattern):
    files = sorted((EVID / folder).glob(pattern), key=lambda p: p.stat().st_mtime)
    if not files:
        return None, None
    return files[-1], json.loads(files[-1].read_text(encoding="utf-8-sig"))


def level(score):
    return "Bajo" if score <= 4 else "Moderado" if score <= 9 else "Alto" if score <= 15 else "Crítico"


# ---------------------------------------------------------------- Inventario
assets = [
    ("ACT-001","Host Windows/Docker Desktop","Infraestructura","TI UVCG","Administrador del laboratorio","Local","Contenedores y volúmenes del SGSI",3,5,5,"Crítica","Energía; hardware; Docker Desktop","Implementado"),
    ("ACT-002","Redes Docker segmentadas","Red","Seguridad TI","Administrador del laboratorio","Local","Flujos entre DMZ, aplicaciones, datos e identidad",3,5,5,"Crítica","ACT-001; compose.yaml","Implementado"),
    ("ACT-003","API académica Flask/Gunicorn","Aplicación","Dirección Académica","TI Aplicaciones","Red apps","Cursos y decisiones RBAC",4,5,4,"Alta","ACT-005; ACT-006; ACT-002","Implementado"),
    ("ACT-004","Proxy Nginx/TLS","Aplicación perimetral","Seguridad TI","TI Infraestructura","DMZ Docker","Solicitudes HTTPS y logs de acceso",3,5,5,"Crítica","ACT-003; ACT-013; ACT-002","Implementado"),
    ("ACT-005","PostgreSQL académico","Base de datos","Dirección Académica","DBA/TI","Red datos","Información académica ficticia",5,5,5,"Crítica","ACT-001; ACT-010","Implementado"),
    ("ACT-006","Keycloak","Identidad","Seguridad TI","IAM/TI","Red identidad/apps","Identidades, roles y eventos de autenticación ficticios",5,5,5,"Crítica","ACT-007; ACT-004","Implementado"),
    ("ACT-007","PostgreSQL de identidad","Base de datos","Seguridad TI","DBA/IAM","Red identidad","Configuración, usuarios y credenciales derivadas",5,5,5,"Crítica","ACT-001; ACT-010","Implementado"),
    ("ACT-008","SIEM ligero SQLite","Monitoreo","Seguridad TI","Analista de Seguridad","Host local","Eventos saneados y alertas",4,5,4,"Alta","Docker logs; ACT-009","Implementado"),
    ("ACT-009","Suricata offline (7 reglas)","IDS","Seguridad TI","Analista de Seguridad","Perfil Docker aislado (sin red)","PCAP sintético y alertas EVE",3,5,3,"Alta","Reglas IDS; ACT-008","Implementado parcial (offline)"),
    ("ACT-010","Repositorio local de backups cifrados","Respaldo","TI UVCG","DBA/TI","Disco local","Copias cifradas de ACT-005 y ACT-007",5,5,5,"Crítica","ACT-001; ACT-011","Implementado"),
    ("ACT-011","Secretos locales .env","Información de autenticación","Seguridad TI","Administrador del laboratorio","Host local, ignorado por Git","Claves de DB, IAM y cifrado",5,5,5,"Crítica","ACL del host; gestión manual","Implementado laboratorio"),
    ("ACT-012","Código y configuración SGSI","Software/Información","TI UVCG","DevSecOps","Workspace local","Código, Compose, Terraform y políticas",4,5,4,"Alta","ACT-001; control de versiones futuro","Implementado"),
    ("ACT-013","Certificado y clave TLS de laboratorio","Criptográfico","Seguridad TI","TI Infraestructura","Host/volumen TLS","Identidad TLS autofirmada del laboratorio",5,5,4,"Alta","ACT-004; ACT-011","Implementado laboratorio"),
    ("ACT-014","Evidencias técnicas y documentos SGSI","Información","Responsable SGSI","Equipo del proyecto","Workspace local","Resultados, matrices y reportes saneados",4,5,4,"Alta","ACT-001; ACT-012","Implementado"),
    ("ACT-015","Entorno híbrido AWS (VPC multi-AZ)","Cloud","TI UVCG","Cloud/DevSecOps","AWS us-east-1","Redes, IAM, monitoreo y recuperación",4,5,5,"Crítica","Cuenta AWS, presupuesto, conectividad","Planificado"),
    ("ACT-016","Repositorio offsite/inmutable","Respaldo","TI UVCG","DBA/Continuidad","Por definir","Segunda copia y retención institucional",5,5,5,"Crítica","Proveedor/ubicación aprobados","Planificado"),
    ("ACT-017","SIEM empresarial","Seguridad","Seguridad TI","SOC/Proveedor","Por definir","Telemetría institucional y casos de uso",5,5,5,"Crítica","Licencia, almacenamiento, personal","Planificado"),
    ("ACT-018","MDM/EDR institucional","Endpoint","Seguridad TI","Soporte/SOC","Dispositivos institucionales","Postura, cumplimiento y respuesta endpoint",5,5,4,"Alta","Licencias y enrolamiento","Planificado"),
    ("ACT-019","Plataforma virtual de aprendizaje","Aplicación","Dirección Académica","TI Aplicaciones","Escenario institucional","Contenido, evaluaciones y actividad docente",5,5,5,"Crítica","Identidad; red; proveedores","Académico no implementado"),
    ("ACT-020","Sistema financiero/pagos","Aplicación","Dirección Financiera","TI/Finanzas","Escenario institucional","Pagos y registros financieros",5,5,5,"Crítica","Banca; identidad; cumplimiento","Académico no implementado"),
    ("ACT-021","Correo/comunicaciones","Servicio","Comunicación Institucional","TI/Proveedor","Escenario institucional","Mensajes y notificaciones",4,4,5,"Alta","Proveedor; DNS; identidad","Académico no implementado"),
    ("ACT-022","Monitor de disponibilidad continuo (uptime-monitor)","Monitoreo","Seguridad TI","Analista de Seguridad","Red DMZ Docker","Estado y latencia de Nginx, API y Keycloak",2,4,4,"Media","ACT-004; ACT-008","Implementado"),
    ("ACT-023","Laboratorio PITR y archivo WAL aislado","Respaldo","TI UVCG","DBA/Continuidad","Volúmenes sgsi_pitr_* (red recovery/none)","Respaldos base y segmentos WAL de réplicas",5,5,4,"Alta","ACT-010; ACT-011","Implementado (réplicas); principales preparado"),
    ("ACT-024","Registro operativo del SGSI","Información","Responsable SGSI","Equipo del proyecto","evidencias/gestion","Incidentes, cambios, accesos, activos y evaluaciones",4,5,3,"Alta","ACT-014","Implementado"),
    # Activos AWS (evidencias/aws/ARQUITECTURA-AWS.md): S3/IAM/Budget en Terraform validado; el resto diseñado.
    ("ACT-030","Cuenta AWS del SGSI (plan Free)","Servicio cloud","Dirección TI","Operador de plataforma","AWS us-east-1","Recursos del laboratorio híbrido",3,4,3,"Alta","ACT-015","Planificado"),
    ("ACT-031","VPC, subredes y grupos de seguridad AWS","Red","Seguridad TI","Operador de plataforma","AWS us-east-1","Flujos DMZ/apps/datos/endpoints privados",3,5,4,"Alta","ACT-030; ACT-015","Planificado"),
    ("ACT-032","AWS KMS / Secrets Manager del SGSI","Criptográfico","Seguridad TI","Administrador de seguridad","AWS us-east-1","Secretos y certificados",5,5,4,"Crítica","ACT-030; ACT-031","Planificado"),
    ("ACT-033","Bucket S3 privado (evidencias e intercambio)","Información","Responsable SGSI","Operador de plataforma","AWS us-east-1","Evidencias y copias cifradas ficticias",4,5,3,"Alta","ACT-031; ACT-032; ACT-011","Planificado"),
    ("ACT-034","CloudTrail / GuardDuty / Security Hub","Monitoreo","Seguridad TI","Analista de seguridad","AWS us-east-1","Registros de actividad y diagnósticos",4,5,3,"Alta","ACT-030","Planificado"),
    ("ACT-035","AWS Backup / S3 Object Lock","Respaldo","TI UVCG","Operador de respaldo","AWS us-east-1","Copias de servidores locales",5,5,4,"Alta","ACT-030; ACT-001","Planificado"),
    ("ACT-036","Conectividad híbrida (AWS Site-to-Site VPN)","Red","Redes","Operador de redes","AWS + campus","Tráfico cifrado campus-AWS",4,5,3,"Alta","ACT-001; ACT-031","Planificado"),
    ("ACT-037","Código IaC y estado de Terraform","Software/Información","DevSecOps","Operador de plataforma","Repositorio + backend Storage","Definición de infraestructura; estado sensible",4,5,3,"Alta","ACT-030","Implementado (código validado); estado inexistente"),
    ("ACT-038","Guardrails AWS (Budgets, AWS Config) y presupuesto","Gobierno","Responsable SGSI","Finanzas/SGSI","AWS","Reglas de cumplimiento y alertas de gasto",2,4,2,"Media","ACT-030","Planificado"),
]
asset_fields = ["id","activo","tipo","propietario","custodio","ubicacion","informacion_procesada","confidencialidad_1_5","integridad_1_5","disponibilidad_1_5","criticidad","dependencias","estado_real"]
asset_rows = [dict(zip(asset_fields, row)) for row in assets]
write_csv("inventario-activos.csv", asset_rows)
estado_counts = defaultdict(int)
for row in asset_rows:
    estado_counts["Implementado" if row["estado_real"].startswith("Implementado") else row["estado_real"]] += 1
(OUT / "inventario-activos.md").write_text(
    f"# Inventario de activos del SGSI UVCG\n\nGenerado: {STAMP}. {DISCLAIMER}\n\n"
    "Escala CIA: 1 insignificante, 2 baja, 3 moderada, 4 alta, 5 crítica. Criticidad del activo = máximo de C/I/A, "
    "ajustado por dependencia transversal.\n\n"
    "Clasificación por estado real: **Implementado** = existe y se prueba en el laboratorio; **Planificado** = diseñado "
    "o requerido, sin despliegue; **Académico no implementado** = sólo forma parte del escenario universitario.\n\n"
    + "Resumen: " + "; ".join(f"{k}: {v}" for k, v in sorted(estado_counts.items())) + ".\n\n"
    + table(asset_rows), encoding="utf-8")
asset_ids = {row["id"] for row in asset_rows}

# ---------------------------------------------------------------- BIA
impact_scales = [
    {"nivel": 1, "operativo": "Sin efecto perceptible", "financiero": "< Q10,000", "academico": "Sin efecto en actividades", "reputacional": "Sin difusión", "legal": "Sin incumplimiento"},
    {"nivel": 2, "operativo": "Demora menor con alternativa", "financiero": "Q10,000–50,000", "academico": "Reprogramación menor", "reputacional": "Quejas aisladas", "legal": "Incumplimiento interno menor"},
    {"nivel": 3, "operativo": "Proceso degradado < 1 día", "financiero": "Q50,000–250,000", "academico": "Afecta a un grupo de cursos", "reputacional": "Difusión local", "legal": "Observación de ente regulador o contractual"},
    {"nivel": 4, "operativo": "Proceso detenido en periodo normal", "financiero": "Q250,000–1,000,000", "academico": "Afecta a una facultad o evaluación", "reputacional": "Medios regionales/redes", "legal": "Sanción o reclamo formal probable"},
    {"nivel": 5, "operativo": "Proceso detenido en periodo crítico", "financiero": "> Q1,000,000", "academico": "Afecta a toda la población estudiantil", "reputacional": "Cobertura nacional/pérdida de confianza", "legal": "Sanción grave o exposición de datos personales"},
]
bia_fields = ["id","proceso","responsable","descripcion","dependencias_tecnologicas","activos","impacto_operativo_1_5","impacto_financiero_1_5","impacto_academico_1_5","impacto_reputacional_1_5","impacto_legal_1_5","rto_horas","rpo_horas","mtpd_horas","criticidad","justificacion","estado_datos"]
bia_data = [
    ("PROC-001","Inscripción y matrícula","Registro Académico","Alta y modificación de matrícula estudiantil","Identidad; portal; base académica; pagos","ACT-005; ACT-006; ACT-020",5,4,5,5,4,4,1,12,"Crítica","La indisponibilidad en ventanas de inscripción detiene el ingreso académico y puede afectar ingresos.",DISCLAIMER),
    ("PROC-002","Gestión académica","Dirección Académica","Cursos, calificaciones, expedientes y programación","API; base académica; identidad","ACT-003; ACT-005; ACT-006",5,3,5,4,5,8,4,24,"Crítica","La integridad de expedientes es esencial y existen obligaciones de conservación/privacidad.",DISCLAIMER),
    ("PROC-003","Aprendizaje virtual","Dirección Académica","Entrega de contenido, tareas, evaluación y clases","LMS; identidad; comunicaciones; Internet","ACT-006; ACT-019; ACT-021",5,3,5,4,3,4,1,12,"Crítica","Una interrupción durante evaluaciones afecta directamente continuidad docente.",DISCLAIMER),
    ("PROC-004","Identidad y autenticación","Seguridad TI","Autenticación, MFA, sesiones y roles","Keycloak; DB identidad; TLS; DNS/tiempo","ACT-006; ACT-007; ACT-013",5,4,5,5,5,2,0.25,4,"Crítica","Es dependencia transversal; su caída bloquea múltiples procesos.",DISCLAIMER),
    ("PROC-005","Gestión financiera y pagos","Dirección Financiera","Cobros, conciliación y obligaciones financieras","Sistema financiero; identidad; banca","ACT-006; ACT-020",4,5,3,5,5,8,1,24,"Crítica","Errores o indisponibilidad afectan ingresos, conciliación y obligaciones regulatorias.",DISCLAIMER),
    ("PROC-006","Servicios administrativos","Administración","RRHH, compras, expedientes y soporte administrativo","Identidad; sistemas administrativos; correo","ACT-006; ACT-021",3,3,3,3,4,24,8,72,"Alta","Tolera mayor demora fuera de cierres, pero maneja información confidencial.",DISCLAIMER),
    ("PROC-007","Correo y comunicaciones","Comunicación Institucional","Avisos, coordinación y comunicaciones de emergencia","Correo; identidad; DNS; Internet","ACT-006; ACT-021",4,3,4,5,3,8,4,24,"Alta","Es canal operativo y de crisis; existen alternativas temporales limitadas.",DISCLAIMER),
]
bia_rows = [dict(zip(bia_fields, row)) for row in bia_data]
impact_keys = [f for f in bia_fields if f.startswith("impacto_")]


def expected_criticality(row):
    values = [int(row[key]) for key in impact_keys]
    if values.count(5) >= 2:
        return "Crítica"
    return "Alta" if max(values) >= 4 else "Media" if max(values) == 3 else "Baja"


for row in bia_rows:
    rto, rpo, mtpd = float(row["rto_horas"]), float(row["rpo_horas"]), float(row["mtpd_horas"])
    assert rpo <= rto < mtpd and rto <= mtpd / 2, row["id"]
    assert row["criticidad"] == expected_criticality(row), row["id"]
    assert set(a.strip() for a in row["activos"].split(";")) <= asset_ids, row["id"]
write_csv("bia.csv", bia_rows)
_, api_cont = latest("recovery", "continuidad-api-*.json")
_, iam_cont = latest("recovery", "continuidad-iam-*.json")
_, restore = latest("recovery", "restauracion-dual-*.json")
lab_note = []
if api_cont:
    lab_note.append(f"recuperación de la API en {api_cont['recovery_seconds']} s")
if iam_cont:
    lab_note.append(f"recuperación de Keycloak en {iam_cont['recovery_seconds']} s")
if restore:
    lab_note += [f"restauración aislada {r['target']} en {r['elapsed_seconds']} s" for r in restore.get("results", [])]
(OUT / "bia.md").write_text(
    f"# Business Impact Analysis — UVCG\n\nGenerado: {STAMP}. **{DISCLAIMER}**\n\n"
    "## Escalas de impacto (1–5)\n\nUmbrales financieros en quetzales, propuestos para una universidad privada de ~3,000 estudiantes.\n\n"
    + table(impact_scales) +
    "\n\n## Reglas de coherencia verificadas automáticamente\n\n"
    "- RPO ≤ RTO < MTPD, y RTO ≤ 50 % del MTPD (margen para detección, decisión y comunicación).\n"
    "- Criticidad: **Crítica** si dos o más dimensiones valen 5; **Alta** si el máximo es 4 o una sola dimensión vale 5; **Media** si el máximo es 3; **Baja** en otro caso.\n"
    "- Todos los activos referenciados existen en `inventario-activos.csv`.\n\n"
    "## Evidencia técnica del laboratorio (no son objetivos institucionales)\n\n"
    + ("Última medición: " + "; ".join(lab_note) + ". " if lab_note else "")
    + "Estos tiempos corresponden a bases pequeñas y a un solo host; no incluyen detección, decisión, comunicación ni validación funcional, por lo que no se extrapolan al RTO universitario.\n\n"
    "## Matriz BIA\n\n" + table(bia_rows), encoding="utf-8")
process_ids = {row["id"] for row in bia_rows}

# ---------------------------------------------------------------- Riesgos
risk_fields = ["id","proceso","activo","amenaza","vulnerabilidad","escenario","probabilidad_1_5","impacto_1_5","riesgo_inherente","nivel_inherente","controles_existentes","efectividad_control_1_5","probabilidad_residual_1_5","impacto_residual_1_5","riesgo_residual","nivel_residual","responsable","evidencia","naturaleza_valoracion"]
# (id, proceso, activos, amenaza, vulnerabilidad, escenario, P, I, controles, efectividad, P_res, I_res, responsable, evidencia)
risk_data = [
    ("R-001","PROC-002","ACT-003; ACT-005","Acceso no autorizado","Token/rol comprometido","Un actor consulta información académica fuera de su función.",3,5,"OIDC; MFA; RBAC; TLS; logging; SIEM-RBAC-001",4,2,3,"Seguridad TI","scripts/pruebas_identidad.py; local/monitoring/rules.json; evidencias/siem/pipeline-siem-*.json"),
    ("R-002","PROC-004","ACT-006","Fuerza bruta/credential stuffing","Credenciales reutilizadas o intentos automatizados","Intentos reiterados buscan tomar una cuenta.",4,4,"MFA; bloqueo Keycloak; política contraseña; SIEM-AUTH-001; regla IDS 1000007",4,2,3,"IAM","local/identity/uvcg-realm.json; evidencias/siem/consulta-auth-denied-*.json; evidencias/ids/resultado.json"),
    ("R-003","PROC-002","ACT-005; ACT-014","Exposición de información","Manejo o transferencia inadecuada","Datos académicos o evidencias salen por canal no autorizado.",3,5,"Clasificación; compuerta DLP con bloqueo e incidentes; RBAC; redacción de secretos en SIEM",3,3,3,"Propietario de información","policies/clasificacion-informacion.md; evidencias/dlp/dlp-20261024-091533.json"),
    ("R-004","PROC-001","ACT-001","Interrupción de servicios","Dependencia de un único host local","Fallo de host/Docker detiene inscripción y servicios relacionados.",4,5,"Restart; healthchecks; backup; DRP laboratorio; prueba de continuidad API/IAM",2,3,5,"TI Infraestructura","evidencias/recovery/continuidad-api-*.json; evidencias/recovery/continuidad-iam-*.json"),
    ("R-005","PROC-002","ACT-005","Pérdida/corrupción de datos","Fallo lógico, humano o de almacenamiento","Se pierden registros académicos sin copia recuperable.",3,5,"Backup cifrado programado; SHA-256; restore aislado periódico",4,2,3,"DBA","evidencias/backup/backups-programados-*.json; evidencias/recovery/recuperacion-periodica-*.json"),
    ("R-006","PROC-004","ACT-007","Pérdida de identidades","Antes no existía backup validado de identidad","La base IAM se corrompe e impide autenticación.",3,5,"Backup cifrado identidad; restore con conteo de identidades",4,2,3,"IAM/DBA","evidencias/recovery/restauracion-dual-*.json"),
    ("R-007","PROC-002; PROC-004","ACT-010","Fallo de respaldos","Copia incompleta, clave ausente o tarea detenida","La recuperación falla cuando se requiere.",3,5,"Schedulers; manifiesto; SHA-256; alerta SIEM-BACKUP-001 probada con fallo controlado; prueba periódica",4,2,3,"DBA/Continuidad","local/backups/execution.log; evidencias/siem/consulta-backup-failure-*.json; scripts/prueba_recuperacion_periodica.ps1"),
    ("R-008","Todos","ACT-012","Configuración insegura","Cambio no validado o secreto expuesto","Una configuración introduce exposición o indisponibilidad.",3,4,"Compose validate; Trivy misconfig/secret; línea base SHA-256 de configuración",4,2,2,"DevSecOps","evidencias/security/trivy-fs.json; scripts/integridad_configuracion.py; evidencias/integridad/linea-base-configuracion.json"),
    ("R-009","PROC-002; PROC-004","ACT-005; ACT-007","Explotación de vulnerabilidades PostgreSQL","Imagen oficial con 1 critical y 25 high en Go stdlib de /usr/local/bin/gosu (componente eliminado en la imagen en uso)","Un componente vulnerable es explotado pese a que la DB no se publica.",4,5,"Imagen local-postgres-hardened:16 aplicada (gosu eliminado, UID 70); segmentación; sin puertos; read-only; reescaneo de imágenes en uso",4,2,3,"DBA/DevSecOps","evidencias/security/escaneo-imagenes-en-uso-post-upgrade.json; evidencias/security/trivy-antes-postgres-16-alpine-pre-upgrade.json; evidencias/postgres-upgrade/REPORTE-ACTUALIZACION-POSTGRESQL.md"),
    ("R-010","PROC-004","ACT-006","Explotación de vulnerabilidades Keycloak","2 high OpenJDK sin corrección publicada; escaneo JAR completado sin hallazgos","Una falla del runtime afecta IAM.",3,5,"No publicado directo; TLS proxy; cap_drop; MFA; monitoreo",3,2,5,"IAM/DevSecOps","evidencias/security/trivy-keycloak-full-image.json"),
    ("R-011","Todos","ACT-001; ACT-015; ACT-016","Desastre del sitio/equipo","Sin despliegue híbrido ni copia offsite","Pérdida del host destruye servicio y copias locales.",4,5,"Terraform preparado; backups locales",1,4,5,"Dirección TI","aws/main.tf; CIERRE_AWS.md"),
    ("R-012","Todos","ACT-008","Detección insuficiente","SIEM local sin HA/UEBA/agentes","Un incidente no es correlacionado o preservado oportunamente.",4,4,"SQLite sellado (hash encadenado); 11 reglas; monitor de disponibilidad continuo; vigilancia de contenedores; Suricata integrado",3,3,3,"Seguridad TI","evidencias/siem/pipeline-siem-*.json"),
    ("R-013","PROC-006","ACT-018","Malware en endpoints","Sin MDM/EDR real","Un endpoint comprometido roba sesión o información.",4,4,"Política BYOD; MFA; simulación de cumplimiento MDM; vigilancia de procesos en contenedores (no endpoints)",1,4,4,"Seguridad TI","policies/byod-mdm.md"),
    ("R-014","Todos","ACT-001","Incidente físico/ambiental","Sin sitio alterno ni controles físicos evaluados","Robo, incendio o energía afecta el único host.",3,5,"Backups locales; procedimientos",1,3,5,"Administración/TI","governance/bia.md; governance/drp.md"),
    ("R-015","PROC-002; PROC-004","ACT-011","Compromiso de clave de backup","Gestión local manual de secretos; ACL heredada de .env concede Modificar a Usuarios autentificados","Un actor descifra copias o impide recuperación.",2,5,"Secreto fuera del directorio de copias; .gitignore; cifrado AES-256; no se imprime",3,2,3,"Seguridad TI","local/.env.example; local/backup/backup-encrypted.sh"),
    ("R-016","PROC-004","ACT-006","Abuso de privilegios","Cuenta administrativa comprometida o mal utilizada","Se alteran roles o clientes IAM.",3,5,"MFA; eventos admin; mínimo privilegio; consola no publicada; regla IDS 1000005",4,2,3,"Responsable IAM","local/identity/uvcg-realm.json; local/ids/rules/uvcg.rules"),
    ("R-017","Todos","ACT-015","Configuración cloud insegura","Arquitectura aún no probada contra una cuenta real","Un futuro despliegue expone recursos o genera costos.",3,5,"Terraform validate; Trivy; compuerta de plan; bloqueo público S3",2,3,4,"Cloud/DevSecOps","evidencias/aws/validacion-terraform-aws-20261024.txt"),
    ("R-018","PROC-003; PROC-005; PROC-007","ACT-019; ACT-020; ACT-021","Fallo de tercero","Dependencia contractual no evaluada","Proveedor de LMS/pagos/correo interrumpe o expone datos.",3,4,"Requisitos preparados; no hay contratos reales",1,3,4,"Compras/Propietarios","governance/declaracion-aplicabilidad.md"),
    ("R-019","PROC-002; PROC-004","ACT-005; ACT-007; ACT-010","Pérdida de transacciones recientes","Backup diario sin archivado WAL/PITR","Tras una corrupción se pierden hasta 24 h de cambios, por encima del RPO propuesto (4 h académico, 15 min identidad).",3,4,"Backup diario cifrado; PITR validado en réplicas aisladas (RPO observado ≈ 56 s); monitor WAL; activación en principales pendiente de autorización",2,3,4,"DBA/Continuidad","evidencias/recovery/recuperacion-periodica-*.json; evidencias/pitr/pitr-*.json; local/compose.pitr.yaml"),
    ("R-020","Todos","ACT-030; ACT-038","Gasto cloud no controlado (RC-01)","Servicios con facturación por hora; presupuestos sólo notifican","Un despliegue o recurso olvidado genera costos no aprobados.",4,4,"Plan Free; presupuesto de gasto cero; compuerta de plan; procedimiento de retirada",3,2,3,"Responsable SGSI","evidencias/aws/COSTOS-AWS.md; evidencias/aws/RIESGOS-Y-RETIRADA-AWS.md"),
    ("R-021","Todos","ACT-037","Exposición del estado de Terraform (RC-05)","El estado puede contener identificadores y datos sensibles","El archivo de estado se filtra o se corrompe.",3,4,"Estado local fuera de Git (.gitignore); sin estado en el repositorio",3,2,4,"DevSecOps","aws/.gitignore; evidencias/aws/RIESGOS-Y-RETIRADA-AWS.md"),
    ("R-022","PROC-004","ACT-030; ACT-018","Licencias insuficientes MDM/EDR (RC-15)","Acceso condicional, PIM y MDM dependen de licencias","No pueden aplicarse controles de dispositivo y de acceso privilegiado en la nube.",3,4,"MFA de Keycloak; simulación MDM; roles IAM sin claves permanentes",2,3,3,"Dirección TI","evidencias/aws/COSTOS-AWS.md; scripts/mdm_cumplimiento.py"),
]
risk_rows = []
for (rid, proc, act, threat, vuln, scen, p, i, ctrls, eff, pr, ir, owner, ev) in risk_data:
    risk_rows.append(dict(zip(risk_fields, (rid, proc, act, threat, vuln, scen, p, i, p * i, level(p * i), ctrls, eff, pr, ir, pr * ir, level(pr * ir), owner, ev, DISCLAIMER))))
write_csv("matriz-riesgos.csv", risk_rows)

scale = """## Método y aceptación

Enfoque ISO/IEC 27005:2022 (identificación, análisis, evaluación) con la estructura de NIST SP 800-30 Rev. 1 (fuente/evento de amenaza, vulnerabilidad, probabilidad, impacto, riesgo).

| Valor | Probabilidad (12 meses) | Impacto |
|---|---|---|
| 1 | Raro: no se espera | Insignificante: sin efecto en procesos BIA |
| 2 | Improbable: podría ocurrir excepcionalmente | Menor: degradación tolerable dentro del RTO |
| 3 | Posible: ha ocurrido en instituciones similares | Moderado: afecta un proceso BIA cerca de su RTO |
| 4 | Probable: condiciones presentes y conocidas | Alto: supera el RTO/RPO de un proceso crítico |
| 5 | Casi cierto: se espera que ocurra | Crítico: supera el MTPD o expone datos personales |

Riesgo = P × I. **Criterios de aceptación:** 1–4 Bajo (aceptable por el propietario); 5–9 Moderado (tratar o aceptación documentada por el propietario); 10–15 Alto (tratamiento obligatorio; aceptación sólo por Dirección); 16–25 Crítico (prioridad inmediata; no aceptable).

El riesgo residual es una **re-estimación de P e I** tras los controles existentes (columnas `probabilidad_residual_1_5` e `impacto_residual_1_5`), apoyada en la efectividad del control (1 inexistente, 2 limitada, 3 parcial, 4 efectiva en laboratorio, 5 validada institucionalmente). Las cifras son estimaciones de escritorio, no mediciones objetivas.
"""
(OUT / "matriz-riesgos.md").write_text(f"# Análisis de riesgos ISO 27005 / NIST SP 800-30\n\nGenerado: {STAMP}. {DISCLAIMER}\n\n{scale}\n" + table(risk_rows), encoding="utf-8")


def heat_table(prob_key, imp_key):
    cells = defaultdict(list)
    for risk in risk_rows:
        cells[(int(risk[imp_key]), int(risk[prob_key]))].append(risk["id"])
    lines = ["| Impacto \\ Probabilidad | 1 | 2 | 3 | 4 | 5 |", "|---|---|---|---|---|---|"]
    for impact in range(5, 0, -1):
        lines.append(f"| **{impact}** | " + " | ".join(
            (", ".join(cells[(impact, p)]) or "—") + f" <sub>({level(impact * p)})</sub>" for p in range(1, 6)) + " |")
    return "\n".join(lines)


def level_counts(key):
    counts = defaultdict(int)
    for risk in risk_rows:
        counts[risk[key]] += 1
    return ", ".join(f"{name}: {counts[name]}" for name in ("Crítico", "Alto", "Moderado", "Bajo"))


heat = [
    "# Matrices de calor 5 × 5", "", f"Generado: {STAMP}. {DISCLAIMER}", "",
    "Cada ID corresponde a una fila de `matriz-riesgos.csv`; la celda muestra entre paréntesis el nivel de P × I.", "",
    "## Riesgo inherente", "", heat_table("probabilidad_1_5", "impacto_1_5"), "",
    f"Distribución inherente — {level_counts('nivel_inherente')}.", "",
    "## Riesgo residual (tras controles existentes)", "", heat_table("probabilidad_residual_1_5", "impacto_residual_1_5"), "",
    f"Distribución residual — {level_counts('nivel_residual')}.", "",
    "Leyenda: 1–4 Bajo; 5–9 Moderado; 10–15 Alto; 16–25 Crítico.",
]
(OUT / "matriz-calor.md").write_text("\n".join(heat), encoding="utf-8")

# ---------------------------------------------------------------- Tratamiento
treatment_fields = ["riesgo_id","estrategia","control_propuesto","referencia_iso_27001_27002_2022","responsable","prioridad","plazo_academico","estado","evidencia","riesgo_residual_esperado"]
strategies = {
"R-001":("Mitigar","Revisión trimestral de roles y pruebas RBAC","A.5.15; A.5.16; A.5.18; A.8.3","IAM","Alta","90 días","Implementado laboratorio","scripts/pruebas_identidad.py","4 Bajo"),
"R-002":("Mitigar","Alertar ráfagas y revisar bloqueo/adopción de MFA","A.5.17; A.8.5; A.8.16","IAM/SOC","Alta","30 días","Implementado laboratorio","local/monitoring/rules.json","4 Bajo"),
"R-003":("Mitigar","Compuerta DLP de transferencia (laboratorio) y DLP empresarial con etiquetado","A.5.12; A.5.13; A.5.14; A.8.12","Propietarios/Seguridad","Alta","180 días","Parcial (compuerta implementada)","scripts/dlp_compuerta.py","6 Moderado"),
"R-004":("Mitigar","Segundo nodo/sitio y automatización de recuperación","A.5.29; A.5.30; A.8.14","TI/Continuidad","Crítica","12 meses","Planificado","governance/drp.md","8 Moderado"),
"R-005":("Mitigar","Copia offsite/inmutable y restore trimestral","A.8.13; A.5.30","DBA","Alta","90 días","Parcial (offsite pendiente)","scripts/prueba_recuperacion_periodica.ps1","4 Bajo"),
"R-006":("Mitigar","Mantener backup IAM cifrado y prueba trimestral","A.8.13; A.5.30","IAM/DBA","Alta","90 días","Implementado laboratorio","scripts/restaurar_prueba.ps1","4 Bajo"),
"R-007":("Mitigar","Monitorear scheduler, alertar fallos y probar recuperación periódicamente","A.8.13; A.8.16","DBA/SOC","Alta","30 días","Implementado laboratorio","scripts/siem_pipeline.py","4 Bajo"),
"R-008":("Mitigar","Control de cambios, CI y línea base de integridad de configuración","A.8.9; A.8.25; A.8.29; A.8.32","DevSecOps","Alta","90 días","Parcial","scripts/integridad_configuracion.py","4 Bajo"),
"R-009":("Mitigar","Imagen PostgreSQL sin gosu aplicada a db e identity-db; reescaneo mensual y seguimiento de la imagen upstream","A.8.8; A.8.20; A.8.22","DBA/DevSecOps","Crítica","Aplicado 2026-10-24; revisión mensual","Implementado laboratorio","evidencias/postgres-upgrade/REPORTE-ACTUALIZACION-POSTGRESQL.md","4 Bajo"),
"R-010":("Mitigar","Seguir publicación de OpenJDK corregido en imagen Keycloak; reescaneo mensual","A.8.8; A.8.29","IAM/DevSecOps","Alta","Revisión mensual","Pendiente upstream","evidencias/security/registro-vulnerabilidades-detallado.md","8 Moderado"),
"R-011":("Mitigar","Aprobar copia offsite y arquitectura híbrida/DR","A.5.30; A.8.13; A.8.14","Dirección/TI","Crítica","12 meses","Requiere autorización","aws/main.tf","10 Alto"),
"R-012":("Mitigar","SIEM ligero sellado + monitor continuo; adoptar SIEM con HA/agentes/retención inmutable","A.8.15; A.8.16","Seguridad TI","Alta","12 meses","Parcial","scripts/siem_ligero.py","6 Moderado"),
"R-013":("Mitigar","Seleccionar MDM/EDR y acceso condicional (política y simulación de cumplimiento listas)","A.6.7; A.8.1; A.8.7","Seguridad/Soporte","Crítica","12 meses","Requiere licencia; simulación lista","scripts/mdm_cumplimiento.py","10 Alto"),
"R-014":("Transferir/Mitigar","Seguro, sitio alterno, energía y copia externa","A.7.5; A.7.11; A.5.30","Administración/TI","Alta","12 meses","Pendiente","governance/bcp.md","8 Moderado"),
"R-015":("Mitigar","Restringir ACL de .env (propuesto CHG-005), Vault/rotación y separación de funciones","A.5.17; A.8.24; A.8.3","Seguridad TI","Alta","180 días","Parcial; ACL pendiente de autorización","governance/registros-operativos.md","4 Bajo"),
"R-016":("Mitigar","PAM, revisión de eventos admin y doble control","A.5.3; A.8.2; A.8.15","IAM/Auditoría","Alta","180 días","Parcial","local/identity/uvcg-realm.json","6 Moderado"),
"R-017":("Evitar hasta aprobación","No desplegar; revisar plan, costos y guardrails","A.5.23; A.8.9; A.8.20","Cloud/DevSecOps","Alta","Antes de despliegue","Preparado","aws/main.tf","6 Moderado"),
"R-018":("Transferir/Mitigar","Due diligence, SLA, seguridad contractual y salida","A.5.19; A.5.20; A.5.21; A.5.22; A.5.23","Compras/Legal/TI","Alta","Antes de contratar","Pendiente","governance/declaracion-aplicabilidad.md","8 Moderado"),
"R-020":("Mitigar","Revisión del plan con revisar_plan.py, presupuesto con alertas y desactivación segura","A.5.23; A.8.32","Responsable SGSI","Alta","Antes de cada apply","Preparado","aws/scripts/revisar_plan.py","6 Moderado"),
"R-021":("Mitigar","Backend S3 privado con cifrado, versionado y bloqueo de estado","A.8.4; A.8.9","DevSecOps","Alta","Antes del despliegue institucional","Documentado","aws/.gitignore","6 Moderado"),
"R-022":("Transferir/Aceptar","Adoptar MDM/EDR con licencia académica o alternativa de código abierto (Wazuh)","A.5.15; A.8.2; A.8.1","Dirección TI","Media","Presupuesto institucional","Pendiente","evidencias/aws/COSTOS-AWS.md","6 Moderado"),
"R-019":("Mitigar","Archivado WAL/PITR (archive_timeout 900 s académico, 60 s identidad) en las bases principales","A.8.13; A.5.30","DBA/Continuidad","Alta","Al autorizar","Validado en réplicas; activación pendiente de autorización","local/compose.pitr.yaml","4 Bajo"),
}
assert set(strategies) == {row["id"] for row in risk_rows}
treatment_rows = [dict(zip(treatment_fields, (risk_id, *strategies[risk_id]))) for risk_id in sorted(strategies)]
write_csv("plan-tratamiento.csv", treatment_rows)
(OUT / "plan-tratamiento.md").write_text(
    f"# Plan de tratamiento de riesgos\n\nGenerado: {STAMP}. Plazos y responsables son propuestas académicas pendientes de aprobación. "
    "Toda referencia ISO corresponde a un control presente en la SoA (`declaracion-aplicabilidad.csv`).\n\n" + table(treatment_rows), encoding="utf-8")

# ---------------------------------------------------------------- SoA
controls_text = """5.1|Policies for information security
5.2|Information security roles and responsibilities
5.3|Segregation of duties
5.4|Management responsibilities
5.5|Contact with authorities
5.6|Contact with special interest groups
5.7|Threat intelligence
5.8|Information security in project management
5.9|Inventory of information and other associated assets
5.10|Acceptable use of information and other associated assets
5.11|Return of assets
5.12|Classification of information
5.13|Labelling of information
5.14|Information transfer
5.15|Access control
5.16|Identity management
5.17|Authentication information
5.18|Access rights
5.19|Information security in supplier relationships
5.20|Addressing information security within supplier agreements
5.21|Managing information security in the ICT supply chain
5.22|Monitoring, review and change management of supplier services
5.23|Information security for use of cloud services
5.24|Information security incident management planning and preparation
5.25|Assessment and decision on information security events
5.26|Response to information security incidents
5.27|Learning from information security incidents
5.28|Collection of evidence
5.29|Information security during disruption
5.30|ICT readiness for business continuity
5.31|Legal, statutory, regulatory and contractual requirements
5.32|Intellectual property rights
5.33|Protection of records
5.34|Privacy and protection of PII
5.35|Independent review of information security
5.36|Compliance with policies, rules and standards for information security
5.37|Documented operating procedures
6.1|Screening
6.2|Terms and conditions of employment
6.3|Information security awareness, education and training
6.4|Disciplinary process
6.5|Responsibilities after termination or change of employment
6.6|Confidentiality or non-disclosure agreements
6.7|Remote working
6.8|Information security event reporting
7.1|Physical security perimeters
7.2|Physical entry
7.3|Securing offices, rooms and facilities
7.4|Physical security monitoring
7.5|Protecting against physical and environmental threats
7.6|Working in secure areas
7.7|Clear desk and clear screen
7.8|Equipment siting and protection
7.9|Security of assets off-premises
7.10|Storage media
7.11|Supporting utilities
7.12|Cabling security
7.13|Equipment maintenance
7.14|Secure disposal or re-use of equipment
8.1|User endpoint devices
8.2|Privileged access rights
8.3|Information access restriction
8.4|Access to source code
8.5|Secure authentication
8.6|Capacity management
8.7|Protection against malware
8.8|Management of technical vulnerabilities
8.9|Configuration management
8.10|Information deletion
8.11|Data masking
8.12|Data leakage prevention
8.13|Information backup
8.14|Redundancy of information processing facilities
8.15|Logging
8.16|Monitoring activities
8.17|Clock synchronization
8.18|Use of privileged utility programs
8.19|Installation of software on operational systems
8.20|Networks security
8.21|Security of network services
8.22|Segregation of networks
8.23|Web filtering
8.24|Use of cryptography
8.25|Secure development life cycle
8.26|Application security requirements
8.27|Secure system architecture and engineering principles
8.28|Secure coding
8.29|Security testing in development and acceptance
8.30|Outsourced development
8.31|Separation of development, test and production environments
8.32|Change management
8.33|Test information
8.34|Protection of information systems during audit testing"""
# Implementado = configuración + prueba repetible + evidencia en el laboratorio.
# Parcial = documento, demostración o cobertura incompleta. El resto queda pendiente institucional.
evidence_by_control = {
    "5.9": ("I", "governance/inventario-activos.csv"),
    "5.15": ("I", "policies/matriz-acceso-zero-trust.md; scripts/pruebas_identidad.py"),
    "5.16": ("I", "local/identity/uvcg-realm.json; scripts/pruebas_identidad.py"),
    "5.17": ("I", "local/identity/uvcg-realm.json; scripts/generar_secretos_lab.ps1"),
    "5.18": ("I", "scripts/pruebas_identidad.py"),
    "5.30": ("I", "evidencias/recovery/recuperacion-periodica-*.json; evidencias/recovery/tarea-programada/ejecuciones.csv; evidencias/pitr/pitr-*.json"),
    "5.37": ("I", "governance/drp.md; policies/procedimiento-investigacion-incidentes.md"),
    "8.2": ("I", "local/identity/uvcg-realm.json; local/compose.yaml"),
    "8.3": ("I", "scripts/pruebas_identidad.py; local/api/app.py"),
    "8.5": ("I", "scripts/pruebas_identidad.py"),
    "8.8": ("I", "evidencias/security/registro-vulnerabilidades-detallado.md; evidencias/security/escaneo-imagenes-en-uso-post-upgrade.json"),
    "8.9": ("I", "local/compose.yaml; evidencias/integridad/linea-base-configuracion.json"),
    "8.13": ("I", "evidencias/backup/backups-programados-*.json; evidencias/recovery/restauracion-dual-*.json"),
    "8.15": ("I", "scripts/siem_ligero.py; evidencias/siem/pipeline-siem-*.json"),
    "8.6": ("I", "local/compose.yaml; local/monitoring/uptime_monitor.py"),
    "8.16": ("I", "local/monitoring/rules.json; evidencias/siem/alertas-*.json; evidencias/ids/resultado.json"),
    "8.20": ("I", "local/compose.yaml; evidencias/network/segmentacion-*.json"),
    "8.21": ("I", "local/nginx/default.conf; scripts/pruebas_locales.py"),
    "8.22": ("I", "evidencias/network/segmentacion-*.json"),
    "8.24": ("I", "local/backup/backup-encrypted.sh; local/nginx/default.conf"),
    "8.26": ("I", "local/api/app.py; scripts/pruebas_locales.py"),
    "8.27": ("I", "local/compose.yaml; policies/matriz-acceso-zero-trust.md"),
    "8.28": ("I", "evidencias/security/bandit.json"),
    "8.29": ("I", "scripts/ejecutar_seguridad.ps1; evidencias/security/trivy-fs.json"),
    "8.33": ("I", "scripts/generar_pcap_ids.py; scripts/pruebas_siem.py"),
    "8.34": ("I", "scripts/restaurar_prueba.ps1"),
    "5.1": ("P", "ESTADO_PROYECTO.md"), "5.2": ("P", "governance/bcp.md"), "5.3": ("P", "local/identity/uvcg-realm.json"),
    "5.7": ("P", "evidencias/security/registro-vulnerabilidades-detallado.md"), "5.8": ("P", "ESTADO_PROYECTO.md"),
    "5.10": ("P", "policies/clasificacion-informacion.md"), "5.12": ("P", "policies/clasificacion-informacion.md"),
    "5.13": ("P", "policies/clasificacion-informacion.md"), "5.14": ("P", "scripts/dlp_scan.py"),
    "5.19": ("P", "governance/plan-tratamiento.md"), "5.20": ("P", "governance/plan-tratamiento.md"),
    "5.21": ("P", "evidencias/security/registro-vulnerabilidades-detallado.md"), "5.22": ("P", "governance/plan-tratamiento.md"),
    "5.23": ("P", "aws/main.tf; CIERRE_AWS.md; evidencias/aws/ARQUITECTURA-AWS.md"), "5.24": ("I", "policies/procedimiento-investigacion-incidentes.md; governance/registros-operativos.md"),
    "5.25": ("P", "local/monitoring/rules.json; policies/procedimiento-investigacion-incidentes.md"),
    "5.26": ("I", "governance/registros-operativos.md"), "5.27": ("I", "governance/registros-operativos.md"),
    "5.28": ("P", "scripts/siem_ligero.py; evidencias/integridad/linea-base-configuracion.json"),
    "5.29": ("P", "governance/bcp.md"), "5.31": ("P", "governance/bia.md"), "5.33": ("P", "governance/drp.md"),
    "5.34": ("P", "scripts/siem_ligero.py; scripts/dlp_scan.py"), "5.36": ("P", "scripts/validar_sgsi.ps1"),
    "6.3": ("P", "policies/byod-mdm.md"), "6.7": ("P", "policies/byod-mdm.md"), "6.8": ("P", "policies/procedimiento-investigacion-incidentes.md"),
    "7.9": ("P", "policies/byod-mdm.md"), "7.10": ("P", "local/backup/backup-encrypted.sh"),
    "8.1": ("P", "local/mdm/politica-cumplimiento.json; evidencias/mdm/cumplimiento-mdm-*.json"), "8.4": ("P", "local/.gitignore"),
    "8.7": ("P", "scripts/vigilancia_contenedores.py; evidencias/edr/vigilancia-*.json"), "8.10": ("P", "local/backup/retention-policy.json; evidencias/retencion/simulacion-retencion-*.md"), "8.11": ("P", "scripts/siem_ligero.py"),
    "8.12": ("P", "scripts/dlp_compuerta.py; evidencias/dlp/compuerta-*.json"), "8.14": ("P", "aws/main.tf"), "8.17": ("P", "local/compose.yaml"),
    "8.18": ("P", "local/compose.yaml"), "8.19": ("P", "local/compose.yaml"), "8.25": ("P", "scripts/ejecutar_seguridad.ps1"),
    "8.31": ("P", "local/compose.yaml"), "8.32": ("I", "governance/registros-operativos.md; scripts/integridad_configuracion.py"),
}
group_justification = {
    "5": "Control organizacional necesario para gobernar el SGSI en el alcance universitario.",
    "6": "Aplica a personal docente, administrativo, estudiantes con funciones y terceros con acceso a información.",
    "7": "Aplica a instalaciones y equipos institucionales; el laboratorio local no lo cubre.",
    "8": "Aplica a la infraestructura local e híbrida prevista.",
}
risk_by_control = defaultdict(list)
for rid, refs in strategies.items():
    for ref in refs[2].split(";"):
        risk_by_control[ref.strip().removeprefix("A.")].append(rid)
soa_rows = []
for line in controls_text.splitlines():
    cid, title = line.split("|", 1)
    status_code, evidence = evidence_by_control.get(cid, ("N", "Sin evidencia técnica; requisito institucional pendiente"))
    status = {"I": "Implementado/validado en laboratorio", "P": "Parcial/preparado", "N": "Pendiente de implementación institucional"}[status_code]
    risks = sorted(set(risk_by_control[cid]))
    justification = group_justification[cid.split(".")[0]]
    if risks:
        justification += " Seleccionado en el tratamiento de " + ", ".join(risks) + "."
    soa_rows.append({
        "control_id": f"A.{cid}", "control_name": title, "applicable": "Sí", "justification": justification,
        "implementation_status": status, "related_risks": "; ".join(risks) or "Sin riesgo específico valorado aún",
        "evidence": evidence,
    })
assert len(soa_rows) == 93 and len({row["control_id"] for row in soa_rows}) == 93
assert set(evidence_by_control) <= {line.split("|")[0] for line in controls_text.splitlines()}
write_csv("declaracion-aplicabilidad.csv", soa_rows)
soa_counts = defaultdict(int)
for row in soa_rows:
    soa_counts[row["implementation_status"]] += 1
soa_intro = (
    f"# Declaración de Aplicabilidad (SoA) — borrador académico\n\nGenerado: {STAMP}. Contiene los 93 identificadores y títulos "
    "breves (en inglés, como figuran en la norma) del Anexo A de ISO/IEC 27001:2022, sin reproducir el texto normativo.\n\n"
    "**Aplicabilidad:** no se excluye ningún control porque el alcance es una universidad completa (personal, instalaciones, "
    "proveedores y TI híbrida); las exclusiones deben decidirse en el proceso formal de tratamiento. La SoA no demuestra conformidad ni certificación.\n\n"
    "**Estado:** *Implementado/validado en laboratorio* exige configuración, prueba repetible y evidencia; *Parcial/preparado* "
    "cubre políticas, demostraciones o cobertura incompleta; *Pendiente* no tiene evidencia técnica.\n\n"
    "Resumen: " + "; ".join(f"{k}: {v}" for k, v in sorted(soa_counts.items())) + ".\n\n"
    "Estructura verificada: 93 controles en 4 temas (5: 37 organizacionales, 6: 8 de personas, 7: 14 físicos, 8: 34 tecnológicos).\n\n"
)
assert [sum(1 for r in soa_rows if r["control_id"].startswith(f"A.{g}.")) for g in "5678"] == [37, 8, 14, 34]
(OUT / "declaracion-aplicabilidad.md").write_text(soa_intro + table(soa_rows), encoding="utf-8")

# ---------------------------------------------------------------- OCTAVE Allegro
impact_areas = [("Académico", 6), ("Reputación y confianza", 5), ("Legal/regulatorio", 4), ("Financiero", 3), ("Productividad/operación", 2), ("Seguridad y salud", 1)]
octave_assets = [
    {"id": "IA-01", "activo": "Expedientes y gestión académica", "contenedores_tecnicos": "ACT-003; ACT-005; ACT-010", "contenedores_personas": "Registro Académico, docentes", "propietario": "Dirección Académica",
     "C": "Sólo personal con rol docente/administrativo", "I": "Calificaciones sólo modificables por rol autorizado", "A": "RTO 8 h (PROC-002)", "requisito_principal": "Integridad"},
    {"id": "IA-02", "activo": "Identidades, credenciales y roles", "contenedores_tecnicos": "ACT-006; ACT-007; ACT-011; ACT-013", "contenedores_personas": "Administradores IAM", "propietario": "Seguridad TI",
     "C": "Hashes y secretos nunca expuestos", "I": "Roles alterados sólo con MFA y registro", "A": "RTO 2 h (PROC-004)", "requisito_principal": "Confidencialidad"},
    {"id": "IA-03", "activo": "Copias de respaldo", "contenedores_tecnicos": "ACT-010; ACT-011; ACT-016", "contenedores_personas": "DBA/Continuidad", "propietario": "TI UVCG",
     "C": "Cifradas con clave separada", "I": "SHA-256 verificado antes de restaurar", "A": "Disponibles fuera del host (pendiente)", "requisito_principal": "Disponibilidad"},
    {"id": "IA-04", "activo": "Registros y alertas de seguridad", "contenedores_tecnicos": "ACT-008; ACT-009; ACT-014", "contenedores_personas": "Analista de seguridad", "propietario": "Seguridad TI",
     "C": "Sin secretos ni datos personales", "I": "Eventos con hash y deduplicación", "A": "Retención 30 días", "requisito_principal": "Integridad"},
    {"id": "IA-05", "activo": "Información financiera y de pagos (escenario)", "contenedores_tecnicos": "ACT-020; ACT-006", "contenedores_personas": "Finanzas, proveedor bancario", "propietario": "Dirección Financiera",
     "C": "Datos de pago protegidos", "I": "Conciliación exacta", "A": "RTO 8 h (PROC-005)", "requisito_principal": "Integridad"},
]
# Impactos Alto=3, Medio=2, Bajo=1 por área, en el orden de impact_areas.
octave_scenarios = [
    ("OS-01", "IA-01", "Usuario interno con token válido", "Abuso de rol/API", "Modificación", "Media", (3, 2, 3, 1, 2, 1), "R-001", "Mitigar"),
    ("OS-02", "IA-02", "Atacante externo", "Credential stuffing contra Keycloak", "Divulgación", "Alta", (2, 3, 3, 2, 3, 1), "R-002", "Mitigar"),
    ("OS-03", "IA-02", "Atacante externo", "Explotación de vulnerabilidad en imagen", "Interrupción/divulgación", "Media", (3, 3, 3, 2, 3, 1), "R-009; R-010", "Mitigar"),
    ("OS-04", "IA-03", "Fallo técnico o ransomware", "Corrupción/borrado de copias en el mismo host", "Destrucción", "Media", (3, 3, 2, 3, 3, 1), "R-007; R-011; R-019", "Mitigar"),
    ("OS-05", "IA-03", "Insider/robo de equipo", "Obtención de la clave de cifrado", "Divulgación", "Baja", (2, 3, 3, 2, 1, 1), "R-015", "Mitigar"),
    ("OS-06", "IA-04", "Atacante que evade detección", "Ausencia de agentes y HA", "Interrupción de la detección", "Media", (2, 2, 2, 1, 2, 1), "R-012", "Diferir/mitigar"),
    ("OS-07", "IA-01", "Evento físico/ambiental", "Pérdida del único host", "Interrupción", "Media", (3, 3, 2, 3, 3, 1), "R-004; R-014", "Mitigar"),
    ("OS-08", "IA-05", "Proveedor externo", "Falla o brecha del tercero", "Divulgación/interrupción", "Media", (1, 3, 3, 3, 2, 1), "R-018", "Transferir"),
]
octave_rows = []
for sid, ia, actor, means, outcome, prob, impacts, risks, approach in octave_scenarios:
    score = sum(value * weight for value, (_, weight) in zip(impacts, impact_areas))
    pool = "Pool 1 (≥ 50)" if score >= 50 else "Pool 2 (40–49)" if score >= 40 else "Pool 3 (< 40)"
    octave_rows.append({"escenario": sid, "activo_info": ia, "actor": actor, "medio": means, "resultado": outcome,
                        "probabilidad_subjetiva": prob, **{name: v for (name, _), v in zip(impact_areas, impacts)},
                        "puntaje_relativo": score, "pool": pool, "enfoque": approach, "riesgos_vinculados": risks})
octave_rows.sort(key=lambda row: -row["puntaje_relativo"])
octave = f"""# Evaluación OCTAVE Allegro — ejercicio de escritorio

Generado: {STAMP}.

> **Naturaleza:** evaluación de escritorio realizada por el equipo del proyecto con base en el laboratorio y en supuestos del escenario. **No se realizaron entrevistas ni talleres**, por lo que no hay resultados de participantes. Una evaluación organizacional real requiere talleres con Registro, Dirección Académica, Finanzas, Legal, RRHH y TI, y validación de los propietarios.

## Variante metodológica

Se seleccionó **OCTAVE Allegro** (SEI/CERT, 2007) porque se centra en activos de información y sus contenedores, puede ejecutarse con un equipo reducido y no requiere el inventario exhaustivo de OCTAVE original ni la escala de OCTAVE-S. Se aplican sus ocho pasos y sus hojas de trabajo de forma resumida.

## Paso 1 — Criterios de medición del riesgo

Áreas de impacto priorizadas (supuesto académico; 6 = más importante). Cada escenario recibe Alto = 3, Medio = 2 o Bajo = 1 por área; puntaje relativo = Σ(valor × prioridad), mínimo 21 y máximo 63. Pools: 1 ≥ 50; 2 = 40–49; 3 < 40.

{table([{"area_impacto": n, "prioridad": w} for n, w in impact_areas])}

Las definiciones de Alto/Medio/Bajo se alinean con las escalas del BIA (`bia.md`): Alto ≈ 4–5, Medio ≈ 3, Bajo ≈ 1–2.

## Pasos 2 y 3 — Perfiles de activos críticos y contenedores

{table(octave_assets)}

## Paso 4 — Áreas de preocupación

Acceso indebido a expedientes; toma de cuentas; vulnerabilidades de imágenes; pérdida o inutilización de copias; robo de la clave de cifrado; detección insuficiente; pérdida del único host; dependencia de terceros sin contrato evaluado.

## Pasos 5 a 7 — Escenarios de amenaza, consecuencias y análisis

{table(octave_rows)}

## Paso 8 — Enfoque de mitigación

- **Pool 1 (mitigar de inmediato):** {", ".join(r["escenario"] for r in octave_rows if r["pool"].startswith("Pool 1")) or "—"}.
- **Pool 2 (mitigar o diferir con justificación):** {", ".join(r["escenario"] for r in octave_rows if r["pool"].startswith("Pool 2")) or "—"}.
- **Pool 3 (diferir/aceptar con seguimiento):** {", ".join(r["escenario"] for r in octave_rows if r["pool"].startswith("Pool 3")) or "—"}.

Las acciones concretas están en `plan-tratamiento.md` mediante los riesgos vinculados.

## Resultados

Los escenarios de mayor puntaje se concentran en la credencial/identidad (IA-02), las copias de respaldo en el mismo host (IA-03) y la pérdida del host (IA-01). Esto coincide con los riesgos críticos residuales de `matriz-riesgos.md` (R-011, R-013) y con la brecha de RPO medida (R-019). Fortalezas comprobadas en laboratorio: MFA/RBAC, segmentación, TLS, backups cifrados de ambas bases, restauración aislada periódica, correlación SIEM e IDS offline.

## Recomendaciones

1. Validar en talleres las prioridades del Paso 1 y los requisitos del Paso 2.
2. Aprobar repositorio offsite/inmutable y WAL/PITR (OS-04, R-011, R-019).
3. Mantener el reescaneo mensual de la imagen PostgreSQL sin gosu ya aplicada (OS-03, R-009).
4. Definir MDM/EDR y SIEM institucional con presupuesto (OS-06, R-012, R-013).
5. Repetir la evaluación anualmente y tras cambios mayores.
"""
(OUT / "octave-allegro.md").write_text(octave, encoding="utf-8")

# ---------------------------------------------------------------- BCP / DRP
bia_by_id = {row["id"]: row for row in bia_rows}
observed = []
if api_cont:
    observed.append(("Interrupción de la API (contenedor detenido)", "PROC-002", api_cont["recovery_seconds"], api_cont.get("timestamp", "")))
if iam_cont:
    observed.append(("Interrupción de Keycloak (contenedor detenido)", "PROC-004", iam_cont["recovery_seconds"], iam_cont.get("timestamp", "")))
if restore:
    for item in restore.get("results", []):
        proc = "PROC-004" if item["target"] == "identity" else "PROC-002"
        observed.append((f"Restauración aislada {item['target']} desde copia cifrada", proc, item["elapsed_seconds"], restore.get("timestamp", "")))
_, pitr_run = latest("pitr", "pitr-*.json")
if pitr_run:
    for item in pitr_run.get("results", []):
        if item.get("result") == "success":
            proc = "PROC-004" if item["target"] == "identity" else "PROC-002"
            observed.append((f"PITR {item['target']} (réplica aislada) al punto objetivo", proc, item["restore"]["rto_technical_seconds"], pitr_run["timestamp"]))
observed_rows = []
for scenario, proc, seconds, when in observed:
    rto_s = float(bia_by_id[proc]["rto_horas"]) * 3600
    observed_rows.append({"prueba": scenario, "proceso": proc, "rto_propuesto": f"{bia_by_id[proc]['rto_horas']} h",
                          "observado_s": seconds, "diferencia_s": round(rto_s - float(seconds), 1),
                          "cumple_tecnico": "Sí" if float(seconds) <= rto_s else "No", "fecha": when[:19]})
_, periodic = latest("recovery", "recuperacion-periodica-*.json")
rpo_rows = []
if periodic:
    for item in periodic.get("comparison", []):
        rpo_rows.append({"base": item["target"], "proceso": item["bia_process"], "rpo_propuesto_s": item["proposed_rpo_seconds"],
                         "intervalo_backup_s": item["backup_interval_seconds"],
                         "cumple": "Sí" if item["rpo_achievable_with_current_schedule"] else "No — brecha R-019"})
observed_md = (table(observed_rows) if observed_rows else "Sin mediciones disponibles.") + "\n\n" + (table(rpo_rows) if rpo_rows else "")
priority = sorted(bia_rows, key=lambda r: (float(r["rto_horas"]), r["id"]))

bcp = f"""# Plan de Continuidad del Negocio (BCP) — borrador UVCG

Generado: {STAMP}. Objetivos, roles y estrategias son **supuestos académicos pendientes de aprobación**. Se basa en `bia.md`; el detalle técnico de recuperación está en `drp.md`.

## 1. Alcance y objetivos

Procesos PROC-001 a PROC-007 del BIA. Objetivo: mantener los procesos críticos dentro de su MTPD y recuperarlos dentro del RTO/RPO propuestos.

## 2. Priorización de servicios

{table([{"orden": n + 1, "proceso": r["id"] + " " + r["proceso"], "criticidad": r["criticidad"], "RTO_h": r["rto_horas"], "RPO_h": r["rpo_horas"], "MTPD_h": r["mtpd_horas"]} for n, r in enumerate(priority)])}

Identidad (PROC-004) se recupera primero porque todos los demás procesos dependen de ella.

## 3. Criterios de activación

| Nivel | Condición | Decide |
|---|---|---|
| Alerta | Alerta SIEM alta/crítica, fallo de backup o servicio degradado sin impacto confirmado | Líder TI |
| Activación parcial | Indisponibilidad de un proceso crítico > 50 % de su RTO o corrupción confirmada de datos | Coordinador de Continuidad |
| Activación total | Pérdida del host/sitio, compromiso de identidad, o proyección de superar el MTPD de cualquier proceso crítico | Director de crisis |

## 4. Roles y responsabilidades (RACI resumido)

| Actividad | Director de crisis | Coordinador de Continuidad | Líder TI | Seguridad | Propietario de proceso | Comunicaciones | Legal/privacidad |
|---|---|---|---|---|---|---|---|
| Activar el plan | A | R | C | C | I | I | I |
| Recuperación técnica (DRP) | I | A | R | C | I | – | – |
| Contención y evidencia | I | I | C | R/A | I | – | C |
| Validación funcional | I | A | C | – | R | – | – |
| Comunicación interna/externa | A | C | – | C | C | R | C |
| Notificación de brecha de datos | A | I | – | C | I | C | R |

Los nombramientos reales están pendientes.

## 5. Estrategias de continuidad por proceso

| Proceso | Estrategia técnica | Alternativa manual temporal (definir con propietario) |
|---|---|---|
| PROC-004 Identidad | Backup cifrado + restauración aislada probada; reinicio controlado medido | Ninguna segura sin IAM; priorizar recuperación |
| PROC-001 Inscripción | Recuperar IAM + BD académica + API | Recepción de solicitudes en formulario controlado y carga posterior |
| PROC-003 Aprendizaje virtual | Depende de proveedor LMS (escenario) | Publicación de materiales por correo institucional |
| PROC-002 Gestión académica | Backup/restore de BD académica | Congelar cambios de calificaciones hasta restaurar |
| PROC-005 Finanzas | Proveedor/banca (escenario) | Registro manual de pagos con conciliación posterior |
| PROC-007 Comunicaciones | Proveedor de correo (escenario) | Canales alternos aprobados (sitio web, mensajería oficial) |
| PROC-006 Administrativos | Restauración ordinaria | Diferir trámites no urgentes |

Brechas estratégicas abiertas: sin copia offsite/inmutable ni sitio alterno (R-011, R-014) y RPO no alcanzable con backup diario (R-019).

## 6. Procedimiento de respuesta

1. Detectar (SIEM/IDS/usuarios) y registrar hora de inicio.
2. Evaluar impacto contra el BIA y decidir el nivel de activación.
3. Contener (Seguridad) y preservar evidencia antes de cambios.
4. Ejecutar el DRP en el orden de dependencias.
5. Activar alternativas manuales cuando la recuperación supere el 50 % del RTO.
6. Comunicar sólo hechos confirmados, a intervalos definidos.

## 7. Pruebas y resultados observados

Tiempos medidos en el laboratorio (último registro), comparados con el RTO/RPO académico propuesto. **Sólo cubren la recuperación técnica** de bases pequeñas en un host; no incluyen detección, decisión, comunicación ni validación funcional.

{observed_md}

Programa: semanal automatizado (tarea `SGSI-UVCG-Prueba-Recuperacion`, `scripts/prueba_recuperacion_periodica.ps1`), mensual (salud y hashes), semestral (interrupción controlada API/IAM con `scripts/prueba_continuidad.ps1`), anual (ejercicio de mesa con todos los roles y, cuando exista, pérdida de sitio).

## 8. Retorno a la normalidad

1. Confirmar integridad (conteos, hashes, pruebas RBAC/MFA) y ausencia de amenaza activa.
2. Aceptación formal del propietario de cada proceso.
3. Sincronizar transacciones registradas manualmente y conciliar.
4. Desactivar alternativas manuales y comunicar la normalización.
5. Reforzar monitoreo 72 h y ejecutar backup completo inmediato.
6. Lecciones aprendidas en 10 días hábiles; actualizar BIA, riesgos y este plan.
"""
(OUT / "bcp.md").write_text(bcp, encoding="utf-8")

drp = f"""# Disaster Recovery Plan (DRP) — laboratorio UVCG

Generado: {STAMP}. Borrador académico pendiente de aprobación y de infraestructura alterna. Deriva de `bia.md` y `bcp.md`.

## 1. Dependencias y orden de recuperación

1. Host/Docker, almacenamiento, red y tiempo (ACT-001, ACT-002).
2. Secretos y clave de cifrado de backups (ACT-011), custodiados fuera del directorio de copias.
3. PostgreSQL de identidad (ACT-007) → Keycloak (ACT-006).
4. PostgreSQL académico (ACT-005) → API (ACT-003).
5. Nginx/TLS (ACT-004, ACT-013).
6. SIEM, IDS y schedulers de backup (ACT-008, ACT-009, ACT-010).

## 2. Objetivos propuestos

{table([{"proceso": r["id"] + " " + r["proceso"], "RTO_h": r["rto_horas"], "RPO_h": r["rpo_horas"], "MTPD_h": r["mtpd_horas"]} for r in priority])}

El backup lógico diario (86 400 s) **no satisface** por sí solo el RPO de 15 min / 4 h. El archivado WAL/PITR se validó en réplicas aisladas (RPO observado ≈ 56 s con `archive_timeout` 60 s; recuperación exacta al punto objetivo); en las bases principales está **preparado** (`local/compose.pitr.yaml`) y pendiente de autorización (R-019).

## 3. Escenarios y procedimientos

**DR-1 Caída de un contenedor** (probado): `docker compose -f local/compose.yaml up -d --no-deps <servicio>`; esperar `healthy`; verificar `/health` y conteos. Evidencia: `evidencias/recovery/continuidad-*.json`.

**DR-2b Error lógico con hora conocida (PITR)** (probado en réplicas): restaurar el respaldo base, aplicar WAL hasta `recovery_target_time` anterior al error y promover en una instancia aislada (`scripts/pitr_prueba.py`); validar y migrar con autorización.

**DR-2 Corrupción de la base académica o de identidad** (restauración aislada probada):
1. Declarar incidente, congelar cambios y registrar tiempo; preservar logs y hashes.
2. No restaurar sobre la base activa. Verificar SHA-256 de la copia cifrada y disponibilidad separada de la clave.
3. Restaurar en instancia aislada: `scripts/restaurar_prueba.ps1 -Target Both` (conserva la base restaurada para su revisión).
4. Validar conteos (≥ 3 cursos, ≥ 4 identidades), MFA/RBAC y TLS.
5. Para recuperación productiva: autorización, respaldo del estado fallido, ventana definida y migración controlada.

**DR-3 Compromiso de identidad:** aislar Keycloak (detener el servicio), rotar secretos (`scripts/generar_secretos_lab.ps1` tras autorización), restaurar IAM desde copia anterior al compromiso, forzar reinscripción MFA.

**DR-4 Pérdida del host:** hoy **no recuperable dentro del RTO** (sin sitio ni copia externa: R-011). Procedimiento objetivo: nuevo host con Docker → recuperar código y `.env` desde custodia → restaurar copias offsite → DR-2.

**DR-5 Ransomware/cifrado de archivos:** aislar el host de la red, preservar evidencia, no pagar, reconstruir desde copia offsite inmutable (pendiente) y verificar integridad con `scripts/integridad_configuracion.py --verify`.

## 4. Resultados observados vs. objetivo

{observed_md}

## 5. Pruebas

Mensual: salud y hashes. Semanal (tarea programada `SGSI-UVCG-Prueba-Recuperacion`, domingos 10:00): `scripts/prueba_recuperacion_periodica.ps1` (restore aislado de ambas bases y comparación con RTO/RPO). Semestral: `scripts/prueba_continuidad.ps1 -Service api|keycloak`. Anual: pérdida de host/sitio cuando exista entorno alterno. Registrar observado contra objetivo, desviaciones, responsables y correcciones.

## 6. Reversión y retorno

Toda recuperación productiva conserva la copia del estado fallido hasta la aceptación del propietario. El retorno sigue la sección 8 del BCP.
"""
(OUT / "drp.md").write_text(drp, encoding="utf-8")

print(f"OK: activos={len(asset_rows)} procesos_bia={len(bia_rows)} riesgos={len(risk_rows)} controles_soa={len(soa_rows)} escenarios_octave={len(octave_rows)}")
