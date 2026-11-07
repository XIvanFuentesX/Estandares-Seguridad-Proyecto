# Raíz de la infraestructura Azure del SGSI UVCG — PREPARADA, NO DESPLEGADA.
# Orquesta los módulos; todo lo que tiene costo depende de banderas enable_* en false por defecto.

data "azurerm_client_config" "current" {}

data "azurerm_subscription" "current" {}

resource "azurerm_resource_group" "lab" {
  name     = "rg-${local.name}"
  location = var.location
  tags     = local.tags

  lifecycle {
    precondition {
      condition     = !var.enable_sentinel || var.enable_monitoring
      error_message = "enable_sentinel requiere enable_monitoring = true."
    }
    precondition {
      condition     = !(var.enable_key_vault || var.enable_storage) || var.enable_private_endpoints || var.environment == "dev"
      error_message = "Key Vault/Storage sin acceso público necesitan endpoints privados fuera de dev."
    }
    precondition {
      condition     = !var.enable_app_gateway || var.enable_key_vault
      error_message = "Application Gateway obtiene su certificado de Key Vault: habilite enable_key_vault."
    }
  }
}

module "networking" {
  source = "./modules/networking"

  name                  = local.name
  location              = var.location
  resource_group_name   = azurerm_resource_group.lab.name
  tags                  = local.tags
  hub_address_space     = var.hub_address_space
  spoke_address_space   = var.spoke_address_space
  hub_subnets           = local.hub_subnets
  spoke_subnets         = local.spoke_subnets
  onprem_address_spaces = var.onprem_address_spaces

  enable_vpn_gateway    = var.enable_vpn_gateway
  vpn_gateway_id        = module.hybrid_connectivity.vpn_gateway_id
  enable_firewall       = var.enable_firewall
  firewall_private_ip   = module.security.firewall_private_ip
  enable_app_gateway    = var.enable_app_gateway
  enable_bastion_access = var.enable_bastion && var.bastion_sku != "Developer"
  enable_private_dns    = var.enable_private_endpoints

  enable_diagnostics         = local.diagnostics_enabled
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id
}

module "monitoring" {
  source = "./modules/monitoring"

  name                = local.name
  location            = var.location
  resource_group_name = azurerm_resource_group.lab.name
  resource_group_id   = azurerm_resource_group.lab.id
  subscription_id     = data.azurerm_subscription.current.id
  tags                = local.tags

  enable_monitoring     = var.enable_monitoring
  log_retention_days    = var.log_retention_days
  log_daily_quota_gb    = var.log_daily_quota_gb
  enable_sentinel       = var.enable_sentinel
  enable_alerts         = var.enable_alerts
  alert_email_receivers = var.alert_email_receivers
  enable_budget         = var.enable_budget
  budget_amount         = var.budget_amount
  budget_start_date     = var.budget_start_date
  budget_thresholds     = var.budget_thresholds
  budget_contact_emails = var.budget_contact_emails
}

module "security" {
  source = "./modules/security"

  name                = local.name
  location            = var.location
  resource_group_name = azurerm_resource_group.lab.name
  tags                = local.tags
  tenant_id           = data.azurerm_client_config.current.tenant_id

  enable_key_vault           = var.enable_key_vault
  key_vault_name             = local.key_vault_name
  enable_private_endpoints   = var.enable_private_endpoints
  private_endpoint_subnet_id = module.networking.spoke_subnet_ids["privateendpoints"]
  private_dns_zone_vault_id  = lookup(module.networking.private_dns_zone_ids, "vault", null)

  enable_firewall               = var.enable_firewall
  firewall_sku_tier             = var.firewall_sku_tier
  firewall_subnet_id            = module.networking.hub_subnet_ids["firewall"]
  firewall_management_subnet_id = module.networking.hub_subnet_ids["firewall_mgmt"]
  spoke_subnets                 = local.spoke_subnets
  onprem_address_spaces         = var.onprem_address_spaces
  allowed_egress_fqdns          = var.allowed_egress_fqdns

  enable_bastion    = var.enable_bastion
  bastion_sku       = var.bastion_sku
  bastion_subnet_id = module.networking.hub_subnet_ids["bastion"]
  hub_vnet_id       = module.networking.hub_vnet_id

  enable_app_gateway                = var.enable_app_gateway
  app_gateway_subnet_id             = module.networking.spoke_subnet_ids["dmz"]
  app_gateway_identity_id           = module.identity.app_gateway_identity_id
  app_gateway_certificate_secret_id = var.app_gateway_certificate_secret_id
  app_gateway_backend_addresses     = var.app_gateway_backend_addresses

  manage_defender_plans  = var.manage_defender_plans
  defender_plans         = var.defender_plans
  security_contact_email = var.security_contact_email

  enable_diagnostics         = local.diagnostics_enabled
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id
}

module "storage" {
  source = "./modules/storage"

  name                 = local.name
  storage_account_name = local.storage_account_name
  location             = var.location
  resource_group_name  = azurerm_resource_group.lab.name
  tags                 = local.tags

  enable_storage        = var.enable_storage
  replication_type      = var.storage_replication_type
  blob_soft_delete_days = var.blob_soft_delete_days
  cool_after_days       = 30
  delete_after_days     = 30

  enable_private_endpoints   = var.enable_private_endpoints
  private_endpoint_subnet_id = module.networking.spoke_subnet_ids["privateendpoints"]
  private_dns_zone_blob_id   = lookup(module.networking.private_dns_zone_ids, "blob", null)

  enable_diagnostics         = local.diagnostics_enabled
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id
}

module "backup" {
  source = "./modules/backup"

  name                = local.name
  location            = var.location
  resource_group_name = azurerm_resource_group.lab.name
  tags                = local.tags

  enable_backup                 = var.enable_backup
  storage_mode_type             = var.backup_storage_mode
  public_network_access_enabled = var.backup_public_network_access
  immutability                  = var.backup_immutability
  daily_retention_days          = 30
  weekly_retention_weeks        = 12
  timezone                      = "Central America Standard Time"

  enable_diagnostics         = local.diagnostics_enabled
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id
}

module "hybrid_connectivity" {
  source = "./modules/hybrid-connectivity"

  name                = local.name
  location            = var.location
  resource_group_name = azurerm_resource_group.lab.name
  resource_group_id   = azurerm_resource_group.lab.id
  tags                = local.tags

  enable_vpn_gateway          = var.enable_vpn_gateway
  vpn_gateway_sku             = var.vpn_gateway_sku
  gateway_subnet_id           = module.networking.hub_subnet_ids["gateway"]
  onprem_gateway_address      = var.onprem_gateway_address
  onprem_address_spaces       = var.onprem_address_spaces
  vpn_shared_key              = var.vpn_shared_key
  arc_onboarding_principal_id = var.arc_onboarding_principal_id

  enable_diagnostics         = local.diagnostics_enabled
  log_analytics_workspace_id = module.monitoring.log_analytics_workspace_id
}

module "identity" {
  source = "./modules/identity"

  name                = local.name
  location            = var.location
  resource_group_name = azurerm_resource_group.lab.name
  resource_group_id   = azurerm_resource_group.lab.id
  tags                = local.tags

  enable_app_gateway_identity = var.enable_app_gateway
  enable_key_vault            = var.enable_key_vault
  key_vault_id                = module.security.key_vault_id
  enable_storage              = var.enable_storage
  storage_container_ids       = module.storage.container_ids
  enable_backup               = var.enable_backup
  recovery_vault_id           = module.backup.recovery_services_vault_id
  enable_monitoring           = var.enable_monitoring
  log_analytics_workspace_id  = module.monitoring.log_analytics_workspace_id

  principals                  = var.principals
  arc_machine_principal_id    = var.arc_machine_principal_id
  additional_role_assignments = var.additional_role_assignments
}

module "policies" {
  source = "./modules/policies"

  name              = local.name
  resource_group_id = azurerm_resource_group.lab.id
  enable_policies   = var.enable_policies
  allowed_locations = [var.location]
  required_tags     = local.required_tag_names
  effect            = var.policy_effect
}
