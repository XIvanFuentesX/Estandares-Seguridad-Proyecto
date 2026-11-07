# Estimación y comprobación de costos AWS

Fecha: 2026-10-24.

## Condiciones verificadas en fuentes oficiales

| Hecho | Fuente |
|---|---|
| El plan Free "ensures you won't incur any charges"; dura 6 meses o hasta agotar los créditos; después la cuenta se cierra (90 días de retención) | [Choosing a plan — AWS Billing](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html) |
| Pasa automáticamente a Paid al unirse a AWS Organizations, crear una landing zone de Control Tower, unirse al AWS Partner Network, entre otros | misma fuente |
| Estado del plan, créditos y vencimiento consultables por API/CLI sin costo (`freetier:GetAccountPlanState`); existe `UpgradeAccountPlan` | [Tracking Free Tier usage](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/tracking-free-tier-usage.html), [Free Tier API](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_Operations_AWS_Free_Tier.html) |
| S3 está disponible en ambos planes | [AWS Free Tier](https://aws.amazon.com/free/) |
| Budgets: monitoreo y notificaciones gratuitos | [AWS Budgets pricing](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/) |
| CloudTrail: historial de eventos de 90 días sin costo | [CloudTrail pricing](https://aws.amazon.com/cloudtrail/pricing/) |
| `aws login` usa credenciales de consola temporales (CLI ≥ 2.32) | [Login for AWS local development](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html) |

## Precios S3 us-east-1 (API pública de listas de precios, publicación 2026-10-15)

Evidencia: `precios-s3-us-east-1-20261024.json`.

| Concepto | Precio | Uso estimado en la demostración | Costo |
|---|---|---|---|
| Almacenamiento Standard | 0.023 USD/GB-mes | < 10 KB durante ≤ 30 días | ≈ 0.0000002 USD |
| PUT/COPY/POST/LIST | 0.005 USD/1 000 | ≈ 30 solicitudes | ≈ 0.00015 USD |
| GET y otras | 0.004 USD/10 000 | ≈ 50 solicitudes | ≈ 0.00002 USD |
| Transferencia entrante | 0 USD/GB | KB | 0 |
| IAM, STS, Budgets (sin acciones), historial CloudTrail | sin costo | — | 0 |

**Total estimado: < 0.001 USD**, descontado de los créditos del plan Free. **Gasto de bolsillo (tarjeta): 0.00 USD**, condicionado a que la cuenta siga en plan **FREE/ACTIVE**, lo que se verifica antes y después del `apply`.

## Comprobación real

**No realizada**: no hubo sesión AWS. No se consultó el saldo de créditos ni se pudo comparar entre las secciones de Billing. No se usa la API de Cost Explorer porque cobra 0.01 USD por solicitud. Tras desplegar se verifica con `freetier get-account-plan-state` (créditos antes y después) y con la consola de Billing.

## Hallazgos de seguridad aceptados por costo (Trivy)

| ID | Severidad | Hallazgo | Decisión |
|---|---|---|---|
| AWS-0132 | HIGH | Sin CMK de KMS | Aceptado: SSE-S3 (AES-256) no tiene costo; una CMK cuesta por mes. Los datos son ficticios. |
| AWS-0090 | MEDIUM | Sin versionado | Aceptado: datos ficticios con expiración de 30 días; el versionado añade almacenamiento. |
| AWS-0089 | LOW | Sin registro de acceso del bucket | Aceptado: los registros generan almacenamiento; se usa el historial de CloudTrail (eventos de gestión). |
