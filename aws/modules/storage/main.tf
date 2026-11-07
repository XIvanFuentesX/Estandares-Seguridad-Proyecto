# Bucket privado para intercambio cifrado de datos FICTICIOS con el laboratorio local.
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

variable "bucket_name" { type = string }
variable "object_expiration_days" { type = number }
variable "uploader_role_arn" { type = string }

resource "aws_s3_bucket" "lab" {
  bucket        = var.bucket_name
  force_destroy = false # la retirada vacía el bucket de forma explícita (scripts/retirar.ps1)
}

resource "aws_s3_bucket_public_access_block" "lab" {
  bucket                  = aws_s3_bucket.lab.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "lab" {
  bucket = aws_s3_bucket.lab.id
  rule {
    object_ownership = "BucketOwnerEnforced" # desactiva ACL
  }
}

# SSE-S3 (AES-256) sin costo adicional; una CMK de KMS cuesta por mes y se excluye.
resource "aws_s3_bucket_server_side_encryption_configuration" "lab" {
  bucket = aws_s3_bucket.lab.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "lab" {
  bucket = aws_s3_bucket.lab.id
  rule {
    id     = "expirar-datos-ficticios"
    status = "Enabled"
    filter {}
    expiration {
      days = var.object_expiration_days
    }
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

data "aws_iam_policy_document" "bucket" {
  statement {
    sid     = "DenegarTransporteNoCifrado"
    effect  = "Deny"
    actions = ["s3:*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    resources = [aws_s3_bucket.lab.arn, "${aws_s3_bucket.lab.arn}/*"]
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
  statement {
    sid     = "DenegarTLSAntiguo"
    effect  = "Deny"
    actions = ["s3:*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    resources = [aws_s3_bucket.lab.arn, "${aws_s3_bucket.lab.arn}/*"]
    condition {
      test     = "NumericLessThan"
      variable = "s3:TlsVersion"
      values   = ["1.2"]
    }
  }
  statement {
    sid     = "DenegarEscrituraFueraDelRolDeCarga"
    effect  = "Deny"
    actions = ["s3:PutObject"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    resources = ["${aws_s3_bucket.lab.arn}/*"]
    condition {
      test     = "ArnNotEquals"
      variable = "aws:PrincipalArn"
      values   = [var.uploader_role_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "lab" {
  bucket     = aws_s3_bucket.lab.id
  policy     = data.aws_iam_policy_document.bucket.json
  depends_on = [aws_s3_bucket_public_access_block.lab]
}

output "bucket_name" { value = aws_s3_bucket.lab.bucket }
output "bucket_arn" { value = aws_s3_bucket.lab.arn }
