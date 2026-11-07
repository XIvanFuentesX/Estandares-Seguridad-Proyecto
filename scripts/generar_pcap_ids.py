"""Genera un PCAP sintético y autorizado para validar reglas IDS offline.

Cada escenario usa direcciones de documentación privadas y nunca se transmite por la red.
Antes de generar, archiva las salidas Suricata previas porque Suricata agrega a eve.json.
"""

import datetime as dt
import json
import shutil
import socket
import struct
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "local" / "ids" / "pcap" / "trafico-controlado.pcap"
IDS_EVIDENCE = ROOT / "evidencias" / "ids"
SCENARIOS = IDS_EVIDENCE / "escenarios-pcap.json"


def checksum(data):
    if len(data) % 2:
        data += b"\x00"
    total = sum(struct.unpack(f"!{len(data) // 2}H", data))
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return (~total) & 0xFFFF


def packet(src, dst, sport, dport, seq, ack, flags, payload=b""):
    src_ip = socket.inet_aton(src)
    dst_ip = socket.inet_aton(dst)
    tcp = struct.pack("!HHLLBBHHH", sport, dport, seq, ack, 5 << 4, flags, 64240, 0, 0)
    pseudo = src_ip + dst_ip + struct.pack("!BBH", 0, 6, len(tcp) + len(payload))
    tcp_checksum = checksum(pseudo + tcp + payload)
    tcp = struct.pack("!HHLLBBHHH", sport, dport, seq, ack, 5 << 4, flags, 64240, tcp_checksum, 0)
    total_length = 20 + len(tcp) + len(payload)
    ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, total_length, 1234, 0x4000, 64, 6, 0, src_ip, dst_ip)
    ip = ip[:10] + struct.pack("!H", checksum(ip)) + ip[12:]
    ethernet = bytes.fromhex("0200000000200200000000100800")
    return ethernet + ip + tcp + payload


def http_session(src, sport, dst, dport, request):
    """Handshake TCP + una solicitud HTTP del cliente."""
    return [
        packet(src, dst, sport, dport, 100, 0, 0x02),
        packet(dst, src, dport, sport, 200, 101, 0x12),
        packet(src, dst, sport, dport, 101, 201, 0x10),
        packet(src, dst, sport, dport, 101, 201, 0x18, request),
    ]


def http_get(path, user_agent="Mozilla/5.0 UVCG-lab"):
    return (f"GET {path} HTTP/1.1\r\nHost: laboratorio.local\r\nUser-Agent: {user_agent}\r\n"
            "Connection: close\r\n\r\n").encode()


def archive_previous_outputs():
    files = [IDS_EVIDENCE / name for name in ("eve.json", "fast.log", "stats.log", "suricata.log")]
    present = [path for path in files if path.exists()]
    if not present:
        return None
    target = IDS_EVIDENCE / "historico" / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    target.mkdir(parents=True, exist_ok=True)
    for path in present:
        shutil.move(str(path), target / path.name)
    return target


WEB = ("10.10.10.20", 8080)
scenarios = [
    # (id, descripción, sid esperado o None si es tráfico benigno, frames)
    ("IDS-T01", "Path traversal en URI", 1000001,
     http_session("10.10.10.10", 54321, *WEB, http_get("/../../etc/passwd"))),
    ("IDS-T02", "SYN directo a PostgreSQL", 1000002,
     [packet("10.10.10.30", "10.10.10.40", 55222, 5432, 300, 0, 0x02)]),
    ("IDS-T03", "Inyección SQL UNION SELECT", 1000003,
     http_session("10.10.10.11", 54400, *WEB, http_get("/cursos?id=1%20UNION%20SELECT%20usuario,clave%20FROM%20x"))),
    ("IDS-T04", "Agente de escaneo sqlmap", 1000004,
     http_session("10.10.10.12", 54500, *WEB, http_get("/health", "sqlmap/1.8 (https://sqlmap.org)"))),
    ("IDS-T05", "Acceso a consola admin Keycloak", 1000005,
     http_session("10.10.10.13", 54600, *WEB, http_get("/auth/admin/master/console/"))),
    ("IDS-T06", "SYN al puerto de gestión Keycloak", 1000006,
     [packet("10.10.10.14", "10.10.10.50", 54700, 9000, 400, 0, 0x02)]),
]
login = (b"POST /auth/realms/uvcg/login-actions/authenticate HTTP/1.1\r\nHost: laboratorio.local\r\n"
         b"Content-Type: application/x-www-form-urlencoded\r\nContent-Length: 27\r\nConnection: close\r\n\r\n"
         b"username=sintetico&otp=0000")
burst = []
for attempt in range(6):
    burst += http_session("10.10.10.15", 54800 + attempt, *WEB, login)
scenarios.append(("IDS-T07", "Ráfaga de 6 POST de login en < 60 s", 1000007, burst))
scenarios.append(("IDS-N01", "Tráfico benigno GET /health (no debe alertar)", None,
                  http_session("10.10.10.16", 54900, *WEB, http_get("/health"))))

archived = archive_previous_outputs()
now = int(time.time())
count = 0
with OUTPUT.open("wb") as handle:
    handle.write(struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
    for _, _, _, frames in scenarios:
        for frame in frames:
            handle.write(struct.pack("<IIII", now + count // 1000, (count % 1000) * 1000, len(frame), len(frame)))
            handle.write(frame)
            count += 1

SCENARIOS.write_text(json.dumps([
    {"id": sid_id, "description": desc, "expected_sid": sid, "src_ip": socket.inet_ntoa(frames[0][26:30])}
    for sid_id, desc, sid, frames in scenarios
], ensure_ascii=False, indent=2), encoding="utf-8")
print(f"OK: pcap_sintetico={OUTPUT.name} escenarios={len(scenarios)} paquetes={count} destino=solo_archivo"
      + (f" archivado={archived.name}" if archived else ""))
