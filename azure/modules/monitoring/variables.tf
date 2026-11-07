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
  description = "ID del grupo de recursos (alcance de alertas y presupuesto)."
  type        = string
}

variable "subscription_id" {
  description = "ID de recurso de la suscripción (/subscriptions/<guid>) para el registro de actividad."
  type        = string
}

variable "tags" {
  description = "Etiquetas obligatorias."
  type        = map(string)
}

variable "enable_monitoring" {
  description = "Crea Log Analytics, diagnóstico del registro de actividad y alertas de consulta (cobro por GB ingerido)."
  type        = bool
}

variable "log_retention_days" {
  description = "Retención interactiva en Log Analytics (mínimo 30)."
  type        = number
}

variable "log_daily_quota_gb" {
  description = "Límite diario de ingesta en GB (control de costo; -1 = sin límite)."
  type        = number
}

variable "enable_sentinel" {
  description = "Habilita Microsoft Sentinel sobre el workspace (cobro por GB analizado)."
  type        = bool
}

variable "enable_alerts" {
  description = "Crea grupo de acciones y alertas del registro de actividad."
  type        = bool
}

variable "alert_email_receivers" {
  description = "Mapa nombre => correo para el grupo de acciones."
  type        = map(string)
}

variable "enable_budget" {
  description = "Crea un presupuesto con alertas (no bloquea el gasto)."
  type        = bool
}

variable "budget_amount" {
  description = "Monto mensual del presupuesto en la moneda de facturación."
  type        = number
}

variable "budget_start_date" {
  description = "Inicio del presupuesto (primer día de un mes, RFC3339)."
  type        = string
}

variable "budget_thresholds" {
  description = "Umbrales en % del presupuesto real."
  type        = list(number)
}

variable "budget_contact_emails" {
  description = "Correos que reciben las notificaciones del presupuesto."
  type        = list(string)
}
