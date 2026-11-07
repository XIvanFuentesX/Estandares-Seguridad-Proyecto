# Presupuesto de gasto cero: monitoreo y notificación sin costo (Budgets sin acciones).
# include_credit = false para alertar ante CUALQUIER uso, aunque lo cubran los créditos del plan Free.
# Un presupuesto NO bloquea el gasto: la garantía de cero cargos proviene del plan Free.
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

variable "prefix" { type = string }
variable "budget_email" { type = string }

resource "aws_budgets_budget" "zero_spend" {
  name         = "${var.prefix}-gasto-cero"
  budget_type  = "COST"
  limit_amount = "0.01"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_types {
    include_credit = false
    include_refund = false
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_email]
  }
}

output "budget_name" { value = aws_budgets_budget.zero_spend.name }
