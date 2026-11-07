locals {
  location_short = {
    eastus2        = "eus2"
    southcentralus = "scus"
  }[var.location]

  # Convención: <prefijo>-<ambiente>-<región corta>, p. ej. uvcg-sgsi-dev-eus2
  name = "${var.prefix}-${var.environment}-${local.location_short}"

  key_vault_name       = substr("kv-${replace(var.prefix, "-", "")}-${var.environment}-${var.unique_suffix}", 0, 24)
  storage_account_name = substr("st${replace(var.prefix, "-", "")}${var.environment}${var.unique_suffix}", 0, 24)

  required_tag_names = ["proyecto", "ambiente", "propietario", "clasificacion", "gestionado_por"]

  tags = merge(var.extra_tags, {
    proyecto       = "SGSI-UVCG"
    ambiente       = var.environment
    propietario    = var.owner
    centro_costo   = var.cost_center
    clasificacion  = var.data_classification
    gestionado_por = "terraform"
  })

  hub_subnets = {
    firewall      = cidrsubnet(var.hub_address_space, 10, 0)    # /26 AzureFirewallSubnet
    firewall_mgmt = cidrsubnet(var.hub_address_space, 10, 1)    # /26 AzureFirewallManagementSubnet
    bastion       = cidrsubnet(var.hub_address_space, 10, 4)    # /26 AzureBastionSubnet
    management    = cidrsubnet(var.hub_address_space, 8, 10)    # /24 gestión
    gateway       = cidrsubnet(var.hub_address_space, 11, 2040) # /27 GatewaySubnet (x.x.255.0/27)
  }

  spoke_subnets = {
    dmz              = cidrsubnet(var.spoke_address_space, 8, 10)
    apps             = cidrsubnet(var.spoke_address_space, 8, 20)
    datos            = cidrsubnet(var.spoke_address_space, 8, 30)
    gestion          = cidrsubnet(var.spoke_address_space, 8, 40)
    seguridad        = cidrsubnet(var.spoke_address_space, 8, 50)
    privateendpoints = cidrsubnet(var.spoke_address_space, 8, 60)
  }

  diagnostics_enabled = var.enable_monitoring

  # Resumen de funciones con costo (salida informativa y base del análisis de costos).
  cost_features = {
    log_analytics     = var.enable_monitoring
    sentinel          = var.enable_monitoring && var.enable_sentinel
    alerta_consulta   = var.enable_monitoring && var.enable_alerts
    key_vault         = var.enable_key_vault
    storage           = var.enable_storage
    private_endpoints = var.enable_private_endpoints
    backup_vault      = var.enable_backup
    vpn_gateway       = var.enable_vpn_gateway
    azure_firewall    = var.enable_firewall
    bastion           = var.enable_bastion
    app_gateway_waf   = var.enable_app_gateway
    defender_standard = [for k, v in var.defender_plans : k if v == "Standard"]
  }
}
