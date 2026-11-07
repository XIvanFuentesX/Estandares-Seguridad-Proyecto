"""Monitor continuo de disponibilidad (contenedor `uptime-monitor`, perfil `monitoring`).

Sondea por HTTPS, a través del proxy en la red DMZ, cada INTERVAL segundos:
  nginx (/healthz), API (/health, que consulta la base académica) y Keycloak (OIDC discovery,
  que depende de la base de identidad). Valida TLS contra el certificado del laboratorio.
Escribe líneas `target=avail-<servicio> result=success|failure latency_ms=` en /out/disponibilidad.log.
No usa el socket de Docker, no publica puertos y no requiere privilegios.
"""

import datetime as dt
import os
import ssl
import time
import urllib.request

INTERVAL = int(os.environ.get("INTERVAL_SECONDS", "60"))
LOG = "/out/disponibilidad.log"
CONTEXT = ssl.create_default_context(cafile="/ca/uvcg-lab.crt")
CHECKS = {
    "nginx": "http://proxy:8080/healthz",
    "api": "https://proxy:8443/health",
    "keycloak": "https://proxy:8443/auth/realms/uvcg/.well-known/openid-configuration",
}


def probe(url):
    request = urllib.request.Request(url, headers={"Host": "localhost:8443" if url.startswith("https") else "localhost"})
    started = time.monotonic()
    try:
        # El certificado del laboratorio es para "localhost": se valida con ese nombre aunque la conexión vaya a "proxy".
        context = CONTEXT if url.startswith("https") else None
        handler = urllib.request.HTTPSHandler(context=context) if context else urllib.request.HTTPHandler()
        opener = urllib.request.build_opener(handler)
        if context:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED
        with opener.open(request, timeout=10) as response:
            code = response.status
    except Exception as exc:  # noqa: BLE001
        return "failure", int((time.monotonic() - started) * 1000), type(exc).__name__
    return ("success" if code == 200 else "failure"), int((time.monotonic() - started) * 1000), str(code)


while True:
    with open(LOG, "a", encoding="utf-8") as handle:
        for name, url in CHECKS.items():
            result, latency, detail = probe(url)
            handle.write(f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ} target=avail-{name} result={result} latency_ms={latency} detail={detail}\n")
    time.sleep(INTERVAL)
