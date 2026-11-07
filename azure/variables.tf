# Variables del módulo raíz. TODO lo que tiene costo está en false por defecto.
# No coloque secretos en .tfvars: use variables de entorno TF_VAR_* desde un gestor de secretos.

# ================================================================ Contexto
variable "subscription_id" {
  description = "ID de suscripción. Preferible ARM_SUBSCRIPTION_ID; null usa la sesión de Azure CLI."
  type        = string
  default     = null
  sensitive   = true

  validation {
    condition     = var.subscription_id == null || can(regex("^[0-9a-fA-F-]{36}$", var.subscription_id))
    error_message = "subscription_id debe ser un GUID."
  }
}

variable "environment" {
  description = "Ambiente: dev (mínimo académico), demo (académico recomendado) o inst (institucional de referencia)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "demo", "inst"], var.environment)
    error_message = "environment debe ser dev, demo o inst."
  }
}

variable "location" {
  description = "Región de Azure. Restringida a regiones evaluadas por latencia desde Guatemala y precio."
  type        = string
  default     = "eastus2"

  validation {
    condition     = contains(["eastus2", "southcentralus"], var.location)
    error_message = "Región no permitida. Valores aprobados: eastus2 (recomendada) o southcentralus (alternativa)."
  }
}

variable "prefix" {
  description = "Prefijo corto de nombres (minúsculas, dígitos y guiones)."
  type        = string
  default     = "uvcg-sgsi"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,9}$", var.prefix))
    error_message = "prefix: 3-10 caracteres, inicia con letra, sólo minúsculas, dígitos y guiones."
  }
}

variable "unique_suffix" {
  description = "Sufijo para nombres globales (Storage, Key Vault)."
  type        = string
  default     = "lab01"

  validation {
    condition     = can(regex("^[a-z0-9]{2,5}$", var.unique_suffix))
    error_message = "unique_suffix: 2-5 caracteres en minúsculas o dígitos."
  }
}

variable "owner" {
  description = "Responsable del recurso (área, no persona)."
  type        = string
  default     = "seguridad-ti-uvcg"
}

variable "cost_center" {
  description = "Centro de costo académico."
  type        = string
  default     = "cc-sgsi-academico"
}

variable "data_classification" {
  description = "Clasificación de la información según la política del SGSI."
  type        = string
  default     = "ficticia-academica"

  validation {
    condition     = contains(["ficticia-academica", "publica", "interna", "confidencial"], var.data_classification)
    error_message = "Clasificación no reconocida por la política de clasificación del SGSI."
  }
}

variable "extra_tags" {
  description = "Etiquetas adicionales."
  type        = map(string)
  default     = {}
}

# ================================================================ Red
variable "hub_address_space" {
  description = "Espacio del hub."
  type        = string
  default     = "10.20.0.0/16"

  validation {
    condition     = can(cidrhost(var.hub_address_space, 0))
    error_message = "hub_address_space debe ser un CIDR válido."
  }
}

variable "spoke_address_space" {
  description = "Espacio del spoke académico."
  type        = string
  default     = "10.21.0.0/16"

  validation {
    condition     = can(cidrhost(var.spoke_address_space, 0))
    error_message = "spoke_address_space debe ser un CIDR válido."
  }
}

variable "onprem_address_spaces" {
  description = "Prefijos de la red del laboratorio local (ficticios) alcanzables por VPN. No deben solaparse con Azure."
  type        = list(string)
  default     = ["192.168.50.0/24"]

  validation {
    condition     = alltrue([for c in var.onprem_address_spaces : can(cidrhost(c, 0))])
    error_message = "onprem_address_spaces debe contener CIDR válidos."
  }
}

# ================================================================ Banderas de costo (false por defecto)
variable "enable_monitoring" {
  description = "Log Analytics + registro de actividad + diagnósticos (COSTO: GB ingeridos sobre la franja gratuita)."
  type        = bool
  default     = false
}

variable "enable_sentinel" {
  description = "Microsoft Sentinel (COSTO por GB analizado). Requiere enable_monitoring."
  type        = bool
  default     = false
}

variable "enable_alerts" {
  description = "Grupo de acciones y alertas del registro de actividad (alerta de consulta con costo si hay monitoring)."
  type        = bool
  default     = false
}

variable "enable_key_vault" {
  description = "Key Vault Standard (COSTO por operación)."
  type        = bool
  default     = false
}

variable "enable_storage" {
  description = "Cuenta de almacenamiento privada (COSTO por GB/operación)."
  type        = bool
  default     = false
}

variable "enable_private_endpoints" {
  description = "Endpoints privados + zonas DNS privadas (COSTO por hora y por zona)."
  type        = bool
  default     = false
}

variable "enable_backup" {
  description = "Recovery Services Vault (COSTO por instancia protegida y GB)."
  type        = bool
  default     = false
}

variable "enable_vpn_gateway" {
  description = "VPN Gateway S2S (COSTO por hora mientras exista)."
  type        = bool
  default     = false
}

variable "enable_firewall" {
  description = "Azure Firewall + UDR (COSTO alto por hora de despliegue)."
  type        = bool
  default     = false
}

variable "enable_bastion" {
  description = "Azure Bastion (COSTO por hora salvo Developer, no verificado)."
  type        = bool
  default     = false
}

variable "enable_app_gateway" {
  description = "Application Gateway WAF_v2 (COSTO fijo por hora + unidades de capacidad)."
  type        = bool
  default     = false
}

# ================================================================ Controles sin costo
variable "enable_policies" {
  description = "Asignaciones de Azure Policy (sin costo)."
  type        = bool
  default     = true
}

variable "policy_effect" {
  description = "Efecto de las políticas de Storage/Key Vault: Deny (por defecto) o Audit para una primera fase."
  type        = string
  default     = "Deny"

  validation {
    condition     = contains(["Audit", "Deny"], var.policy_effect)
    error_message = "policy_effect debe ser Audit o Deny."
  }
}

variable "enable_budget" {
  description = "Presupuesto con alertas (sin costo; NO bloquea el gasto)."
  type        = bool
  default     = true
}

variable "manage_defender_plans" {
  description = "Gestiona planes de Defender for Cloud a nivel de SUSCRIPCIÓN (afecta a toda la suscripción)."
  type        = bool
  default     = true
}

variable "defender_plans" {
  description = "Planes de Defender for Cloud. Free por defecto; Standard tiene costo."
  type        = map(string)
  default = {
    VirtualMachines = "Free"
    StorageAccounts = "Free"
    KeyVaults       = "Free"
    Arm             = "Free"
  }

  validation {
    condition     = alltrue([for t in values(var.defender_plans) : contains(["Free", "Standard"], t)])
    error_message = "Cada plan de Defender debe ser Free o Standard."
  }
}

# ================================================================ Parámetros de servicios
variable "log_retention_days" {
  description = "Retención en Log Analytics (mínimo 30; requisito del SGSI)."
  type        = number
  default     = 30

  validation {
    condition     = var.log_retention_days >= 30 && var.log_retention_days <= 730
    error_message = "log_retention_days debe estar entre 30 y 730."
  }
}

variable "log_daily_quota_gb" {
  description = "Tope diario de ingesta (GB). 0.16 GB/día ≈ 5 GB/mes. -1 = sin tope."
  type        = number
  default     = 0.16
}

variable "storage_replication_type" {
  description = "Replicación de Storage."
  type        = string
  default     = "LRS"

  validation {
    condition     = contains(["LRS", "ZRS", "GRS", "RAGRS"], var.storage_replication_type)
    error_message = "Use LRS, ZRS, GRS o RAGRS."
  }
}

variable "blob_soft_delete_days" {
  description = "Días de borrado suave de blobs y contenedores."
  type        = number
  default     = 14

  validation {
    condition     = var.blob_soft_delete_days >= 7 && var.blob_soft_delete_days <= 365
    error_message = "Entre 7 y 365 días."
  }
}

variable "backup_storage_mode" {
  description = "Redundancia del Recovery Services Vault."
  type        = string
  default     = "LocallyRedundant"

  validation {
    condition     = contains(["LocallyRedundant", "ZoneRedundant", "GeoRedundant"], var.backup_storage_mode)
    error_message = "Valor no válido."
  }
}

variable "backup_public_network_access" {
  description = "Permite acceso público al vault (necesario para MARS sin VPN). false por defecto."
  type        = bool
  default     = false
}

variable "backup_immutability" {
  description = "Inmutabilidad del vault: Disabled, Unlocked o Locked (irreversible)."
  type        = string
  default     = "Unlocked"

  validation {
    condition     = contains(["Disabled", "Unlocked", "Locked"], var.backup_immutability)
    error_message = "Valor no válido."
  }
}

variable "firewall_sku_tier" {
  description = "SKU de Azure Firewall."
  type        = string
  default     = "Basic"

  validation {
    condition     = contains(["Basic", "Standard"], var.firewall_sku_tier)
    error_message = "Use Basic o Standard (Premium fuera de alcance)."
  }
}

variable "allowed_egress_fqdns" {
  description = "FQDN de salida permitidos por el firewall."
  type        = list(string)
  default     = ["login.microsoftonline.com", "management.azure.com", "*.ubuntu.com"]
}

variable "bastion_sku" {
  description = "SKU de Bastion."
  type        = string
  default     = "Developer"

  validation {
    condition     = contains(["Developer", "Basic", "Standard"], var.bastion_sku)
    error_message = "Use Developer, Basic o Standard."
  }
}

variable "vpn_gateway_sku" {
  description = "SKU del VPN Gateway."
  type        = string
  default     = "VpnGw1AZ"

  validation {
    condition     = contains(["VpnGw1AZ", "VpnGw2AZ", "VpnGw1"], var.vpn_gateway_sku)
    error_message = "SKU no aprobado."
  }
}

variable "onprem_gateway_address" {
  description = "IP pública del dispositivo VPN local (dato de red, no secreto). null = no crear conexión."
  type        = string
  default     = null
}

variable "vpn_shared_key" {
  description = "PSK IPsec. SÓLO por TF_VAR_vpn_shared_key; nunca en archivos."
  type        = string
  default     = null
  sensitive   = true
}

variable "app_gateway_certificate_secret_id" {
  description = "ID del certificado TLS en Key Vault para Application Gateway."
  type        = string
  default     = null
}

variable "app_gateway_backend_addresses" {
  description = "IP privadas de backend en snet-apps."
  type        = list(string)
  default     = []
}

variable "security_contact_email" {
  description = "Buzón de seguridad para Defender for Cloud (no personal)."
  type        = string
  default     = null
}

variable "alert_email_receivers" {
  description = "Buzones del grupo de acciones (nombre => correo)."
  type        = map(string)
  default     = {}
}

variable "budget_amount" {
  description = "Presupuesto mensual (moneda de facturación, normalmente USD)."
  type        = number
  default     = 20

  validation {
    condition     = var.budget_amount > 0
    error_message = "budget_amount debe ser positivo."
  }
}

variable "budget_start_date" {
  description = "Primer día del mes de inicio (RFC3339)."
  type        = string
  default     = "2026-11-01T00:00:00Z"

  validation {
    condition     = can(regex("^\\d{4}-\\d{2}-01T00:00:00Z$", var.budget_start_date))
    error_message = "Debe ser el primer día de un mes, p. ej. 2026-11-01T00:00:00Z."
  }
}

variable "budget_thresholds" {
  description = "Umbrales (% real) de notificación."
  type        = list(number)
  default     = [50, 80, 100]
}

variable "budget_contact_emails" {
  description = "Correos de notificación del presupuesto."
  type        = list(string)
  default     = []
}

# ================================================================ Identidad y RBAC
variable "principals" {
  description = "Object IDs de GRUPOS de Entra ID por función. Vacío por defecto (sin identificadores reales en el repositorio)."
  type = object({
    lectores            = optional(list(string), [])
    auditores_registros = optional(list(string), [])
    operadores_red      = optional(list(string), [])
    operadores_respaldo = optional(list(string), [])
    administradores_seg = optional(list(string), [])
    lectores_costos     = optional(list(string), [])
  })
  default = {}

  validation {
    condition = (
      length(setintersection(toset(var.principals.administradores_seg), toset(var.principals.operadores_respaldo))) == 0 &&
      length(setintersection(toset(var.principals.administradores_seg), toset(var.principals.operadores_red))) == 0 &&
      length(setintersection(toset(var.principals.operadores_respaldo), toset(var.principals.operadores_red))) == 0
    )
    error_message = "Separación de funciones: un mismo grupo no puede ser administrador de seguridad, operador de respaldo y operador de red a la vez."
  }
}

variable "additional_role_assignments" {
  description = "Asignaciones adicionales en el grupo de recursos (sin roles privilegiados)."
  type = map(object({
    principal_id         = string
    role_definition_name = string
  }))
  default = {}

  validation {
    condition = alltrue([
      for a in values(var.additional_role_assignments) :
      !contains(["Owner", "Contributor", "User Access Administrator", "Role Based Access Control Administrator"], a.role_definition_name)
    ])
    error_message = "Roles privilegiados prohibidos aquí; use PIM con aprobación."
  }
}

variable "arc_onboarding_principal_id" {
  description = "Principal autorizado a incorporar el host local a Azure Arc."
  type        = string
  default     = null
}

variable "arc_machine_principal_id" {
  description = "Identidad del servidor Arc autorizada a escribir en el contenedor de intercambio."
  type        = string
  default     = null
}
