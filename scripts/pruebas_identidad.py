"""Valida Keycloak, TOTP y la matriz RBAC sin mostrar credenciales o tokens."""

import hashlib
import hmac
import json
import ssl
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://localhost:8443"
LAB_CERT = Path(__file__).resolve().parents[1] / "local" / "tls" / "uvcg-lab.crt"
TLS = ssl.create_default_context(cafile=str(LAB_CERT))
ENV_PATH = Path(__file__).resolve().parents[1] / "local" / ".env"


def load_env():
    values = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value
    return values


def request(path, method="GET", data=None, token=None):
    headers = {}
    body = None
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=TLS, timeout=15) as response:  # nosec B310
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}, dict(response.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"raw": raw[:100]}
        return exc.code, payload, dict(exc.headers)


def totp(secret):
    # Keycloak almacena esta cadena como secreto crudo y codifica esa cadena
    # en Base32 únicamente al construir el QR para la aplicación autenticadora.
    key = secret.encode("ascii")
    counter = int(time.time()) // 30
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha256).digest()
    offset = digest[-1] & 0x0F
    number = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{number:06d}"


def user_token(username, password, otp_secret):
    status, payload, _ = request(
        "/auth/realms/uvcg/protocol/openid-connect/token",
        "POST",
        {
            "grant_type": "password",
            "client_id": "sgsi-cli",
            "username": username,
            "password": password,
            "totp": totp(otp_secret),
        },
    )
    assert status == 200 and "access_token" in payload, (
        username,
        status,
        payload.get("error"),
        payload.get("error_description"),
    )
    return payload["access_token"]


env = load_env()

status, discovery, _ = request("/auth/realms/uvcg/.well-known/openid-configuration")
assert status == 200
assert discovery["issuer"] == "https://localhost:8443/auth/realms/uvcg"

status, payload, _ = request(
    "/auth/realms/uvcg/protocol/openid-connect/token",
    "POST",
    {
        "grant_type": "password",
        "client_id": "sgsi-cli",
        "username": "admin.lab",
        "password": env["UVCG_ADMIN_PASSWORD"],
    },
)
assert status == 400 and payload.get("error") == "invalid_grant", (status, payload.get("error"))

identities = {
    "administrador": (
        "admin.lab",
        env["UVCG_ADMIN_PASSWORD"],
        env["UVCG_ADMIN_TOTP"],
    ),
    "docente": (
        "docente.lab",
        env["UVCG_DOCENTE_PASSWORD"],
        env["UVCG_DOCENTE_TOTP"],
    ),
    "estudiante": (
        "estudiante.lab",
        env["UVCG_ESTUDIANTE_PASSWORD"],
        env["UVCG_ESTUDIANTE_TOTP"],
    ),
    "administrativo": (
        "administrativo.lab",
        env["UVCG_ADMINISTRATIVO_PASSWORD"],
        env["UVCG_ADMINISTRATIVO_TOTP"],
    ),
}

tokens = {
    role: user_token(username, password, otp)
    for role, (username, password, otp) in identities.items()
}

for role, token in tokens.items():
    status, cursos, _ = request("/cursos", token=token)
    assert status == 200 and len(cursos) >= 3, (role, "cursos", status)
    status, profile, _ = request("/perfil", token=token)
    assert status == 200 and profile["username"] == identities[role][0]

expected = {
    "administrador": {"/docencia": 200, "/administracion": 200},
    "docente": {"/docencia": 200, "/administracion": 403},
    "estudiante": {"/docencia": 403, "/administracion": 403},
    "administrativo": {"/docencia": 403, "/administracion": 403},
}
for role, paths in expected.items():
    for path, expected_status in paths.items():
        status, _, _ = request(path, token=tokens[role])
        assert status == expected_status, (role, path, status, expected_status)

status, _, _ = request("/cursos", token="invalid.invalid.invalid")  # nosec B106
assert status == 401

status, admin_auth, _ = request(
    "/auth/realms/master/protocol/openid-connect/token",
    "POST",
    {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": env["KC_ADMIN_USER"],
        "password": env["KC_ADMIN_PASSWORD"],
    },
)
assert status == 200 and "access_token" in admin_auth
status, events, _ = request(
    "/auth/admin/realms/uvcg/events?max=100", token=admin_auth["access_token"]
)
assert status == 200 and isinstance(events, list)
event_types = {event.get("type") for event in events}
assert "LOGIN" in event_types and "LOGIN_ERROR" in event_types, event_types

print(
    "OK: OIDC, MFA TOTP requerido y válido, 4 roles, matriz RBAC, "
    "token inválido rechazado y eventos LOGIN/LOGIN_ERROR registrados"
)
