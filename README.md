# SGSI UVCG — Proyecto final de Estándares de Seguridad

Sistema de Gestión de Seguridad de la Información para la universidad ficticia **UVCG**, con arquitectura híbrida: laboratorio local en Docker (DMZ, aplicaciones, identidad y datos segmentados) más un componente real en **AWS** (us-east-2). Prototipo académico con datos ficticios; no es un SGSI certificado ni infraestructura de producción.

- Documento final: [`documento/Proyecto_Final_SGSI_UVCG.docx`](documento/Proyecto_Final_SGSI_UVCG.docx)
- Arquitectura: `localhost:8443 → Nginx (DMZ) → API Flask (apps) → PostgreSQL (datos)`, con Keycloak (OIDC + MFA) en la red de identidad. Sólo el proxy publica puertos y únicamente en `127.0.0.1`.

## Levantar el laboratorio después de clonar (Windows)

### Requisitos

- **Docker Desktop** iniciado (WSL2), con al menos 6 GB de RAM asignados.
- **Python 3.10+** y **Git** (Git para Windows ya incluye la configuración necesaria).
- **PowerShell 5.1** o superior (viene con Windows).
- Los puertos **8080** y **8443** libres.

### Pasos (una sola vez)

Desde la carpeta del repositorio, en PowerShell:

```powershell
# 1. Secretos propios (contraseñas, claves TOTP y clave de respaldo) en local\.env
powershell -ExecutionPolicy Bypass -File scripts\generar_secretos_lab.ps1

# 2. Certificado TLS autofirmado de laboratorio en local\tls\
powershell -ExecutionPolicy Bypass -File scripts\generar_certificado_lab.ps1

# 3. Construir y levantar los 5 servicios principales (la primera vez tarda varios minutos)
cd local
docker compose -f compose.yaml up -d --build
cd ..
```

Cada integrante genera **sus propios** secretos: `local\.env`, `local\tls\*.key` y los respaldos nunca se suben a GitHub. No compartan su `.env` por chat ni correo.

### Comprobar que funciona

```powershell
python scripts\pruebas_locales.py      # HTTPS, cabeceras y bloqueos -> debe decir "OK: ..."
python scripts\pruebas_identidad.py    # OIDC, MFA TOTP y matriz de roles -> "OK: ..."
```

Keycloak tarda alrededor de un minuto en quedar listo; si una prueba falla justo al arrancar, espere y repita.

### Entrar a Keycloak con MFA (navegador)

1. Abrir <https://localhost:8443/auth/realms/uvcg/account/> y aceptar el aviso del certificado de laboratorio.
2. Usuario `docente.lab` (también `admin.lab`, `estudiante.lab`, `administrativo.lab`). La contraseña está en su `local\.env` (`UVCG_DOCENTE_PASSWORD`, etc.).
3. En la pantalla del código de 6 dígitos: `python scripts\codigo_totp.py docente` (vale 30 s).

Tras el inicio de sesión, la consola de cuenta muestra un error: es esperado, los usuarios no tienen el rol `manage-account` (mínimo privilegio).

### Servicios opcionales y validación integral

```powershell
cd local
docker compose -f compose.yaml --profile backup-scheduled --profile monitoring up -d   # respaldos diarios y monitor
cd ..
powershell -ExecutionPolicy Bypass -File scripts\validar_sgsi.ps1                      # todas las pruebas sin interrupción
```

Comandos por módulo (SIEM, IDS, DLP, MDM, respaldos, PITR, continuidad): [`MANUAL_EJECUCION.md`](MANUAL_EJECUCION.md).

### Detener

```powershell
cd local
docker compose -f compose.yaml --profile backup-scheduled --profile monitoring down
```

**No usar `down -v`**: borra las bases de datos y los usuarios de Keycloak. Apagar la laptop no borra nada; al encender basta con iniciar Docker Desktop y repetir el `up -d`.

## Componente AWS

Desplegado en la cuenta del titular del proyecto (plan Free, región **us-east-2**): bucket S3 privado y cifrado, roles IAM `uploader`/`auditor` con credenciales temporales y presupuesto de gasto cero; 13/13 pruebas (`evidencias/aws/pruebas-aws-*.json`). Los demás integrantes **no necesitan** cuenta de AWS para probar el laboratorio local. Detalle, costos y retirada: [`CIERRE_AWS.md`](CIERRE_AWS.md) y [`aws/README.md`](aws/README.md). La carpeta `azure/` es una alternativa evaluada y descartada.

## Estructura

| Carpeta | Contenido |
|---|---|
| `local/` | Laboratorio Docker: Nginx, API, Keycloak, PostgreSQL, respaldos, IDS, DLP, MDM |
| `scripts/` | Pruebas, validación integral, SIEM ligero, gobierno y utilidades |
| `governance/` | Inventario, BIA, riesgos, OCTAVE, matriz de calor, tratamiento, SoA, BCP/DRP, COBIT/ITIL |
| `policies/` | Políticas, clasificación, Zero Trust, BYOD/MDM, procedimiento de incidentes |
| `aws/` | Terraform y scripts del componente AWS |
| `evidencias/` | Resultados de todas las pruebas, con fecha |
| `documento/` | Documento final y sus generadores (`node documento/generar_documento.js`) |

## Seguridad del repositorio

No subir `.env`, claves TLS, respaldos, `terraform.tfstate`, `terraform.tfvars` ni `*.tfplan` (ya están en `.gitignore`). No incluir contraseñas ni tokens en capturas.
