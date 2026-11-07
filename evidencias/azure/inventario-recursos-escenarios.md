# Inventario de recursos proyectados por escenario

Generado por `azure/scripts/generar_inventario_diagrama.py` a partir del **plan simulado** de
`terraform test -verbose` con `mock_provider` (Terraform 1.14.9, AzureRM 4.81.0). El plan simulado expande
módulos, `count`/`for_each`, validaciones y precondiciones con los `.tfvars.example` de cada ambiente, pero
**no** consulta Azure: no valida cuotas, disponibilidad de nombres globales, permisos ni políticas reales.
Estado de todos los recursos: **PREPARADO / no desplegado**.

Columnas: `default` = sin `-var-file`; `dev` = Escenario 1; `demo` = Escenario 2; `inst` = Escenario 3.

| Módulo | Tipo de recurso | Costo | default | dev | demo | inst |
|---|---|---|---:|---:|---:|---:|
| backup | `azurerm_backup_policy_vm` | Sin costo directo | 0 | 0 | 1 | 1 |
| backup | `azurerm_monitor_diagnostic_setting` | Sin costo directo | 0 | 0 | 1 | 1 |
| backup | `azurerm_recovery_services_vault` | Por instancia protegida + GB | 0 | 0 | 1 | 1 |
| hybrid_connectivity | `azurerm_monitor_diagnostic_setting` | Sin costo directo | 0 | 0 | 0 | 1 |
| hybrid_connectivity | `azurerm_public_ip` | Por hora (IP estándar) | 0 | 0 | 0 | 1 |
| hybrid_connectivity | `azurerm_virtual_network_gateway` | Por hora | 0 | 0 | 0 | 1 |
| identity | `azurerm_role_assignment` | Sin costo directo | 0 | 3 | 3 | 4 |
| identity | `azurerm_user_assigned_identity` | Sin costo directo | 2 | 2 | 2 | 3 |
| monitoring | `azurerm_consumption_budget_resource_group` | Sin costo directo | 1 | 1 | 1 | 1 |
| monitoring | `azurerm_log_analytics_workspace` | Por GB ingerido (5 GB/mes sin costo según API) | 0 | 1 | 1 | 1 |
| monitoring | `azurerm_monitor_action_group` | Sin costo directo | 0 | 1 | 1 | 1 |
| monitoring | `azurerm_monitor_activity_log_alert` | Sin costo directo | 0 | 8 | 8 | 8 |
| monitoring | `azurerm_monitor_diagnostic_setting` | Sin costo directo | 0 | 1 | 1 | 1 |
| monitoring | `azurerm_monitor_scheduled_query_rules_alert_v2` | Mensual por regla | 0 | 1 | 1 | 1 |
| monitoring | `azurerm_sentinel_log_analytics_workspace_onboarding` | Por GB analizado | 0 | 0 | 0 | 1 |
| networking | `azurerm_monitor_diagnostic_setting` | Sin costo directo | 0 | 6 | 6 | 6 |
| networking | `azurerm_network_security_group` | Sin costo directo | 7 | 7 | 7 | 7 |
| networking | `azurerm_network_security_rule` | Sin costo directo | 11 | 11 | 11 | 15 |
| networking | `azurerm_private_dns_zone` | Mensual por zona + consultas | 0 | 2 | 2 | 2 |
| networking | `azurerm_private_dns_zone_virtual_network_link` | Sin costo directo | 0 | 4 | 4 | 4 |
| networking | `azurerm_route_table` | Sin costo directo | 0 | 0 | 0 | 7 |
| networking | `azurerm_subnet` | Sin costo directo | 11 | 11 | 11 | 11 |
| networking | `azurerm_subnet_network_security_group_association` | Sin costo directo | 7 | 7 | 7 | 7 |
| networking | `azurerm_subnet_route_table_association` | Sin costo directo | 0 | 0 | 0 | 7 |
| networking | `azurerm_virtual_network` | Sin costo directo | 2 | 2 | 2 | 2 |
| networking | `azurerm_virtual_network_peering` | Por GB transferido (0 sin tráfico) | 2 | 2 | 2 | 2 |
| policies | `azurerm_resource_group_policy_assignment` | Sin costo directo | 15 | 15 | 15 | 15 |
| raíz | `azurerm_resource_group` | Sin costo directo | 1 | 1 | 1 | 1 |
| security | `azurerm_application_gateway` | Por hora + unidades de capacidad | 0 | 0 | 0 | 1 |
| security | `azurerm_bastion_host` | Por hora (Developer: no verificado) | 0 | 0 | 0 | 1 |
| security | `azurerm_firewall` | Por hora (alto) | 0 | 0 | 0 | 1 |
| security | `azurerm_firewall_policy` | Sin costo directo | 0 | 0 | 0 | 1 |
| security | `azurerm_firewall_policy_rule_collection_group` | Sin costo directo | 0 | 0 | 0 | 1 |
| security | `azurerm_key_vault` | Por operaciones | 0 | 1 | 1 | 1 |
| security | `azurerm_monitor_diagnostic_setting` | Sin costo directo | 0 | 1 | 1 | 4 |
| security | `azurerm_private_endpoint` | Por hora + GB procesado | 0 | 1 | 1 | 1 |
| security | `azurerm_public_ip` | Por hora (IP estándar) | 0 | 0 | 0 | 3 |
| security | `azurerm_security_center_contact` | Sin costo directo | 0 | 1 | 1 | 1 |
| security | `azurerm_security_center_subscription_pricing` | Free = 0; Standard = por recurso/hora | 4 | 4 | 4 | 4 |
| security | `azurerm_web_application_firewall_policy` | Sin costo directo | 0 | 0 | 0 | 1 |
| storage | `azurerm_monitor_diagnostic_setting` | Sin costo directo | 0 | 1 | 1 | 1 |
| storage | `azurerm_private_endpoint` | Por hora + GB procesado | 0 | 1 | 1 | 1 |
| storage | `azurerm_storage_account` | Por GB + operaciones | 0 | 1 | 1 | 1 |
| storage | `azurerm_storage_container` | Sin costo directo | 0 | 2 | 2 | 2 |
| storage | `azurerm_storage_management_policy` | Sin costo directo | 0 | 1 | 1 | 1 |
| **Total** | | | **63** | **100** | **103** | **139** |

## Recursos con costo por escenario (direcciones exactas)

### Valores por defecto (sin costo) — 0 recursos con cargo potencial

- (ninguno)

### Escenario 1 — Mínimo académico (dev) — 8 recursos con cargo potencial

- `module.monitoring.azurerm_log_analytics_workspace.this[0]`
- `module.monitoring.azurerm_monitor_scheduled_query_rules_alert_v2.operaciones_fallidas[0]`
- `module.networking.azurerm_private_dns_zone.this["blob"]`
- `module.networking.azurerm_private_dns_zone.this["vault"]`
- `module.security.azurerm_key_vault.this[0]`
- `module.security.azurerm_private_endpoint.key_vault[0]`
- `module.storage.azurerm_private_endpoint.blob[0]`
- `module.storage.azurerm_storage_account.this[0]`

### Escenario 2 — Académico recomendado (demo) — 9 recursos con cargo potencial

- `module.backup.azurerm_recovery_services_vault.this[0]`
- `module.monitoring.azurerm_log_analytics_workspace.this[0]`
- `module.monitoring.azurerm_monitor_scheduled_query_rules_alert_v2.operaciones_fallidas[0]`
- `module.networking.azurerm_private_dns_zone.this["blob"]`
- `module.networking.azurerm_private_dns_zone.this["vault"]`
- `module.security.azurerm_key_vault.this[0]`
- `module.security.azurerm_private_endpoint.key_vault[0]`
- `module.storage.azurerm_private_endpoint.blob[0]`
- `module.storage.azurerm_storage_account.this[0]`

### Escenario 3 — Institucional de referencia (inst) — 18 recursos con cargo potencial

- `module.backup.azurerm_recovery_services_vault.this[0]`
- `module.hybrid_connectivity.azurerm_public_ip.vpn[0]`
- `module.hybrid_connectivity.azurerm_virtual_network_gateway.this[0]`
- `module.monitoring.azurerm_log_analytics_workspace.this[0]`
- `module.monitoring.azurerm_monitor_scheduled_query_rules_alert_v2.operaciones_fallidas[0]`
- `module.monitoring.azurerm_sentinel_log_analytics_workspace_onboarding.this[0]`
- `module.networking.azurerm_private_dns_zone.this["blob"]`
- `module.networking.azurerm_private_dns_zone.this["vault"]`
- `module.security.azurerm_application_gateway.this[0]`
- `module.security.azurerm_bastion_host.this[0]`
- `module.security.azurerm_firewall.this[0]`
- `module.security.azurerm_key_vault.this[0]`
- `module.security.azurerm_private_endpoint.key_vault[0]`
- `module.security.azurerm_public_ip.app_gateway[0]`
- `module.security.azurerm_public_ip.bastion[0]`
- `module.security.azurerm_public_ip.firewall[0]`
- `module.storage.azurerm_private_endpoint.blob[0]`
- `module.storage.azurerm_storage_account.this[0]`

