# Cierre AWS — SGSI UVCG (despliegue mínimo en plan Free)

> **Actualización 2026-11-07: DESPLEGADO Y PROBADO.** Cuenta `0054****4685` (plan FREE, ACTIVE), región **us-east-2**: la SCP de la organización administradora deniega us-east-1 (INC-013). 11 recursos creados con el plan revisado (CHG-007); `pruebas_aws.ps1`: **13/13 exitosas**. Evidencias: `evidencias/aws/plan-20261107-130521.txt`, `apply-20261107-130521.txt`, `pruebas-aws-20261107-130835.json`. Las secciones siguientes describen el estado previo y se conservan como historial.

Fecha: 2026-10-24. **Estado (histórico): PREPARADO, NO DESPLEGADO.**

## 1. Motivo por el que no se desplegó

La regla del encargo exige verificar la cuenta (identidad, plan Free activo, créditos, vencimiento) antes de crear recursos. En este equipo **no hay AWS CLI instalado, ni sesión temporal, ni perfil AWS**, así que no fue posible verificar nada. Conforme a la instrucción "si no es posible confirmar las condiciones económicas, detener el despliegue y entregar solamente el diseño", **no se generó plan real ni se aplicó Terraform**. No se usó ninguna captura del portal como autorización, no se crearon claves de acceso y no hubo gasto.

## 2. Qué quedó listo

| Elemento | Estado | Evidencia |
|---|---|---|
| Terraform modular `aws/` (storage, iam, guardrails), región `us-east-1`, etiquetas académicas, `allowed_account_ids` | Implementado (código) | `aws/` |
| Validación estática: `fmt`, `validate`, `terraform test` 2/2 (proveedor simulado), TFLint 0 avisos, Trivy 58 OK / 3 aceptados | Ejecutada | `evidencias/aws/validacion-terraform-aws-20261024.txt`, `trivy-config-aws.json` |
| Verificación de cuenta (FREE/ACTIVE, créditos, vencimiento, usuario raíz) | Preparada | `aws/scripts/verificar_cuenta.ps1` |
| Compuerta de costo del plan (lista blanca de tipos, sin destrucciones, máximo 12 recursos) | Implementada y probada con planes sintéticos | `evidencias/aws/prueba-compuerta-plan-20261024.json` |
| Despliegue que aplica sólo el plan revisado (con hash) y re-verifica el plan FREE | Preparado | `aws/scripts/desplegar.ps1` |
| 13 pruebas reales post-despliegue (existencia, IAM, permitido/denegado, TLS, SSE, integridad, anónimo, CloudTrail, plan) | Preparadas, no ejecutadas | `aws/scripts/pruebas_aws.ps1` |
| Retirada manual con confirmación | Preparada | `aws/scripts/retirar.ps1`, `evidencias/aws/RIESGOS-Y-RETIRADA-AWS.md` |
| Arquitectura, diagrama e inventario | Documentados | `evidencias/aws/ARQUITECTURA-AWS.md` |
| Costos con fuentes oficiales y precios S3 de la API pública | Documentados | `evidencias/aws/COSTOS-AWS.md`, `precios-s3-us-east-1-20261024.json` |

## 3. Matriz de requisitos académicos

| Requisito | Estado | Observación |
|---|---|---|
| Componente real de nube pública | **PENDIENTE** | S3 preparado; requiere verificación de cuenta y despliegue |
| IAM y mínimo privilegio | **PREPARADO** | 2 roles con políticas acotadas; validados sólo estáticamente |
| Seguridad de acceso | **PREPARADO** | Bloqueo público, sólo TLS ≥ 1.2, escritura restringida, sin claves permanentes |
| Registro o evidencia de configuración | **PREPARADO** | Historial de CloudTrail (gratuito) y `pruebas_aws.ps1`; nada registrado todavía |
| Integración verificable con el laboratorio | **PREPARADO** | Carga por HTTPS de un archivo ficticio con identidad temporal; **no** es una VPN privada |
| Costo cero de bolsillo | **CUMPLE (sin gasto)** | No se creó nada; el diseño sólo usa servicios sin costo o cubiertos por créditos del plan Free |
| IaC, validación, despliegue y retirada documentados | **CUMPLE** | `aws/`, `evidencias/aws/` |
| Pruebas reales y verificación de facturación | **PENDIENTE** | Requiere despliegue |
| Arquitectura híbrida completa | **NO CUMPLE** | Ni siquiera desplegado, sólo sería un componente cloud aislado con transferencia TLS |

## 4. Recursos: implementados, preparados y simulados

- **Implementados en AWS:** ninguno.
- **Preparados (Terraform validado):** 11 recursos (bucket S3 y sus 5 configuraciones, 2 roles IAM con sus políticas y 1 presupuesto).
- **Simulados:** sólo las pruebas de Terraform con `mock_provider` y la prueba de la compuerta con planes sintéticos (ambas rotuladas).
- **Diseñados y excluidos por costo:** VPN, NAT, EC2, RDS, ELB/WAF, KMS CMK, trail, GuardDuty, Security Hub, Organizations.

## 5. Pasos para habilitar el despliegue (los realiza el titular de la cuenta)

1. Instalar AWS CLI v2.32 o superior (`winget install Amazon.AWSCLI` o el instalador MSI oficial). Puede requerir elevación en Windows, que no se solicitó automáticamente.
2. Recomendado: crear en la consola un usuario IAM o de Identity Center con MFA para no operar con el usuario raíz.
3. Ejecutar `aws login` y luego `aws\scripts\verificar_cuenta.ps1`. Si la respuesta es "ELEGIBLE", comparar los créditos con las secciones de Billing (Créditos e Inicio) y anotar cualquier diferencia.
4. Crear `aws\terraform.tfvars` a partir del ejemplo.
5. Ejecutar `aws\scripts\desplegar.ps1` (sólo plan y compuerta), revisar la lista exacta y luego `desplegar.ps1 -Aplicar`.
6. Ejecutar `aws\scripts\pruebas_aws.ps1` y, al terminar la evaluación, `retirar.ps1 -Confirmacion RETIRAR-SGSI-UVCG`.

## 6. Gasto de bolsillo

**0.00 USD**: no se creó ningún recurso ni se usaron APIs con cargo. Estimación tras desplegar: menos de 0.001 USD, cubierto por créditos del plan Free, con 0.00 USD a la tarjeta mientras la cuenta permanezca en plan FREE.
