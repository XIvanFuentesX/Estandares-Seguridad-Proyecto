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
  description = "Alcance de la asignación de incorporación de Azure Arc."
  type        = string
}

variable "tags" {
  description = "Etiquetas obligatorias."
  type        = map(string)
}

variable "enable_vpn_gateway" {
  description = "Crea VPN Gateway S2S (cobro por hora mientras exista; no se puede 'apagar', sólo eliminar)."
  type        = bool
}

variable "vpn_gateway_sku" {
  description = "SKU del gateway (VpnGw1AZ recomendado; los SKU no-AZ están en retiro para nuevas implementaciones)."
  type        = string
}

variable "gateway_subnet_id" {
  description = "GatewaySubnet del hub."
  type        = string
}

variable "onprem_gateway_address" {
  description = "IP pública del dispositivo VPN local (null = no crear conexión)."
  type        = string
  default     = null
}

variable "onprem_address_spaces" {
  description = "Prefijos de la red local."
  type        = list(string)
}

variable "vpn_shared_key" {
  description = "Clave precompartida IPsec. Pasar sólo por TF_VAR_vpn_shared_key desde un gestor de secretos; nunca en .tfvars."
  type        = string
  default     = null
  sensitive   = true
}

variable "arc_onboarding_principal_id" {
  description = "Objeto (principal de servicio o grupo) autorizado a incorporar servidores a Azure Arc en el grupo de recursos."
  type        = string
  default     = null
}

variable "enable_diagnostics" {
  description = "Envía registros del gateway a Log Analytics."
  type        = bool
}

variable "log_analytics_workspace_id" {
  description = "Workspace de Log Analytics."
  type        = string
  default     = null
}
