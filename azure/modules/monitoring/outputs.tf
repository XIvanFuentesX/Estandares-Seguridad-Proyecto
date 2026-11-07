output "log_analytics_workspace_id" {
  description = "ID del workspace (null si monitoring está deshabilitado)."
  value       = try(azurerm_log_analytics_workspace.this[0].id, null)
}

output "action_group_id" {
  description = "ID del grupo de acciones."
  value       = try(azurerm_monitor_action_group.this[0].id, null)
}

output "sentinel_enabled" {
  description = "Indica si Sentinel quedó incorporado al workspace."
  value       = length(azurerm_sentinel_log_analytics_workspace_onboarding.this) > 0
}

output "budget_id" {
  description = "ID del presupuesto."
  value       = try(azurerm_consumption_budget_resource_group.this[0].id, null)
}

output "resource_counts" {
  description = "Conteo de recursos del módulo."
  value = {
    log_analytics   = length(azurerm_log_analytics_workspace.this)
    sentinel        = length(azurerm_sentinel_log_analytics_workspace_onboarding.this)
    action_group    = length(azurerm_monitor_action_group.this)
    activity_alerts = length(azurerm_monitor_activity_log_alert.sensitive) + length(azurerm_monitor_activity_log_alert.service_health)
    query_alerts    = length(azurerm_monitor_scheduled_query_rules_alert_v2.operaciones_fallidas)
    budget          = length(azurerm_consumption_budget_resource_group.this)
  }
}
