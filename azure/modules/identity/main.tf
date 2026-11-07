# Módulo identity: identidades administradas y RBAC de mínimo privilegio con separación de funciones.
# - Ninguna asignación usa Owner, Contributor ni User Access Administrator (los roles privilegiados
#   se gestionan con PIM/aprobación fuera de este código).
# - Cada rol se limita al recurso más pequeño posible (contenedor, vault, workspace o grupo de recursos).

locals {
  # Rol por función y alcance. Las funciones de seguridad y respaldo no se solapan (validado en la raíz).
  sod_matrix = concat(
    [for p in var.principals.lectores : { key = "lector-${p}", principal = p, role = "Reader", scope = var.resource_group_id }],
    [for p in var.principals.operadores_red : { key = "red-${p}", principal = p, role = "Network Contributor", scope = var.resource_group_id }],
    [for p in var.principals.administradores_seg : { key = "seg-${p}", principal = p, role = "Security Admin", scope = var.resource_group_id }],
    [for p in var.principals.lectores_costos : { key = "costos-${p}", principal = p, role = "Cost Management Reader", scope = var.resource_group_id }],
    var.enable_key_vault ? [for p in var.principals.administradores_seg : { key = "kvadmin-${p}", principal = p, role = "Key Vault Administrator", scope = var.key_vault_id }] : [],
    var.enable_backup ? [for p in var.principals.operadores_respaldo : { key = "backup-${p}", principal = p, role = "Backup Operator", scope = var.recovery_vault_id }] : [],
    var.enable_monitoring ? [for p in var.principals.auditores_registros : { key = "logs-${p}", principal = p, role = "Log Analytics Reader", scope = var.log_analytics_workspace_id }] : [],
  )
}

resource "azurerm_user_assigned_identity" "app" {
  name                = "id-${var.name}-app"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_user_assigned_identity" "intercambio" {
  name                = "id-${var.name}-intercambio"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_user_assigned_identity" "app_gateway" {
  count               = var.enable_app_gateway_identity ? 1 : 0
  name                = "id-${var.name}-agw"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# ---------------------------------------------------------------- Identidades de carga de trabajo
resource "azurerm_role_assignment" "app_kv_secrets" {
  count                = var.enable_key_vault ? 1 : 0
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
  principal_type       = "ServicePrincipal"
  description          = "La aplicación sólo lee secretos; no los administra"
}

resource "azurerm_role_assignment" "app_evidencias_lectura" {
  count                = var.enable_storage ? 1 : 0
  scope                = var.storage_container_ids["evidencias"]
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
  principal_type       = "ServicePrincipal"
  description          = "Lectura de evidencias sin capacidad de escritura"
}

resource "azurerm_role_assignment" "intercambio_escritura" {
  count                = var.enable_storage ? 1 : 0
  scope                = var.storage_container_ids["intercambio_hibrido"]
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.intercambio.principal_id
  principal_type       = "ServicePrincipal"
  description          = "Escritura limitada al contenedor de intercambio de datos ficticios"
}

resource "azurerm_role_assignment" "arc_intercambio" {
  count                = var.enable_storage && var.arc_machine_principal_id != null ? 1 : 0
  scope                = var.storage_container_ids["intercambio_hibrido"]
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.arc_machine_principal_id
  principal_type       = "ServicePrincipal"
  description          = "Host local incorporado a Azure Arc: subida de respaldos cifrados de datos ficticios"
}

resource "azurerm_role_assignment" "app_gateway_kv" {
  count                = var.enable_app_gateway_identity && var.enable_key_vault ? 1 : 0
  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.app_gateway[0].principal_id
  principal_type       = "ServicePrincipal"
  description          = "Application Gateway lee su certificado TLS"
}

# ---------------------------------------------------------------- Personas (grupos de Entra ID)
resource "azurerm_role_assignment" "sod" {
  for_each             = { for a in local.sod_matrix : a.key => a }
  scope                = each.value.scope
  role_definition_name = each.value.role
  principal_id         = each.value.principal
  principal_type       = "Group"
  description          = "Separación de funciones SGSI UVCG"
}

resource "azurerm_role_assignment" "additional" {
  for_each             = var.additional_role_assignments
  scope                = var.resource_group_id
  role_definition_name = each.value.role_definition_name
  principal_id         = each.value.principal_id
}
