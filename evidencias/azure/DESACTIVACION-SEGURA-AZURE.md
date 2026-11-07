# Desactivación segura para reducir costos

Aplica sólo si en el futuro existe un despliegue. Toda desactivación es un cambio: requiere plan, revisión y registro en
`REGISTRO-CAMBIOS-AZURE.md`. Nunca usar `terraform destroy` completo sin autorización expresa (borra red, políticas y presupuesto).

## 1. Orden recomendado (del más caro al más barato)

| Orden | Componente | Cambio en `<amb>.tfvars` | Efecto y precauciones |
|---|---|---|---|
| 1 | Azure Firewall | `enable_firewall = false` | Elimina firewall, IP pública y UDR. Verificar que ninguna carga dependa de la salida por firewall. |
| 2 | Sentinel | `enable_sentinel = false` | Exportar incidentes/reglas antes; los datos del workspace se conservan según retención. |
| 3 | App Gateway WAF_v2 | `enable_app_gateway = false` | Retira la publicación web y su IP. |
| 4 | VPN Gateway | `enable_vpn_gateway = false` | Elimina gateway, conexión e IP (cambia la IP al recrear). Cerrar túnel en el router local. |
| 5 | Bastion | `enable_bastion = false` | Sin acceso administrativo por Bastion. |
| 6 | Defender Standard | `defender_plans = { ... = "Free" }` | Pierde detección avanzada; registrar la aceptación del riesgo. |
| 7 | Log Analytics | Reducir `log_daily_quota_gb` (p. ej. 0.16) | Se pierden eventos que excedan el tope (RC-08). |
| 8 | Backup | Detener protección **conservando datos** antes de `enable_backup = false` | Con inmutabilidad/borrado suave el vault no se elimina hasta que expire la retención (sigue cobrando almacenamiento). |
| 9 | Storage + PE | `enable_storage = false`, `enable_private_endpoints = false` | Descargar evidencias; el borrado suave retiene blobs 14 días. |
| 10 | Key Vault | `enable_key_vault = false` | Queda en borrado suave 90 días con purge protection: el nombre no se puede reutilizar. |

## 2. Procedimiento

1. `terraform plan -var-file=environments/<amb>.tfvars -out=desactivar.tfplan`.
2. `python -X utf8 -I azure/scripts/revisar_plan.py <plan.json>`: debe listar **sólo** las destrucciones previstas (código 2 esperado).
3. Aprobación y registro del hash del plan.
4. `terraform apply desactivar.tfplan`.
5. Verificar en *Cost Management* que el costo diario baja al día siguiente; ejecutar PT-AZ-24.
6. Conservar red, políticas, presupuesto y alertas (sin costo) salvo instrucción de cierre total.

## 3. Cierre total (fin del proyecto)

Exportar evidencias → deshabilitar inmutabilidad si es *Unlocked* y esperar retenciones → `terraform destroy` con plan
aprobado → eliminar backend de estado al final → confirmar en *Cost Management* costo 0 el mes siguiente.
