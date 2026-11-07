# Despliegue MÍNIMO para el plan AWS Free: sólo S3 privado, IAM de mínimo privilegio y un presupuesto
# de gasto cero. Sin VPC, NAT, VPN, EC2, RDS, KMS CMK ni balanceadores (ver CIERRE_AWS.md).

module "storage" {
  source                 = "./modules/storage"
  bucket_name            = local.bucket_name
  object_expiration_days = var.object_expiration_days
  uploader_role_arn      = module.iam.uploader_role_arn
}

module "iam" {
  source     = "./modules/iam"
  prefix     = var.prefix
  account_id = var.account_id
  bucket_arn = "arn:aws:s3:::${local.bucket_name}"
}

module "guardrails" {
  source       = "./modules/guardrails"
  prefix       = var.prefix
  budget_email = var.budget_email
}
