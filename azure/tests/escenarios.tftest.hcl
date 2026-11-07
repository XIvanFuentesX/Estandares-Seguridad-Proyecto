# Pruebas de configuración SIN CREDENCIALES: el proveedor azurerm se sustituye por un mock.
# Ejecutan `plan` lógico (expansión de módulos, count/for_each, validaciones y precondiciones),
# pero NO contactan Azure, NO validan cuotas, nombres globales ni permisos y NO equivalen a un
# `terraform plan` real contra una suscripción.
#
# Uso (desde azure/):
#   terraform test                                           # valores por defecto
#   terraform test -var-file=environments/dev.tfvars.example
#   terraform test -var-file=environments/demo.tfvars.example
#   terraform test -var-file=environments/inst.tfvars.example

mock_provider "azurerm" {
  mock_data "azurerm_client_config" {
    defaults = {
      tenant_id       = "00000000-0000-0000-0000-000000000001"
      subscription_id = "00000000-0000-0000-0000-000000000002"
      object_id       = "00000000-0000-0000-0000-000000000003"
      client_id       = "00000000-0000-0000-0000-000000000004"
    }
  }
  mock_data "azurerm_subscription" {
    defaults = {
      id              = "/subscriptions/00000000-0000-0000-0000-000000000002"
      subscription_id = "00000000-0000-0000-0000-000000000002"
      tenant_id       = "00000000-0000-0000-0000-000000000001"
    }
  }
  mock_resource "azurerm_resource_group" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000002/resourceGroups/rg-simulado"
    }
  }
}

run "plan_simulado" {
  command = plan

  # --- Red: hub-and-spoke y segmentación (siempre presentes, sin costo por hora)
  assert {
    condition     = length(module.networking.spoke_subnet_ids) == 6
    error_message = "El spoke debe tener 6 subredes (dmz, apps, datos, gestion, seguridad, privateendpoints)."
  }
  assert {
    condition     = length(module.networking.nsg_ids) == 6
    error_message = "Cada zona del spoke debe tener su NSG."
  }
  assert {
    condition     = alltrue([for k, v in module.networking.deny_rule_priorities : v == "Deny:4096"])
    error_message = "Cada NSG debe terminar con denegación explícita (prioridad 4096)."
  }
  assert {
    condition     = length(module.networking.route_table_ids) == (var.enable_firewall ? 6 : 0)
    error_message = "Las UDR hacia el firewall sólo existen cuando el firewall está habilitado."
  }
  assert {
    condition     = module.networking.private_dns_zone_count == (var.enable_private_endpoints ? 2 : 0)
    error_message = "Zonas DNS privadas (blob y vault) sólo con endpoints privados."
  }

  # --- Región restringida y etiquetas obligatorias
  assert {
    condition     = contains(["eastus2", "southcentralus"], azurerm_resource_group.lab.location)
    error_message = "Región fuera de la lista permitida."
  }
  assert {
    condition     = alltrue([for t in local.required_tag_names : contains(keys(azurerm_resource_group.lab.tags), t)])
    error_message = "Faltan etiquetas obligatorias."
  }

  # --- Coherencia de banderas de costo
  assert {
    condition     = module.hybrid_connectivity.resource_counts.vpn_gateway == (var.enable_vpn_gateway ? 1 : 0)
    error_message = "VPN Gateway no coincide con enable_vpn_gateway."
  }
  assert {
    condition     = module.security.resource_counts.firewall == (var.enable_firewall ? 1 : 0)
    error_message = "Azure Firewall no coincide con enable_firewall."
  }
  assert {
    condition     = module.security.resource_counts.bastion == (var.enable_bastion ? 1 : 0)
    error_message = "Bastion no coincide con enable_bastion."
  }
  assert {
    condition     = module.security.resource_counts.app_gateway == (var.enable_app_gateway ? 1 : 0)
    error_message = "App Gateway no coincide con enable_app_gateway."
  }
  assert {
    condition     = module.security.resource_counts.key_vault == (var.enable_key_vault ? 1 : 0)
    error_message = "Key Vault no coincide con enable_key_vault."
  }
  assert {
    condition     = module.storage.resource_counts.storage_account == (var.enable_storage ? 1 : 0)
    error_message = "Storage no coincide con enable_storage."
  }
  assert {
    condition     = module.monitoring.resource_counts.log_analytics == (var.enable_monitoring ? 1 : 0)
    error_message = "Log Analytics no coincide con enable_monitoring."
  }
  assert {
    condition     = module.monitoring.resource_counts.sentinel == (var.enable_monitoring && var.enable_sentinel ? 1 : 0)
    error_message = "Sentinel no coincide con enable_sentinel."
  }
  assert {
    condition     = module.backup.resource_counts.recovery_vault == (var.enable_backup ? 1 : 0)
    error_message = "Recovery Services Vault no coincide con enable_backup."
  }

  # --- Endurecimiento de Key Vault y Storage cuando existen
  assert {
    condition     = alltrue([for kv in module.security.key_vault_hardening : kv.rbac && !kv.acceso_publico && kv.purge])
    error_message = "Key Vault debe usar RBAC, sin acceso público y con purge protection."
  }
  assert {
    condition = alltrue([for st in module.storage.hardening :
    !st.acceso_publico && !st.blobs_publicos && !st.clave_compartida && st.tls == "TLS1_2" && st.versionado])
    error_message = "Storage debe ser privado, sin acceso anónimo ni claves compartidas, TLS 1.2 y con versionado."
  }

  # --- Gobierno sin costo
  assert {
    condition     = module.policies.policy_assignment_count == (var.enable_policies ? 15 : 0)
    error_message = "Se esperaban 10 políticas fijas + 5 de etiquetas."
  }
  assert {
    condition     = module.monitoring.resource_counts.budget == (var.enable_budget ? 1 : 0)
    error_message = "Presupuesto no coincide con enable_budget."
  }
}

# Los valores por defecto no deben crear NINGÚN recurso con cargo por hora o por GB.
run "valores_por_defecto_sin_costo" {
  command = plan

  variables {
    environment              = "dev"
    enable_monitoring        = false
    enable_sentinel          = false
    enable_alerts            = false
    enable_key_vault         = false
    enable_storage           = false
    enable_private_endpoints = false
    enable_backup            = false
    enable_vpn_gateway       = false
    enable_firewall          = false
    enable_bastion           = false
    enable_app_gateway       = false
    defender_plans           = { VirtualMachines = "Free", StorageAccounts = "Free", KeyVaults = "Free", Arm = "Free" }
  }

  assert {
    condition = alltrue([
      module.security.resource_counts.firewall == 0,
      module.security.resource_counts.bastion == 0,
      module.security.resource_counts.app_gateway == 0,
      module.security.resource_counts.public_ips == 0,
      module.security.resource_counts.key_vault == 0,
      module.hybrid_connectivity.resource_counts.vpn_gateway == 0,
      module.hybrid_connectivity.resource_counts.public_ip == 0,
      module.storage.resource_counts.storage_account == 0,
      module.monitoring.resource_counts.log_analytics == 0,
      module.backup.resource_counts.recovery_vault == 0,
      module.networking.private_dns_zone_count == 0,
    ])
    error_message = "Con los valores por defecto no debe existir ningún recurso con costo."
  }
}

# Región no aprobada: la validación debe rechazarla.
run "region_no_permitida" {
  command = plan

  variables {
    location = "westeurope"
  }

  expect_failures = [var.location]
}

# Separación de funciones: el mismo grupo no puede ser admin. de seguridad y operador de respaldo.
run "separacion_de_funciones" {
  command = plan

  variables {
    principals = {
      administradores_seg = ["11111111-1111-1111-1111-111111111111"]
      operadores_respaldo = ["11111111-1111-1111-1111-111111111111"]
    }
  }

  expect_failures = [var.principals]
}

# Roles privilegiados prohibidos en asignaciones adicionales.
run "rol_privilegiado_rechazado" {
  command = plan

  variables {
    additional_role_assignments = {
      x = { principal_id = "22222222-2222-2222-2222-222222222222", role_definition_name = "Owner" }
    }
  }

  expect_failures = [var.additional_role_assignments]
}
