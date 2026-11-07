# Módulo monitoring: Log Analytics, registro de actividad, Sentinel opcional, grupo de acciones,
# alertas y presupuesto. IMPORTANTE: un presupuesto de Azure sólo NOTIFICA; no detiene ni
# bloquea recursos ni el gasto.

locals {
  activity_log_categories = [
    "Administrative", "Security", "Policy", "Alert", "ServiceHealth", "Recommendation", "ResourceHealth", "Autoscale",
  ]

  # Operaciones sensibles que se notifican (alertas del registro de actividad sobre el grupo de recursos).
  sensitive_operations = {
    rbac-alta        = { op = "Microsoft.Authorization/roleAssignments/write", desc = "Alta o cambio de asignación de rol" }
    rbac-baja        = { op = "Microsoft.Authorization/roleAssignments/delete", desc = "Eliminación de asignación de rol" }
    politica-baja    = { op = "Microsoft.Authorization/policyAssignments/delete", desc = "Eliminación de asignación de Azure Policy" }
    nsg-regla-cambio = { op = "Microsoft.Network/networkSecurityGroups/securityRules/write", desc = "Cambio de regla NSG" }
    nsg-regla-baja   = { op = "Microsoft.Network/networkSecurityGroups/securityRules/delete", desc = "Eliminación de regla NSG" }
    keyvault-baja    = { op = "Microsoft.KeyVault/vaults/delete", desc = "Eliminación de Key Vault" }
    storage-claves   = { op = "Microsoft.Storage/storageAccounts/listKeys/action", desc = "Lectura de claves de Storage (no debería ocurrir: claves deshabilitadas)" }
  }
}

resource "azurerm_log_analytics_workspace" "this" {
  count                        = var.enable_monitoring ? 1 : 0
  name                         = "law-${var.name}"
  location                     = var.location
  resource_group_name          = var.resource_group_name
  sku                          = "PerGB2018"
  retention_in_days            = var.log_retention_days
  daily_quota_gb               = var.log_daily_quota_gb
  local_authentication_enabled = false
  tags                         = var.tags
}

# Registro de actividad de la suscripción hacia Log Analytics (gratuito en la exportación; la ingesta se cobra).
resource "azurerm_monitor_diagnostic_setting" "activity_log" {
  count                      = var.enable_monitoring ? 1 : 0
  name                       = "diag-actividad-a-law"
  target_resource_id         = var.subscription_id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this[0].id

  dynamic "enabled_log" {
    for_each = local.activity_log_categories
    content {
      category = enabled_log.value
    }
  }
}

resource "azurerm_sentinel_log_analytics_workspace_onboarding" "this" {
  count        = var.enable_monitoring && var.enable_sentinel ? 1 : 0
  workspace_id = azurerm_log_analytics_workspace.this[0].id
}

# ---------------------------------------------------------------- Grupo de acciones y alertas
resource "azurerm_monitor_action_group" "this" {
  count               = var.enable_alerts ? 1 : 0
  name                = "ag-${var.name}-seguridad"
  resource_group_name = var.resource_group_name
  short_name          = "sgsiuvcg"
  tags                = var.tags

  dynamic "email_receiver" {
    for_each = var.alert_email_receivers
    content {
      name                    = email_receiver.key
      email_address           = email_receiver.value
      use_common_alert_schema = true
    }
  }
}

resource "azurerm_monitor_activity_log_alert" "sensitive" {
  for_each            = var.enable_alerts ? local.sensitive_operations : {}
  name                = "ala-${var.name}-${each.key}"
  location            = "global"
  resource_group_name = var.resource_group_name
  scopes              = [var.resource_group_id]
  description         = each.value.desc
  tags                = var.tags

  criteria {
    category       = "Administrative"
    operation_name = each.value.op
  }

  action {
    action_group_id = azurerm_monitor_action_group.this[0].id
  }
}

resource "azurerm_monitor_activity_log_alert" "service_health" {
  count               = var.enable_alerts ? 1 : 0
  name                = "ala-${var.name}-salud-servicio"
  location            = "global"
  resource_group_name = var.resource_group_name
  scopes              = [var.subscription_id]
  description         = "Incidentes y mantenimientos de Azure en la región del laboratorio"
  tags                = var.tags

  criteria {
    category = "ServiceHealth"
    service_health {
      events    = ["Incident", "Maintenance", "Security"]
      locations = [var.location]
    }
  }

  action {
    action_group_id = azurerm_monitor_action_group.this[0].id
  }
}

# Alerta de consulta (con costo por regla) sólo si hay Log Analytics.
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "operaciones_fallidas" {
  count                = var.enable_monitoring && var.enable_alerts ? 1 : 0
  name                 = "lqa-${var.name}-operaciones-fallidas"
  location             = var.location
  resource_group_name  = var.resource_group_name
  scopes               = [azurerm_log_analytics_workspace.this[0].id]
  description          = "Más de 5 operaciones de control fallidas en 15 minutos (posible abuso de credenciales o cambios no autorizados)"
  severity             = 2
  evaluation_frequency = "PT15M"
  window_duration      = "PT15M"
  tags                 = var.tags

  criteria {
    query                   = "AzureActivity | where ActivityStatusValue =~ 'Failure' | summarize Fallos = count() by Caller"
    time_aggregation_method = "Maximum"
    metric_measure_column   = "Fallos"
    operator                = "GreaterThan"
    threshold               = 5
  }

  action {
    action_groups = [azurerm_monitor_action_group.this[0].id]
  }
}

# ---------------------------------------------------------------- Presupuesto (sólo notifica)
resource "azurerm_consumption_budget_resource_group" "this" {
  count             = var.enable_budget ? 1 : 0
  name              = "budget-${var.name}"
  resource_group_id = var.resource_group_id
  amount            = var.budget_amount
  time_grain        = "Monthly"

  time_period {
    start_date = var.budget_start_date
  }

  dynamic "notification" {
    for_each = var.budget_thresholds
    content {
      enabled        = true
      threshold      = notification.value
      operator       = "GreaterThanOrEqualTo"
      threshold_type = "Actual"
      contact_emails = var.budget_contact_emails
      contact_groups = azurerm_monitor_action_group.this[*].id
      contact_roles  = ["Owner"]
    }
  }

  notification {
    enabled        = true
    threshold      = 100
    operator       = "GreaterThanOrEqualTo"
    threshold_type = "Forecasted"
    contact_emails = var.budget_contact_emails
    contact_groups = azurerm_monitor_action_group.this[*].id
    contact_roles  = ["Owner"]
  }
}
