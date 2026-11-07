variable "account_id" {
  description = "ID de la cuenta AWS verificada (12 dígitos). Evita aplicar en una cuenta equivocada."
  type        = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "account_id debe tener 12 dígitos."
  }
}

variable "region" {
  description = "Región permitida. us-east-1: catálogo completo de servicios y precio de S3 más bajo; latencia similar a us-east-2 desde Guatemala."
  type        = string
  default     = "us-east-1"
  validation {
    condition     = contains(["us-east-1", "us-east-2"], var.region)
    error_message = "Sólo se permiten us-east-1 o us-east-2."
  }
}

variable "prefix" {
  description = "Prefijo de nombres."
  type        = string
  default     = "uvcg-sgsi-lab"
}

variable "budget_email" {
  description = "Correo para las alertas del presupuesto de gasto cero (no se guarda en el repositorio: usar terraform.tfvars ignorado)."
  type        = string
}

variable "object_expiration_days" {
  description = "Días antes de expirar objetos del bucket (control de costo y retención de datos ficticios)."
  type        = number
  default     = 30
  validation {
    condition     = var.object_expiration_days >= 1 && var.object_expiration_days <= 90
    error_message = "Entre 1 y 90 días."
  }
}
