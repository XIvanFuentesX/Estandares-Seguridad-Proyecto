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

variable "tenant_id" {
  description = "Tenant de Microsoft Entra ID para Key Vault."
  type        = string
}

# ---------------------------------------------------------------- Key Vault
variable "enable_key_vault" {
  description = "Crea Key Vault (cobro por operación)."
  type        = bool
}

variable "key_vault_name" {
  description = "Nombre global del Key Vault (3-24 caracteres)."
  type        = string
}

variable "key_vault_soft_delete_days" {
  description = "Días de retención de borrado suave (7-90)."
  type        = number
  default     = 90
}

variable "enable_private_endpoints" {
  description = "Crea endpoints privados (cobro por hora)."
  type        = bool
}

variable "private_endpoint_subnet_id" {
  description = "Subred de endpoints privados."
  type        = string
}

variable "private_dns_zone_vault_id" {
  description = "Zona DNS privada privatelink.vaultcore.azure.net."
  type        = string
  default     = null
}

# ---------------------------------------------------------------- Azure Firewall
variable "enable_firewall" {
  description = "Crea Azure Firewall (cobro por hora de despliegue)."
  type        = bool
}

variable "firewall_sku_tier" {
  description = "Basic o Standard."
  type        = string
}

variable "firewall_subnet_id" {
  description = "AzureFirewallSubnet."
  type        = string
}

variable "firewall_management_subnet_id" {
  description = "AzureFirewallManagementSubnet (requerida por el SKU Basic)."
  type        = string
}

variable "spoke_subnets" {
  description = "CIDR por zona del spoke para las reglas del firewall."
  type        = map(string)
}

variable "onprem_address_spaces" {
  description = "Prefijos locales autorizados a los endpoints privados."
  type        = list(string)
}

variable "allowed_egress_fqdns" {
  description = "FQDN de salida permitidos desde apps/gestión a través del firewall."
  type        = list(string)
}

# ---------------------------------------------------------------- Bastion
variable "enable_bastion" {
  description = "Crea Azure Bastion."
  type        = bool
}

variable "bastion_sku" {
  description = "Developer, Basic o Standard."
  type        = string
}

variable "bastion_subnet_id" {
  description = "AzureBastionSubnet."
  type        = string
}

variable "hub_vnet_id" {
  description = "VNet hub (requerida por el SKU Developer)."
  type        = string
}

# ---------------------------------------------------------------- Application Gateway + WAF
variable "enable_app_gateway" {
  description = "Crea Application Gateway WAF_v2 (cobro fijo por hora + unidades de capacidad)."
  type        = bool
}

variable "app_gateway_subnet_id" {
  description = "Subred DMZ dedicada a Application Gateway."
  type        = string
}

variable "app_gateway_identity_id" {
  description = "Identidad administrada asignada por el usuario para leer el certificado en Key Vault."
  type        = string
  default     = null
}

variable "app_gateway_certificate_secret_id" {
  description = "ID versionless del secreto/certificado TLS en Key Vault. No se almacena el certificado en el repositorio."
  type        = string
  default     = null
}

variable "app_gateway_backend_addresses" {
  description = "IP privadas del backend en la subred apps (nunca los servicios Docker locales)."
  type        = list(string)
  default     = []
}

variable "app_gateway_max_capacity" {
  description = "Máximo de instancias en autoescalado."
  type        = number
  default     = 2
}

# ---------------------------------------------------------------- Defender for Cloud
variable "manage_defender_plans" {
  description = "Gestiona los planes de Defender for Cloud a nivel de suscripción."
  type        = bool
}

variable "defender_plans" {
  description = "Mapa tipo de recurso => Free/Standard."
  type        = map(string)
}

variable "security_contact_email" {
  description = "Correo de contacto de seguridad (no es secreto; usar buzón institucional)."
  type        = string
  default     = null
}

# ---------------------------------------------------------------- Diagnósticos
variable "enable_diagnostics" {
  description = "Envía registros a Log Analytics."
  type        = bool
}

variable "log_analytics_workspace_id" {
  description = "Workspace de Log Analytics."
  type        = string
  default     = null
}
