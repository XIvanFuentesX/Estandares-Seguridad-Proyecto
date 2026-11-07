output "resource_group" {
  description = "Grupo de recursos del ambiente."
  value       = azurerm_resource_group.lab.name
}

output "naming" {
  description = "Nombres calculados (útiles para revisar el plan)."
  value = {
    base            = local.name
    key_vault       = local.key_vault_name
    storage_account = local.storage_account_name
  }
}

output "hub_vnet_id" {
  description = "VNet hub."
  value       = module.networking.hub_vnet_id
}

output "spoke_vnet_id" {
  description = "VNet spoke."
  value       = module.networking.spoke_vnet_id
}

output "subnets" {
  description = "Subredes del spoke (nombre y CIDR)."
  value       = module.networking.spoke_subnets
}

output "key_vault_uri" {
  description = "URI del Key Vault (resoluble sólo vía DNS privado)."
  value       = module.security.key_vault_uri
}

output "storage_account_name" {
  description = "Cuenta de almacenamiento privada."
  value       = module.storage.storage_account_name
}

output "log_analytics_workspace_id" {
  description = "Workspace de Log Analytics."
  value       = module.monitoring.log_analytics_workspace_id
}

output "firewall_private_ip" {
  description = "IP privada del firewall (siguiente salto de las UDR)."
  value       = module.security.firewall_private_ip
}

output "vpn_public_ip" {
  description = "IP pública del VPN Gateway (para el dispositivo local)."
  value       = module.hybrid_connectivity.vpn_public_ip
}

output "policy_assignments" {
  description = "Número de asignaciones de Azure Policy."
  value       = module.policies.policy_assignment_count
}

output "rbac_summary" {
  description = "Roles asignados por función (sin identificadores personales)."
  value       = module.identity.role_assignment_summary
}

output "cost_features_enabled" {
  description = "Funciones con costo habilitadas en este ambiente."
  value       = local.cost_features
}
