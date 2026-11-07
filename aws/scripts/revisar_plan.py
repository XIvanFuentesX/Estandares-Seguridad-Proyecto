"""Compuerta de costo del plan Terraform: rechaza cualquier recurso fuera de la lista de gratuidad verificada.

Uso: python revisar_plan.py plan.json salida.json
Termina con código 1 si el plan crea/modifica algún tipo de recurso no permitido, si destruye recursos
o si contiene más recursos de los esperados. No aplica nada.
"""

import json
import sys
from pathlib import Path

# Tipos verificados como sin cargo o cubiertos por el plan Free (ver evidencias/aws/COSTOS-AWS.md).
ALLOWED = {
    "aws_s3_bucket": "S3 disponible en el plan Free; uso de KB consume créditos, no tarjeta",
    "aws_s3_bucket_public_access_block": "configuración sin costo",
    "aws_s3_bucket_ownership_controls": "configuración sin costo",
    "aws_s3_bucket_server_side_encryption_configuration": "SSE-S3 sin costo adicional",
    "aws_s3_bucket_lifecycle_configuration": "configuración sin costo",
    "aws_s3_bucket_policy": "configuración sin costo",
    "aws_iam_role": "IAM sin costo",
    "aws_iam_role_policy": "IAM sin costo",
    "aws_budgets_budget": "Budgets sin acciones: monitoreo y notificación gratuitos",
}
MAX_RESOURCES = 12


def main():
    plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rows, problems = [], []
    for change in plan.get("resource_changes", []):
        actions = change["change"]["actions"]
        if actions == ["no-op"] or change.get("mode") == "data":
            continue
        rtype = change["type"]
        ok = rtype in ALLOWED and "delete" not in actions
        rows.append({"address": change["address"], "type": rtype, "actions": actions,
                     "allowed": ok, "justification": ALLOWED.get(rtype, "NO PERMITIDO: costo no verificado")})
        if not ok:
            problems.append(f"{change['address']} ({rtype}, {actions})")
    if len(rows) > MAX_RESOURCES:
        problems.append(f"{len(rows)} recursos > máximo {MAX_RESOURCES}")
    report = {"resources": rows, "count": len(rows), "problems": problems, "approved": not problems}
    Path(sys.argv[2]).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in rows:
        print(f"{'OK ' if row['allowed'] else 'NO '} {row['address']} {row['actions']}")
    if problems:
        print("RECHAZADO: " + "; ".join(problems))
        sys.exit(1)
    print(f"APROBADO: {len(rows)} recursos, todos en la lista de gratuidad verificada")


if __name__ == "__main__":
    main()
