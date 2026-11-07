output "key_vault_id" {
  description = "ID del Key Vault (null si está deshabilitado)."
  value       = try(azurerm_key_vault.this[0].id, null)
}

output "key_vault_uri" {
  description = "URI del Key Vault (sólo resoluble por DNS privado)."
  value       = try(azurerm_key_vault.this[0].vault_uri, null)
}

output "firewall_private_ip" {
  description = "IP privada del Azure Firewall (siguiente salto de las UDR)."
  value       = try(azurerm_firewall.this[0].ip_configuration[0].private_ip_address, null)
}

output "bastion_id" {
  description = "ID de Azure Bastion."
  value       = try(azurerm_bastion_host.this[0].id, null)
}

output "app_gateway_public_ip" {
  description = "IP pública del Application Gateway WAF."
  value       = try(azurerm_public_ip.app_gateway[0].ip_address, null)
}

output "defender_plans" {
  description = "Planes de Defender gestionados."
  value       = { for k, p in azurerm_security_center_subscription_pricing.this : k => p.tier }
}

output "resource_counts" {
  description = "Conteo de recursos con costo creados por este módulo (verificación de banderas)."
  value = {
    key_vault        = length(azurerm_key_vault.this)
    private_endpoint = length(azurerm_private_endpoint.key_vault)
    firewall         = length(azurerm_firewall.this)
    bastion          = length(azurerm_bastion_host.this)
    app_gateway      = length(azurerm_application_gateway.this)
    public_ips = (length(azurerm_public_ip.firewall) + length(azurerm_public_ip.firewall_management) +
    length(azurerm_public_ip.bastion) + length(azurerm_public_ip.app_gateway))
  }
}

output "key_vault_hardening" {
  description = "Configuración de endurecimiento del Key Vault."
  value = [for kv in azurerm_key_vault.this : {
    rbac           = kv.rbac_authorization_enabled
    acceso_publico = kv.public_network_access_enabled
    purge          = kv.purge_protection_enabled
  }]
}
