# Despliegue mínimo AWS (plan Free) — SGSI UVCG

Implementación independiente de `azure/`. **Estado: preparada y validada estáticamente; no desplegada** (no hubo sesión AWS para verificar la cuenta).

## Alcance

| Recurso | Propósito | Costo |
|---|---|---|
| `aws_s3_bucket` + bloqueo de acceso público, `BucketOwnerEnforced`, SSE-S3, ciclo de vida de 30 días, política sólo TLS ≥ 1.2 y escritura sólo por el rol de carga | Componente real de nube pública para intercambio cifrado de archivos **ficticios** con el laboratorio | Créditos del plan Free (fracciones de centavo); 0 USD a la tarjeta mientras la cuenta siga en plan Free |
| 2 roles IAM (`uploader`, `auditor`) con políticas en línea de mínimo privilegio; sin usuarios IAM ni claves de acceso | IAM y separación de funciones | Sin costo |
| `aws_budgets_budget` de gasto cero (`include_credit = false`) | Alerta ante cualquier uso | Sin costo (monitoreo sin acciones) |

Excluidos a propósito: VPC, NAT, VPN, EC2, RDS, ELB, KMS CMK, trail de CloudTrail y AWS Organizations (unirse a Organizations convierte automáticamente el plan Free en Paid).

Región: `us-east-1` (validación de variable: sólo `us-east-1`/`us-east-2`).

## Procedimiento de despliegue (sólo con autorización y verificación previa)

1. Instalar AWS CLI v2.32 o superior (necesario para `aws login`).
2. `aws login`: credenciales temporales de la consola, sin claves permanentes. Preferible un usuario IAM o de Identity Center con MFA en lugar del usuario raíz.
3. `aws\scripts\verificar_cuenta.ps1`: exige plan `FREE`, estado `ACTIVE`, créditos mayores que 1 y más de 7 días de vigencia. Comparar los créditos con la consola de Billing y registrar cualquier diferencia.
4. Copiar `terraform.tfvars.example` a `terraform.tfvars` (ignorado por Git) con el ID de cuenta verificado y el correo de alertas.
5. `aws\scripts\desplegar.ps1`: genera el **plan real** y lo pasa por la compuerta `revisar_plan.py`, que sólo admite los tipos de la lista de gratuidad verificada y ninguna destrucción. Revisar el plan.
6. `aws\scripts\desplegar.ps1 -Aplicar`: aplica exactamente el plan revisado y vuelve a verificar que la cuenta siga en plan FREE.
7. `aws\scripts\pruebas_aws.ps1`: 13 pruebas reales.
8. Después de la demostración: `aws\scripts\retirar.ps1 -Confirmacion RETIRAR-SGSI-UVCG` (manual, nunca automática).

El estado de Terraform queda en `aws/terraform.tfstate`, local e ignorado por Git. Contiene ARN e IDs de cuenta, no secretos: debe protegerse con los permisos del perfil de usuario y no compartirse.

## Validación sin credenciales

`terraform fmt -check`, `validate`, `terraform test` (proveedor simulado), TFLint y `trivy config`; resultados en `evidencias/aws/validacion-terraform-aws-20261024.txt`.
