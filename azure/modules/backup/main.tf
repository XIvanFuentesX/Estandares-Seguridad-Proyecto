# Módulo backup: Recovery Services Vault con borrado suave (activo por defecto en Azure),
# inmutabilidad configurable, alertas de fallos y una política diaria reutilizable.
# Los servicios Docker locales se protegerían con el agente MARS en el host (instancia
# "On Premises Server") o copiando los respaldos ya cifrados al contenedor privado de Storage.

resource "azurerm_recovery_services_vault" "this" {
  count                         = var.enable_backup ? 1 : 0
  name                          = "rsv-${var.name}"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  sku                           = "Standard"
  storage_mode_type             = var.storage_mode_type
  cross_region_restore_enabled  = false
  public_network_access_enabled = var.public_network_access_enabled
  immutability                  = var.immutability
  tags                          = var.tags

  identity {
    type = "SystemAssigned"
  }

  monitoring {
    alerts_for_all_job_failures_enabled            = true
    alerts_for_critical_operation_failures_enabled = true
  }
}

resource "azurerm_backup_policy_vm" "diaria" {
  count               = var.enable_backup ? 1 : 0
  name                = "pol-diaria-${var.daily_retention_days}d"
  resource_group_name = var.resource_group_name
  recovery_vault_name = azurerm_recovery_services_vault.this[0].name
  policy_type         = "V2"
  timezone            = var.timezone

  backup {
    frequency = "Daily"
    time      = "02:00"
  }

  retention_daily {
    count = var.daily_retention_days
  }

  retention_weekly {
    count    = var.weekly_retention_weeks
    weekdays = ["Sunday"]
  }
}

resource "azurerm_monitor_diagnostic_setting" "vault" {
  count                          = var.enable_backup && var.enable_diagnostics ? 1 : 0
  name                           = "diag-a-law"
  target_resource_id             = azurerm_recovery_services_vault.this[0].id
  log_analytics_workspace_id     = var.log_analytics_workspace_id
  log_analytics_destination_type = "Dedicated"

  enabled_log {
    category_group = "allLogs"
  }
}
