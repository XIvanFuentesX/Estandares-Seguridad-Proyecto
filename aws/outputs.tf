output "bucket_name" {
  value = module.storage.bucket_name
}

output "uploader_role_arn" {
  value = module.iam.uploader_role_arn
}

output "auditor_role_arn" {
  value = module.iam.auditor_role_arn
}

output "budget_name" {
  value = module.guardrails.budget_name
}
