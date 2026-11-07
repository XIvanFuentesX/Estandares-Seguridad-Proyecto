output "vpn_gateway_id" {
  description = "ID del gateway VPN (null si está deshabilitado)."
  value       = try(azurerm_virtual_network_gateway.this[0].id, null)
}

output "vpn_public_ip" {
  description = "IP pública del gateway (dato para configurar el dispositivo local)."
  value       = try(azurerm_public_ip.vpn[0].ip_address, null)
}

output "s2s_connection_created" {
  description = "Indica si se creó la conexión S2S."
  value       = local.create_connection
}

output "resource_counts" {
  description = "Conteo de recursos con costo."
  value = {
    vpn_gateway    = length(azurerm_virtual_network_gateway.this)
    public_ip      = length(azurerm_public_ip.vpn)
    s2s_connection = length(azurerm_virtual_network_gateway_connection.s2s)
  }
}
