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

variable "tags" {
  description = "Etiquetas obligatorias."
  type        = map(string)
}

variable "enable_backup" {
  description = "Crea Recovery Services Vault (cobro por instancia protegida y GB almacenado)."
  type        = bool
}

variable "storage_mode_type" {
  description = "LocallyRedundant, ZoneRedundant o GeoRedundant."
  type        = string
}

variable "public_network_access_enabled" {
  description = "El agente MARS sin VPN requiere acceso público al vault; por defecto deshabilitado."
  type        = bool
}

variable "immutability" {
  description = "Disabled, Unlocked o Locked (Locked es irreversible)."
  type        = string
}

variable "daily_retention_days" {
  description = "Retención diaria de la política de respaldo."
  type        = number
}

variable "weekly_retention_weeks" {
  description = "Retención semanal de la política de respaldo."
  type        = number
}

variable "timezone" {
  description = "Zona horaria de programación (Guatemala = Central America Standard Time)."
  type        = string
}

variable "enable_diagnostics" {
  description = "Envía registros del vault a Log Analytics."
  type        = bool
}

variable "log_analytics_workspace_id" {
  description = "Workspace de Log Analytics."
  type        = string
  default     = null
}
