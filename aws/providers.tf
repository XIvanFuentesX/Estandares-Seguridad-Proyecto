# Las credenciales NUNCA se definen aquí: se usan credenciales temporales de `aws login`
# exportadas como variables de entorno (AWS_ACCESS_KEY_ID/SECRET/SESSION_TOKEN) por scripts/desplegar.ps1.
provider "aws" {
  region              = var.region
  allowed_account_ids = [var.account_id]

  default_tags {
    tags = local.tags
  }
}
