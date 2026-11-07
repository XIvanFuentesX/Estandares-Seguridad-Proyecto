output "app_identity_id" {
  description = "ID de recurso de la identidad de la aplicación."
  value       = azurerm_user_assigned_identity.app.id
}

output "intercambio_identity_id" {
  description = "ID de recurso de la identidad de intercambio híbrido."
  value       = azurerm_user_assigned_identity.intercambio.id
}

output "app_gateway_identity_id" {
  description = "ID de recurso de la identidad de Application Gateway."
  value       = try(azurerm_user_assigned_identity.app_gateway[0].id, null)
  # Garantiza que el permiso sobre Key Vault exista antes de crear Application Gateway.
  depends_on = [azurerm_role_assignment.app_gateway_kv]
}

output "role_assignment_summary" {
  description = "Resumen función => rol => alcance (sin datos personales)."
  value       = [for a in local.sod_matrix : "${a.role} @ ${a.scope == null ? "(pendiente)" : basename(a.scope)}"]
}

output "managed_identity_count" {
  description = "Identidades administradas creadas."
  value       = 2 + length(azurerm_user_assigned_identity.app_gateway)
}
