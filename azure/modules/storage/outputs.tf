output "storage_account_id" {
  description = "ID de la cuenta (null si está deshabilitada)."
  value       = try(azurerm_storage_account.this[0].id, null)
}

output "storage_account_name" {
  description = "Nombre de la cuenta."
  value       = try(azurerm_storage_account.this[0].name, null)
}

output "container_ids" {
  description = "IDs de recurso (ARM) de los contenedores, alcance mínimo para RBAC."
  value       = { for k, c in azurerm_storage_container.this : k => c.id }
}

output "hardening" {
  description = "Configuración de endurecimiento de la cuenta."
  value = [for st in azurerm_storage_account.this : {
    acceso_publico   = st.public_network_access_enabled
    blobs_publicos   = st.allow_nested_items_to_be_public
    clave_compartida = st.shared_access_key_enabled
    tls              = st.min_tls_version
    versionado       = st.blob_properties[0].versioning_enabled
  }]
}

output "resource_counts" {
  description = "Conteo de recursos con costo."
  value = {
    storage_account  = length(azurerm_storage_account.this)
    private_endpoint = length(azurerm_private_endpoint.blob)
  }
}
