import json
import logging
import os
from functools import wraps

import jwt
import psycopg
from flask import Flask, g, jsonify, request
from jwt import PyJWKClient

app = Flask(__name__)
app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024,
    JSON_SORT_KEYS=True,
)

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(message)s")
logger = logging.getLogger("uvcg-api")

OIDC_ISSUER = os.environ.get(
    "OIDC_ISSUER", "https://localhost:8443/auth/realms/uvcg"
)
OIDC_JWKS_URL = os.environ.get(
    "OIDC_JWKS_URL", "http://keycloak:8080/auth/realms/uvcg/protocol/openid-connect/certs"
)
OIDC_ALLOWED_CLIENTS = {
    item.strip()
    for item in os.environ.get("OIDC_ALLOWED_CLIENTS", "sgsi-cli,sgsi-web").split(",")
    if item.strip()
}
jwks_client = PyJWKClient(OIDC_JWKS_URL, cache_keys=True, lifespan=300)


def audit_event(event, outcome, **fields):
    payload = {"event": event, "outcome": outcome, **fields}
    logger.info(json.dumps(payload, ensure_ascii=True, sort_keys=True))


def db_connect():
    """Conecta sin construir un URI que pueda interpretar caracteres reservados."""
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=3,
    )


def _unauthorized(message="authentication_required"):
    response = jsonify(error=message)
    response.status_code = 401
    response.headers["WWW-Authenticate"] = 'Bearer realm="uvcg"'
    return response


def require_roles(*allowed_roles):
    allowed = set(allowed_roles)

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                audit_event("authorization", "denied", reason="missing_token", path=request.path)
                return _unauthorized()

            token = header.removeprefix("Bearer ").strip()
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                claims = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256", "PS256"],
                    issuer=OIDC_ISSUER,
                    options={"require": ["exp", "iat", "iss", "sub"], "verify_aud": False},
                )
                if claims.get("azp") not in OIDC_ALLOWED_CLIENTS:
                    raise jwt.InvalidTokenError("client_not_allowed")
            except jwt.PyJWTError as exc:
                audit_event(
                    "authentication",
                    "denied",
                    reason=type(exc).__name__,
                    path=request.path,
                )
                return _unauthorized("invalid_token")

            roles = set(claims.get("realm_access", {}).get("roles", []))
            username = claims.get("preferred_username", "unknown")
            if allowed and roles.isdisjoint(allowed):
                audit_event(
                    "authorization",
                    "denied",
                    subject=username,
                    path=request.path,
                    required_roles=sorted(allowed),
                )
                return jsonify(error="insufficient_permissions"), 403

            g.identity = {"username": username, "roles": sorted(roles & allowed)}
            audit_event("authorization", "allowed", subject=username, path=request.path)
            return view(*args, **kwargs)

        return wrapped

    return decorator


@app.after_request
def api_security_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/health")
def health():
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return jsonify(status="ok", service="academico-demostrativo")
    except (psycopg.Error, KeyError, ValueError):
        return jsonify(status="unavailable"), 503


@app.get("/cursos")
@require_roles("administrador", "docente", "estudiante", "administrativo")
def cursos():
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT codigo, nombre FROM cursos ORDER BY codigo")
                rows = cur.fetchall()
        return jsonify([{"codigo": codigo, "nombre": nombre} for codigo, nombre in rows])
    except (psycopg.Error, KeyError, ValueError):
        return jsonify(status="unavailable"), 503


@app.get("/perfil")
@require_roles("administrador", "docente", "estudiante", "administrativo")
def perfil():
    return jsonify(g.identity)


@app.get("/docencia")
@require_roles("administrador", "docente")
def docencia():
    return jsonify(area="docencia", access="granted")


@app.get("/administracion")
@require_roles("administrador")
def administracion():
    return jsonify(area="administracion", access="granted")
