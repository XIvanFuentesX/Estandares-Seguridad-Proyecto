# Roles de mínimo privilegio asumidos con credenciales temporales (sin usuarios IAM ni claves de acceso).
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

variable "prefix" { type = string }
variable "account_id" { type = string }
variable "bucket_arn" { type = string }

data "aws_iam_policy_document" "trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${var.account_id}:root"] # sólo identidades de esta cuenta con permiso sts:AssumeRole
    }
  }
}

resource "aws_iam_role" "uploader" {
  name                 = "${var.prefix}-uploader"
  description          = "Carga de archivos FICTICIOS cifrados desde el laboratorio local al prefijo laboratorio/."
  assume_role_policy   = data.aws_iam_policy_document.trust.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "uploader" {
  statement {
    sid       = "ListarSoloPrefijoLaboratorio"
    actions   = ["s3:ListBucket"]
    resources = [var.bucket_arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["laboratorio/*"]
    }
  }
  statement {
    sid       = "LeerEscribirPrefijoLaboratorio"
    actions   = ["s3:PutObject", "s3:GetObject"]
    resources = ["${var.bucket_arn}/laboratorio/*"]
  }
  statement {
    sid       = "SinBorradoNiCambioDePlan"
    effect    = "Deny"
    actions   = ["s3:DeleteObject", "s3:DeleteObjectVersion", "s3:PutBucketPolicy", "freetier:UpgradeAccountPlan"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "uploader" {
  name   = "minimo-privilegio-carga"
  role   = aws_iam_role.uploader.id
  policy = data.aws_iam_policy_document.uploader.json
}

resource "aws_iam_role" "auditor" {
  name                 = "${var.prefix}-auditor"
  description          = "Lectura de configuración y verificación de costos; sin acceso a objetos."
  assume_role_policy   = data.aws_iam_policy_document.trust.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "auditor" {
  statement {
    sid = "LeerConfiguracionDelBucket"
    actions = ["s3:GetBucketPolicy", "s3:GetBucketPublicAccessBlock", "s3:GetEncryptionConfiguration",
    "s3:GetLifecycleConfiguration", "s3:GetBucketOwnershipControls", "s3:GetBucketTagging", "s3:GetBucketLocation"]
    resources = [var.bucket_arn]
  }
  statement {
    sid       = "EstadoDelPlanYEventos"
    actions   = ["freetier:GetAccountPlanState", "freetier:GetFreeTierUsage", "cloudtrail:LookupEvents", "budgets:ViewBudget"]
    resources = ["*"]
  }
  statement {
    sid       = "SinAccesoAObjetosNiCambioDePlan"
    effect    = "Deny"
    actions   = ["s3:GetObject", "s3:PutObject", "freetier:UpgradeAccountPlan"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "auditor" {
  name   = "solo-lectura-auditoria"
  role   = aws_iam_role.auditor.id
  policy = data.aws_iam_policy_document.auditor.json
}

output "uploader_role_arn" { value = aws_iam_role.uploader.arn }
output "auditor_role_arn" { value = aws_iam_role.auditor.arn }
