variable "name" {
  description = "Base de nombres."
  type        = string
}

variable "storage_account_name" {
  description = "Nombre global de la cuenta (3-24, minúsculas y dígitos)."
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

variable "enable_storage" {
  description = "Crea la cuenta de almacenamiento privada (cobro por GB y operaciones)."
  type        = bool
}

variable "replication_type" {
  description = "LRS, ZRS, GRS o RAGRS."
  type        = string
}

variable "blob_soft_delete_days" {
  description = "Retención de borrado suave de blobs y contenedores."
  type        = number
}

variable "cool_after_days" {
  description = "Días sin modificación antes de mover a nivel Cool."
  type        = number
}

variable "delete_after_days" {
  description = "Días antes de eliminar blobs del contenedor de intercambio (datos ficticios)."
  type        = number
}

variable "enable_private_endpoints" {
  description = "Crea endpoint privado para blob."
  type        = bool
}

variable "private_endpoint_subnet_id" {
  description = "Subred de endpoints privados."
  type        = string
}

variable "private_dns_zone_blob_id" {
  description = "Zona privatelink.blob.core.windows.net."
  type        = string
  default     = null
}

variable "enable_diagnostics" {
  description = "Envía registros del servicio blob a Log Analytics."
  type        = bool
}

variable "log_analytics_workspace_id" {
  description = "Workspace de Log Analytics."
  type        = string
  default     = null
}
