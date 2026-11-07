output "recovery_services_vault_id" {
  description = "ID del Recovery Services Vault (null si está deshabilitado)."
  value       = try(azurerm_recovery_services_vault.this[0].id, null)
}

output "vm_backup_policy_id" {
  description = "ID de la política diaria."
  value       = try(azurerm_backup_policy_vm.diaria[0].id, null)
}

output "resource_counts" {
  description = "Conteo de recursos del módulo."
  value = {
    recovery_vault = length(azurerm_recovery_services_vault.this)
  }
}
