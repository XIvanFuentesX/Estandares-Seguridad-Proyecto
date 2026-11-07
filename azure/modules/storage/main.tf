# Módulo storage: cuenta privada para evidencias del SGSI e intercambio híbrido de datos FICTICIOS.
# Sin acceso anónimo ni público, TLS 1.2, sin claves compartidas (sólo Entra ID/RBAC),
# versionado, borrado suave, cifrado de infraestructura y endpoint privado.

locals {
  containers = {
    evidencias          = "evidencias-sgsi"
    intercambio_hibrido = "intercambio-hibrido"
  }
}

resource "azurerm_storage_account" "this" {
  count                             = var.enable_storage ? 1 : 0
  name                              = var.storage_account_name
  location                          = var.location
  resource_group_name               = var.resource_group_name
  account_kind                      = "StorageV2"
  account_tier                      = "Standard"
  account_replication_type          = var.replication_type
  access_tier                       = "Hot"
  https_traffic_only_enabled        = true
  min_tls_version                   = "TLS1_2"
  public_network_access_enabled     = false
  allow_nested_items_to_be_public   = false
  shared_access_key_enabled         = false
  default_to_oauth_authentication   = true
  infrastructure_encryption_enabled = true
  cross_tenant_replication_enabled  = false
  local_user_enabled                = false
  sftp_enabled                      = false
  allowed_copy_scope                = "PrivateLink"
  tags                              = var.tags

  blob_properties {
    versioning_enabled            = true
    change_feed_enabled           = true
    change_feed_retention_in_days = 30
    last_access_time_enabled      = true

    delete_retention_policy {
      days = var.blob_soft_delete_days
    }

    container_delete_retention_policy {
      days = var.blob_soft_delete_days
    }
  }

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices", "Logging", "Metrics"]
  }

  sas_policy {
    expiration_period = "00.04:00:00"
    expiration_action = "Log"
  }
}

# Contenedores creados por el plano de control (ARM), compatibles con claves compartidas deshabilitadas.
resource "azurerm_storage_container" "this" {
  for_each              = var.enable_storage ? local.containers : {}
  name                  = each.value
  storage_account_id    = azurerm_storage_account.this[0].id
  container_access_type = "private"
}

resource "azurerm_storage_management_policy" "this" {
  count              = var.enable_storage ? 1 : 0
  storage_account_id = azurerm_storage_account.this[0].id

  rule {
    name    = "evidencias-a-cool"
    enabled = true
    filters {
      blob_types   = ["blockBlob"]
      prefix_match = ["${local.containers.evidencias}/"]
    }
    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than = var.cool_after_days
      }
      version {
        change_tier_to_cool_after_days_since_creation = var.cool_after_days
      }
    }
  }

  rule {
    name    = "intercambio-caducidad"
    enabled = true
    filters {
      blob_types   = ["blockBlob"]
      prefix_match = ["${local.containers.intercambio_hibrido}/"]
    }
    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = var.delete_after_days
      }
      version {
        delete_after_days_since_creation = var.delete_after_days
      }
    }
  }
}

resource "azurerm_private_endpoint" "blob" {
  count               = var.enable_storage && var.enable_private_endpoints ? 1 : 0
  name                = "pe-${var.name}-blob"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${var.name}-blob"
    private_connection_resource_id = azurerm_storage_account.this[0].id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-blob"
    private_dns_zone_ids = [var.private_dns_zone_blob_id]
  }
}

resource "azurerm_monitor_diagnostic_setting" "blob" {
  count                      = var.enable_storage && var.enable_diagnostics ? 1 : 0
  name                       = "diag-blob-a-law"
  target_resource_id         = "${azurerm_storage_account.this[0].id}/blobServices/default"
  log_analytics_workspace_id = var.log_analytics_workspace_id

  enabled_log {
    category_group = "audit"
  }

  enabled_metric {
    category = "Transaction"
  }
}
