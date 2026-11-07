variable "name" {
  description = "Base de nombres."
  type        = string
}

variable "location" {
  description = "Región."
  type        = string
}

variable "resource_group_name" {
  description = "Grupo de recursos."
  type        = string
}

variable "resource_group_id" {
  description = "Alcance de roles de lectura/operación."
  type        = string
}

variable "tags" {
  description = "Etiquetas obligatorias."
  type        = map(string)
}

variable "enable_app_gateway_identity" {
  description = "Crea la identidad que usa Application Gateway para leer su certificado."
  type        = bool
}

# Alcances (pueden ser null cuando el servicio está deshabilitado). Las banderas enable_* deciden el count.
variable "enable_key_vault" {
  description = "Key Vault habilitado."
  type        = bool
}

variable "key_vault_id" {
  description = "Alcance Key Vault."
  type        = string
  default     = null
}

variable "enable_storage" {
  description = "Storage habilitado."
  type        = bool
}

variable "storage_container_ids" {
  description = "IDs ARM de contenedores (evidencias, intercambio_hibrido)."
  type        = map(string)
  default     = {}
}

variable "enable_backup" {
  description = "Recovery Services Vault habilitado."
  type        = bool
}

variable "recovery_vault_id" {
  description = "Alcance del vault."
  type        = string
  default     = null
}

variable "enable_monitoring" {
  description = "Log Analytics habilitado."
  type        = bool
}

variable "log_analytics_workspace_id" {
  description = "Alcance del workspace."
  type        = string
  default     = null
}

variable "principals" {
  description = "Object IDs de grupos de Entra ID por función (separación de funciones)."
  type = object({
    lectores            = optional(list(string), [])
    auditores_registros = optional(list(string), [])
    operadores_red      = optional(list(string), [])
    operadores_respaldo = optional(list(string), [])
    administradores_seg = optional(list(string), [])
    lectores_costos     = optional(list(string), [])
  })
}

variable "arc_machine_principal_id" {
  description = "Identidad asignada por el sistema del servidor Arc (host local) autorizada a escribir en el contenedor de intercambio."
  type        = string
  default     = null
}

variable "additional_role_assignments" {
  description = "Asignaciones adicionales (roles privilegiados prohibidos; validado en el módulo raíz)."
  type = map(object({
    principal_id         = string
    role_definition_name = string
  }))
  default = {}
}
