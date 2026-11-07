output "hub_vnet_id" {
  description = "ID de la VNet hub."
  value       = azurerm_virtual_network.hub.id
}

output "spoke_vnet_id" {
  description = "ID de la VNet spoke."
  value       = azurerm_virtual_network.spoke.id
}

output "hub_subnet_ids" {
  description = "IDs de subredes del hub por clave lógica."
  value       = { for k, s in azurerm_subnet.hub : k => s.id }
}

output "spoke_subnet_ids" {
  description = "IDs de subredes del spoke por zona."
  value       = { for k, s in azurerm_subnet.spoke : k => s.id }
}

output "spoke_subnets" {
  description = "Resumen de subredes del spoke (nombre y CIDR)."
  value       = { for k, s in azurerm_subnet.spoke : k => { name = s.name, cidr = var.spoke_subnets[k] } }
}

output "nsg_ids" {
  description = "IDs de NSG por zona."
  value       = { for k, n in azurerm_network_security_group.spoke : k => n.id }
}

output "private_dns_zone_ids" {
  description = "IDs de zonas DNS privadas (blob, vault) si se habilitaron."
  value       = { for k, z in azurerm_private_dns_zone.this : k => z.id }
}

output "route_table_ids" {
  description = "Tablas de rutas (UDR) creadas cuando el firewall está habilitado."
  value       = { for k, r in azurerm_route_table.spoke : k => r.id }
}

output "deny_rule_priorities" {
  description = "Prioridad y acción de la regla de denegación final por zona (verificación)."
  value       = { for k, r in azurerm_network_security_rule.deny_inbound : k => "${r.access}:${r.priority}" }
}

output "private_dns_zone_count" {
  description = "Zonas DNS privadas (con costo mensual por zona)."
  value       = length(azurerm_private_dns_zone.this)
}
