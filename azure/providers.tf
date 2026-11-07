provider "azurerm" {
  # null => se toma de ARM_SUBSCRIPTION_ID o de la sesión de Azure CLI. Nunca se escribe en el repositorio.
  subscription_id = var.subscription_id

  # Las cuentas de almacenamiento no aceptan claves compartidas: el proveedor usa Entra ID.
  storage_use_azuread = true

  # Registra sólo los proveedores de recursos que usa este código (ver README).
  resource_provider_registrations = "core"
  resource_providers_to_register = [
    "Microsoft.Network",
    "Microsoft.KeyVault",
    "Microsoft.Storage",
    "Microsoft.OperationalInsights",
    "Microsoft.OperationsManagement",
    "Microsoft.Insights",
    "Microsoft.AlertsManagement",
    "Microsoft.RecoveryServices",
    "Microsoft.Security",
    "Microsoft.SecurityInsights",
    "Microsoft.ManagedIdentity",
    "Microsoft.PolicyInsights",
    "Microsoft.Consumption",
    "Microsoft.HybridCompute",
  ]

  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
    key_vault {
      # Purge protection impide la purga; tampoco se intenta al destruir.
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
    recovery_service {
      purge_protected_items_from_vault_on_destroy          = false
      vm_backup_stop_protection_and_retain_data_on_destroy = true
    }
    storage {
      # Storage sin acceso público: Terraform no intenta el plano de datos.
      data_plane_available = false
    }
  }
}
