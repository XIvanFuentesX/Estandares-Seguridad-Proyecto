"""Pruebas de humo HTTPS sobre el laboratorio local encendido."""

import json
import ssl
import urllib.error
import urllib.request
from pathlib import Path

HTTP_BASE = "http://127.0.0.1:8080"
HTTPS_BASE = "https://localhost:8443"
LAB_CERT = Path(__file__).resolve().parents[1] / "local" / "tls" / "uvcg-lab.crt"
LAB_TLS = ssl.create_default_context(cafile=str(LAB_CERT))


def request(url, method="GET", headers=None, context=None):
    req = urllib.request.Request(url, method=method, headers=headers or {})
    opener = urllib.request.build_opener(urllib.request.HTTPHandler)
    try:
        if url.startswith("https://"):
            with urllib.request.urlopen(req, timeout=8, context=context) as response:  # nosec B310
                return response.status, response.read().decode(), dict(response.headers)
        with opener.open(req, timeout=8) as response:  # nosec B310
            return response.status, response.read().decode(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(), dict(exc.headers)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


try:
    urllib.request.build_opener(NoRedirect).open(HTTP_BASE + "/health", timeout=5)
    raise AssertionError("HTTP no fue redirigido")
except urllib.error.HTTPError as exc:
    assert exc.code == 301
    assert exc.headers["Location"].startswith("https://localhost:8443/")

status, data, headers = request(HTTPS_BASE + "/health", context=LAB_TLS)
assert status == 200 and json.loads(data)["status"] == "ok", ("health", status, data)
assert headers.get("Strict-Transport-Security") == "max-age=300"
assert headers.get("X-Content-Type-Options") == "nosniff"
assert headers.get("X-Frame-Options") == "DENY"
assert headers.get("Referrer-Policy") == "no-referrer"

status, data, headers = request(HTTPS_BASE + "/cursos", context=LAB_TLS)
assert status == 401 and json.loads(data)["error"] == "authentication_required"
assert headers.get("WWW-Authenticate") == 'Bearer realm="uvcg"'

for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
    status, _, _ = request(HTTPS_BASE + "/cursos", method, context=LAB_TLS)
    assert status == 403, ("metodo-no-autorizado", method, status)

print(
    "OK: redireccion HTTPS, TLS de laboratorio, health=200, ruta protegida=401, "
    "cabeceras seguras y metodos no autorizados=403"
)
