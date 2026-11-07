# Módulo security: Key Vault (RBAC, privado, purge protection), Azure Firewall opcional,
# Azure Bastion opcional, Application Gateway WAF_v2 opcional y Defender for Cloud.

locals {
  firewall_basic = var.firewall_sku_tier == "Basic"
  bastion_dev    = var.bastion_sku == "Developer"

  diag_targets = merge(
    { for id in azurerm_key_vault.this[*].id : "keyvault" => id },
    { for id in azurerm_firewall.this[*].id : "firewall" => id },
    { for id in azurerm_bastion_host.this[*].id : "bastion" => id if !local.bastion_dev },
    { for id in azurerm_application_gateway.this[*].id : "appgw" => id },
  )
  diag_keys = toset(compact([
    var.enable_key_vault ? "keyvault" : "",
    var.enable_firewall ? "firewall" : "",
    var.enable_bastion && !local.bastion_dev ? "bastion" : "",
    var.enable_app_gateway ? "appgw" : "",
  ]))
}

# ---------------------------------------------------------------- Key Vault
resource "azurerm_key_vault" "this" {
  count                         = var.enable_key_vault ? 1 : 0
  name                          = var.key_vault_name
  location                      = var.location
  resource_group_name           = var.resource_group_name
  tenant_id                     = var.tenant_id
  sku_name                      = "standard"
  rbac_authorization_enabled    = true
  public_network_access_enabled = false
  purge_protection_enabled      = true
  soft_delete_retention_days    = var.key_vault_soft_delete_days
  tags                          = var.tags

  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
  }
}

resource "azurerm_private_endpoint" "key_vault" {
  count               = var.enable_key_vault && var.enable_private_endpoints ? 1 : 0
  name                = "pe-${var.name}-kv"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id
  tags                = var.tags

  private_service_connection {
    name                           = "psc-${var.name}-kv"
    private_connection_resource_id = azurerm_key_vault.this[0].id
    subresource_names              = ["vault"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-vault"
    private_dns_zone_ids = [var.private_dns_zone_vault_id]
  }
}

# ---------------------------------------------------------------- Azure Firewall
resource "azurerm_public_ip" "firewall" {
  count               = var.enable_firewall ? 1 : 0
  name                = "pip-${var.name}-afw"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_public_ip" "firewall_management" {
  count               = var.enable_firewall && local.firewall_basic ? 1 : 0
  name                = "pip-${var.name}-afw-mgmt"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_firewall_policy" "this" {
  count                    = var.enable_firewall ? 1 : 0
  name                     = "afwp-${var.name}"
  location                 = var.location
  resource_group_name      = var.resource_group_name
  sku                      = var.firewall_sku_tier
  threat_intelligence_mode = local.firewall_basic ? "Alert" : "Deny"
  tags                     = var.tags
}

resource "azurerm_firewall_policy_rule_collection_group" "this" {
  count              = var.enable_firewall ? 1 : 0
  name               = "rcg-sgsi-uvcg"
  firewall_policy_id = azurerm_firewall_policy.this[0].id
  priority           = 200

  network_rule_collection {
    name     = "flujos-entre-zonas"
    priority = 200
    action   = "Allow"

    rule {
      name                  = "dmz-a-apps-https"
      protocols             = ["TCP"]
      source_addresses      = [var.spoke_subnets["dmz"]]
      destination_addresses = [var.spoke_subnets["apps"]]
      destination_ports     = ["443"]
    }
    rule {
      name                  = "apps-a-datos-postgresql"
      protocols             = ["TCP"]
      source_addresses      = [var.spoke_subnets["apps"]]
      destination_addresses = [var.spoke_subnets["datos"]]
      destination_ports     = ["5432"]
    }
    rule {
      name                  = "privado-https"
      protocols             = ["TCP"]
      source_addresses      = concat([var.spoke_subnets["apps"], var.spoke_subnets["gestion"], var.spoke_subnets["seguridad"]], var.onprem_address_spaces)
      destination_addresses = [var.spoke_subnets["privateendpoints"]]
      destination_ports     = ["443"]
    }
  }

  application_rule_collection {
    name     = "salida-controlada"
    priority = 300
    action   = "Allow"

    rule {
      name              = "fqdn-autorizados"
      source_addresses  = [var.spoke_subnets["apps"], var.spoke_subnets["gestion"], var.spoke_subnets["seguridad"]]
      destination_fqdns = var.allowed_egress_fqdns
      protocols {
        type = "Https"
        port = 443
      }
    }
  }
}

resource "azurerm_firewall" "this" {
  count               = var.enable_firewall ? 1 : 0
  name                = "afw-${var.name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku_name            = "AZFW_VNet"
  sku_tier            = var.firewall_sku_tier
  firewall_policy_id  = azurerm_firewall_policy.this[0].id
  tags                = var.tags

  ip_configuration {
    name                 = "ipconfig"
    subnet_id            = var.firewall_subnet_id
    public_ip_address_id = azurerm_public_ip.firewall[0].id
  }

  dynamic "management_ip_configuration" {
    for_each = local.firewall_basic ? [1] : []
    content {
      name                 = "mgmt-ipconfig"
      subnet_id            = var.firewall_management_subnet_id
      public_ip_address_id = azurerm_public_ip.firewall_management[0].id
    }
  }

  depends_on = [azurerm_firewall_policy_rule_collection_group.this]
}

# ---------------------------------------------------------------- Azure Bastion
resource "azurerm_public_ip" "bastion" {
  count               = var.enable_bastion && !local.bastion_dev ? 1 : 0
  name                = "pip-${var.name}-bas"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_bastion_host" "this" {
  count                  = var.enable_bastion ? 1 : 0
  name                   = "bas-${var.name}"
  location               = var.location
  resource_group_name    = var.resource_group_name
  sku                    = var.bastion_sku
  virtual_network_id     = local.bastion_dev ? var.hub_vnet_id : null
  copy_paste_enabled     = false
  file_copy_enabled      = false
  shareable_link_enabled = false
  tags                   = var.tags

  dynamic "ip_configuration" {
    for_each = local.bastion_dev ? [] : [1]
    content {
      name                 = "ipconfig"
      subnet_id            = var.bastion_subnet_id
      public_ip_address_id = azurerm_public_ip.bastion[0].id
    }
  }
}

# ---------------------------------------------------------------- Application Gateway WAF_v2
resource "azurerm_public_ip" "app_gateway" {
  count               = var.enable_app_gateway ? 1 : 0
  name                = "pip-${var.name}-agw"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_web_application_firewall_policy" "this" {
  count               = var.enable_app_gateway ? 1 : 0
  name                = "wafp-${var.name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  policy_settings {
    enabled                     = true
    mode                        = "Prevention"
    request_body_check          = true
    max_request_body_size_in_kb = 128
    file_upload_limit_in_mb     = 10
  }

  managed_rules {
    managed_rule_set {
      type    = "OWASP"
      version = "3.2"
    }
  }
}

resource "azurerm_application_gateway" "this" {
  count               = var.enable_app_gateway ? 1 : 0
  name                = "agw-${var.name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  firewall_policy_id  = azurerm_web_application_firewall_policy.this[0].id
  http2_enabled       = true
  tags                = var.tags

  sku {
    name = "WAF_v2"
    tier = "WAF_v2"
  }

  autoscale_configuration {
    min_capacity = 0
    max_capacity = var.app_gateway_max_capacity
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [var.app_gateway_identity_id]
  }

  gateway_ip_configuration {
    name      = "gwip"
    subnet_id = var.app_gateway_subnet_id
  }

  frontend_ip_configuration {
    name                 = "fe-publica"
    public_ip_address_id = azurerm_public_ip.app_gateway[0].id
  }

  frontend_port {
    name = "https"
    port = 443
  }

  ssl_certificate {
    name                = "cert-uvcg"
    key_vault_secret_id = var.app_gateway_certificate_secret_id
  }

  ssl_policy {
    policy_type = "Predefined"
    policy_name = "AppGwSslPolicy20220101S"
  }

  http_listener {
    name                           = "https-listener"
    frontend_ip_configuration_name = "fe-publica"
    frontend_port_name             = "https"
    protocol                       = "Https"
    ssl_certificate_name           = "cert-uvcg"
  }

  backend_address_pool {
    name         = "pool-apps"
    ip_addresses = var.app_gateway_backend_addresses
  }

  probe {
    name                                      = "probe-salud"
    protocol                                  = "Https"
    path                                      = "/health"
    interval                                  = 30
    timeout                                   = 30
    unhealthy_threshold                       = 3
    pick_host_name_from_backend_http_settings = true
  }

  backend_http_settings {
    name                                = "https-backend"
    cookie_based_affinity               = "Disabled"
    port                                = 443
    protocol                            = "Https"
    request_timeout                     = 30
    pick_host_name_from_backend_address = true
    probe_name                          = "probe-salud"
  }

  request_routing_rule {
    name                       = "regla-https"
    rule_type                  = "Basic"
    priority                   = 100
    http_listener_name         = "https-listener"
    backend_address_pool_name  = "pool-apps"
    backend_http_settings_name = "https-backend"
  }

  lifecycle {
    precondition {
      condition     = var.app_gateway_certificate_secret_id != null && var.app_gateway_identity_id != null && length(var.app_gateway_backend_addresses) > 0
      error_message = "Application Gateway requiere certificado en Key Vault, identidad administrada y al menos un backend privado."
    }
  }
}

# ---------------------------------------------------------------- Defender for Cloud
resource "azurerm_security_center_subscription_pricing" "this" {
  for_each      = var.manage_defender_plans ? var.defender_plans : {}
  resource_type = each.key
  tier          = each.value
}

resource "azurerm_security_center_contact" "this" {
  count               = var.manage_defender_plans && var.security_contact_email != null ? 1 : 0
  name                = "contacto-seguridad-uvcg"
  email               = var.security_contact_email
  alert_notifications = true
  alerts_to_admins    = true
}

# ---------------------------------------------------------------- Diagnósticos
resource "azurerm_monitor_diagnostic_setting" "this" {
  for_each                       = var.enable_diagnostics ? local.diag_keys : toset([])
  name                           = "diag-a-law"
  target_resource_id             = local.diag_targets[each.key]
  log_analytics_workspace_id     = var.log_analytics_workspace_id
  log_analytics_destination_type = each.key == "firewall" ? "Dedicated" : null

  enabled_log {
    category_group = each.key == "keyvault" ? "audit" : "allLogs"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}
