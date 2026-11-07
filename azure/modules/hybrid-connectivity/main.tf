# Módulo hybrid-connectivity.
# Opción A (costo por hora): VPN S2S IKEv2 con política IPsec explícita (AES-256/SHA-256/DH14/PFS2048).
# Opción B (bajo costo): Azure Arc. La incorporación del host se hace con azcmagent desde el
# equipo local (no con Terraform); aquí sólo se concede el rol mínimo de incorporación.
# Un endpoint HTTPS en localhost NO es conectividad híbrida.

locals {
  create_connection = var.enable_vpn_gateway && var.onprem_gateway_address != null
}

resource "azurerm_public_ip" "vpn" {
  count               = var.enable_vpn_gateway ? 1 : 0
  name                = "pip-${var.name}-vpn"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = endswith(var.vpn_gateway_sku, "AZ") ? ["1", "2", "3"] : null
  tags                = var.tags
}

resource "azurerm_virtual_network_gateway" "this" {
  count               = var.enable_vpn_gateway ? 1 : 0
  name                = "vng-${var.name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  type                = "Vpn"
  vpn_type            = "RouteBased"
  active_active       = false
  bgp_enabled         = false
  sku                 = var.vpn_gateway_sku
  generation          = "Generation1"
  tags                = var.tags

  ip_configuration {
    name                          = "vnetGatewayConfig"
    public_ip_address_id          = azurerm_public_ip.vpn[0].id
    private_ip_address_allocation = "Dynamic"
    subnet_id                     = var.gateway_subnet_id
  }
}

resource "azurerm_local_network_gateway" "onprem" {
  count               = local.create_connection ? 1 : 0
  name                = "lng-${var.name}-laboratorio"
  location            = var.location
  resource_group_name = var.resource_group_name
  gateway_address     = var.onprem_gateway_address
  address_space       = var.onprem_address_spaces
  tags                = var.tags
}

resource "azurerm_virtual_network_gateway_connection" "s2s" {
  count                      = local.create_connection ? 1 : 0
  name                       = "cn-${var.name}-s2s"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  type                       = "IPsec"
  connection_protocol        = "IKEv2"
  virtual_network_gateway_id = azurerm_virtual_network_gateway.this[0].id
  local_network_gateway_id   = azurerm_local_network_gateway.onprem[0].id
  shared_key                 = var.vpn_shared_key
  dpd_timeout_seconds        = 45
  tags                       = var.tags

  ipsec_policy {
    dh_group         = "DHGroup14"
    ike_encryption   = "AES256"
    ike_integrity    = "SHA256"
    ipsec_encryption = "GCMAES256"
    ipsec_integrity  = "GCMAES256"
    pfs_group        = "PFS2048"
    sa_lifetime      = 27000
    sa_datasize      = 102400000
  }

  lifecycle {
    precondition {
      condition     = var.vpn_shared_key != null
      error_message = "Defina TF_VAR_vpn_shared_key desde un gestor de secretos antes de crear la conexión S2S."
    }
  }
}

# Azure Arc: rol mínimo para incorporar el host local (no concede administración de recursos).
resource "azurerm_role_assignment" "arc_onboarding" {
  count                = var.arc_onboarding_principal_id != null ? 1 : 0
  scope                = var.resource_group_id
  role_definition_name = "Azure Connected Machine Onboarding"
  principal_id         = var.arc_onboarding_principal_id
  description          = "Incorporación del host del laboratorio UVCG a Azure Arc"
}

resource "azurerm_monitor_diagnostic_setting" "vpn" {
  count                      = var.enable_vpn_gateway && var.enable_diagnostics ? 1 : 0
  name                       = "diag-a-law"
  target_resource_id         = azurerm_virtual_network_gateway.this[0].id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  enabled_log {
    category_group = "allLogs"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}
