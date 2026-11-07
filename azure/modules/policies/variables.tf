variable "name" {
  description = "Base de nombres."
  type        = string
}

variable "resource_group_id" {
  description = "Alcance de las asignaciones (grupo de recursos del laboratorio)."
  type        = string
}

variable "enable_policies" {
  description = "Asigna las definiciones integradas (sin costo)."
  type        = bool
}

variable "allowed_locations" {
  description = "Regiones permitidas."
  type        = list(string)
}

variable "required_tags" {
  description = "Etiquetas obligatorias en recursos."
  type        = list(string)
}

variable "effect" {
  description = "Efecto para controles de Storage y Key Vault (Audit o Deny)."
  type        = string
}
