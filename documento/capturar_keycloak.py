"""Toma capturas reales del inicio de sesión con MFA en Keycloak (laboratorio en ejecución).

Uso: python documento/capturar_keycloak.py  ->  documento/figuras/capturas/keycloak-*.png
Usa el Chrome instalado. La contraseña se lee de local/.env y sólo se teclea en el campo
enmascarado; la pantalla del código TOTP se captura antes de escribirlo. La consola de cuenta no se
captura: los usuarios no tienen el rol manage-account (mínimo privilegio) y Keycloak responde 401.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from codigo_totp import leer_secreto  # noqa: E402

OUT = ROOT / "documento" / "figuras" / "capturas"
URL = "https://localhost:8443/auth/realms/uvcg/account/"


def main(usuario="docente"):
    OUT.mkdir(parents=True, exist_ok=True)
    password = leer_secreto(f"UVCG_{usuario.upper()}_PASSWORD")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=True)
        page = browser.new_context(ignore_https_errors=True, viewport={"width": 1280, "height": 800}, locale="es-ES").new_page()
        page.goto(URL, wait_until="networkidle")
        page.fill("#username", f"{usuario}.lab")
        page.fill("#password", password)
        page.screenshot(path=OUT / "keycloak-1-login.png")
        page.click("#kc-login")
        page.wait_for_selector("#otp", timeout=15000)
        page.screenshot(path=OUT / "keycloak-2-mfa-totp.png")
        page.fill("#otp", "000000")  # código inválido: evidencia del rechazo
        page.click("#kc-login")
        page.wait_for_selector("#otp", timeout=15000)
        page.screenshot(path=OUT / "keycloak-3-mfa-rechazado.png")
        browser.close()
    print("OK:", ", ".join(p.name for p in sorted(OUT.glob("keycloak-*.png"))))


if __name__ == "__main__":
    main(*(sys.argv[1:2]))
