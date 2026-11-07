# Registro de riesgos AWS y procedimiento de retirada segura

## Riesgos (escala P×I 1–5 de `governance/matriz-riesgos.md`)

| ID | Riesgo | P | I | Inherente | Controles | Residual | Vínculo |
|---|---|---|---|---|---|---|---|
| RA-01 | Paso a plan Paid (manual o por Organizations/Control Tower) y cargos posteriores | 2 | 5 | 10 Alto | Verificación FREE/ACTIVE antes y después; denegación explícita de `freetier:UpgradeAccountPlan` en los roles; no usar Organizations | 5 Moderado | R-020 |
| RA-02 | Exposición pública del bucket | 2 | 4 | 8 Moderado | Bloqueo de acceso público, `BucketOwnerEnforced`, política sólo TLS, prueba PT-AWS-11 | 2 Bajo | R-003 |
| RA-03 | Credenciales permanentes filtradas | 2 | 5 | 10 Alto | Sólo `aws login` temporal; sin usuarios IAM ni claves; exportación sólo a variables del proceso | 3 Bajo | R-015 |
| RA-04 | Subida de datos reales | 2 | 5 | 10 Alto | Prefijo único `laboratorio/`, sólo muestras rotuladas FICTICIA, expiración a 30 días | 4 Bajo | R-003 |
| RA-05 | Despliegue en cuenta equivocada | 2 | 3 | 6 Moderado | `allowed_account_ids` y verificación previa | 2 Bajo | R-017 |
| RA-06 | Recursos olvidados al vencer el plan (cierre de cuenta y pérdida de datos) | 3 | 2 | 6 Moderado | Retirada documentada; datos sólo ficticios | 2 Bajo | R-020 |
| RA-07 | Uso del usuario raíz para operar | 3 | 4 | 12 Alto | Advertencia en la verificación; recomendación de usuario IAM/Identity Center con MFA | 6 Moderado | R-016 |
| RA-08 | Confundir la demostración con una conexión híbrida privada | 3 | 3 | 9 Moderado | Declarado explícitamente en cierre y pruebas | 3 Bajo | — |

## Procedimiento de retirada segura

1. Ejecutar `aws\scripts\pruebas_aws.ps1` y conservar las evidencias.
2. `aws login` con la misma cuenta y `aws\scripts\verificar_cuenta.ps1`.
3. `aws\scripts\retirar.ps1 -Confirmacion RETIRAR-SGSI-UVCG`: inventaría los objetos, vacía sólo el bucket `uvcg-sgsi-lab-*` y ejecuta `terraform destroy` del estado de `aws/`. No es automático ni se invoca desde otros scripts.
4. Comprobar en la consola de Billing que no quedan recursos ni uso, y guardar `retirada-estado-plan-*.json`.
5. No cerrar ni mejorar la cuenta desde estos scripts; el cierre de la cuenta es decisión del titular.
