variable "name" {
  description = "Base de nombres (prefijo-ambiente-región) calculada en el módulo raíz."
  type        = string
}

variable "location" {
  description = "Región de Azure ya validada en el módulo raíz."
  type        = string
}

variable "resource_group_name" {
  description = "Grupo de recursos donde se crean las redes."
  type        = string
}

variable "tags" {
  description = "Etiquetas obligatorias del SGSI."
  type        = map(string)
}

variable "hub_address_space" {
  description = "Espacio de direcciones del hub (gestión, inspección y conectividad híbrida)."
  type        = string
}

variable "spoke_address_space" {
  description = "Espacio de direcciones del spoke de cargas académicas."
  type        = string
}

variable "hub_subnets" {
  description = "Subredes del hub. Las claves firewall, firewall_mgmt, bastion y gateway usan los nombres reservados por Azure."
  type        = map(string)
}

variable "spoke_subnets" {
  description = "Subredes del spoke por zona de seguridad (dmz, apps, datos, gestion, seguridad, privateendpoints)."
  type        = map(string)
}

variable "onprem_address_spaces" {
  description = "Prefijos de la red local (laboratorio) que podrían llegar por VPN S2S."
  type        = list(string)
}

variable "enable_vpn_gateway" {
  description = "Indica si existe gateway VPN para tránsito por peering."
  type        = bool
}

variable "vpn_gateway_id" {
  description = "ID del gateway VPN (crea la dependencia para use_remote_gateways)."
  type        = string
  default     = null
}

variable "enable_firewall" {
  description = "Si es true se crean UDR que envían el tráfico entre zonas, on-premises e Internet al Azure Firewall."
  type        = bool
}

variable "firewall_private_ip" {
  description = "IP privada del Azure Firewall (salida del módulo security)."
  type        = string
  default     = null
}

variable "enable_app_gateway" {
  description = "Abre en la DMZ sólo lo que Application Gateway v2 necesita (443 desde Internet, GatewayManager y AzureLoadBalancer)."
  type        = bool
}

variable "enable_bastion_access" {
  description = "Permite SSH/RDP hacia la subred de gestión sólo desde AzureBastionSubnet (SKU Basic/Standard)."
  type        = bool
}

variable "enable_private_dns" {
  description = "Crea zonas DNS privadas para blob y Key Vault vinculadas al hub y al spoke."
  type        = bool
}

variable "enable_diagnostics" {
  description = "Envía los registros de los NSG a Log Analytics."
  type        = bool
}

variable "log_analytics_workspace_id" {
  description = "Workspace de Log Analytics para diagnósticos."
  type        = string
  default     = null
}
