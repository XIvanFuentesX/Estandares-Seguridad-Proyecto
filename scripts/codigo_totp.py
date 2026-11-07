"""Muestra el código TOTP vigente de un usuario de laboratorio (no imprime el secreto).

Uso: python scripts/codigo_totp.py docente
Usuarios: administrador, docente, estudiante, administrativo. El código vale 30 s.
"""
import argparse
import hashlib
import hmac
import struct
import time
from pathlib import Path

ENV = Path(__file__).resolve().parent.parent / "local" / ".env"
VARIABLES = {
    "administrador": "UVCG_ADMIN_TOTP",
    "docente": "UVCG_DOCENTE_TOTP",
    "estudiante": "UVCG_ESTUDIANTE_TOTP",
    "administrativo": "UVCG_ADMINISTRATIVO_TOTP",
}


def leer_secreto(variable):
    for linea in ENV.read_text(encoding="utf-8").splitlines():
        if linea.startswith(variable + "="):
            return linea.split("=", 1)[1].strip()
    raise SystemExit(f"No se encontró {variable} en {ENV}")


def totp(secret, instante):
    # Igual que scripts/pruebas_identidad.py: secreto crudo, HMAC-SHA256, 6 dígitos, 30 s.
    digest = hmac.new(secret.encode("ascii"), struct.pack(">Q", instante // 30), hashlib.sha256).digest()
    offset = digest[-1] & 0x0F
    number = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{number:06d}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("usuario", choices=sorted(VARIABLES))
    args = parser.parse_args()
    ahora = int(time.time())
    print(f"Código para {args.usuario}.lab: {totp(leer_secreto(VARIABLES[args.usuario]), ahora)} "
          f"(vence en {30 - ahora % 30} s)")


if __name__ == "__main__":
    main()
