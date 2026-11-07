terraform {
  # 1.9+ por validaciones de variables; se valida con hashicorp/terraform:1.14 en contenedor.
  required_version = ">= 1.9.0"

  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      # Línea 4.x compatible con .terraform.lock.hcl (4.81.0). No se actualiza sin motivo.
      version = "~> 4.0"
    }
  }
}
