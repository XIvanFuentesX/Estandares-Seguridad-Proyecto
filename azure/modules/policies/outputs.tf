output "policy_assignment_ids" {
  description = "IDs de las asignaciones de política."
  value       = { for k, a in azurerm_resource_group_policy_assignment.this : k => a.id }
}

output "policy_assignment_count" {
  description = "Número de asignaciones."
  value       = length(azurerm_resource_group_policy_assignment.this)
}
