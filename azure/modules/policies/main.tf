# Módulo policies: asignaciones de definiciones INTEGRADAS de Azure Policy al grupo de recursos.
# Los GUID y nombres de parámetros se verificaron contra github.com/Azure/azure-policy
# (built-in-policies/policyDefinitions) el 2026-10-24; ver evidencias/azure/politicas-integradas-verificadas-20261024.txt.

locals {
  builtin = "/providers/Microsoft.Authorization/policyDefinitions"

  fixed_assignments = {
    ubicaciones = {
      id      = "e56962a6-4747-49cd-b67b-bf8b01975c4c" # Allowed locations
      display = "SGSI-UVCG: ubicaciones permitidas"
      params  = jsonencode({ listOfAllowedLocations = { value = var.allowed_locations } })
      message = "Sólo se permiten las regiones aprobadas para el laboratorio UVCG."
    }
    nic-sin-ip-publica = {
      id      = "83a86a26-fd1f-447c-b59d-e51f44264114" # Network interfaces should not have public IPs (Deny)
      display = "SGSI-UVCG: NIC sin IP pública"
      params  = null
      message = "Las interfaces de red no pueden tener IP pública; use Bastion, VPN o App Gateway."
    }
    st-transferencia-segura = {
      id      = "404c3081-a854-4457-ae30-26a93ef643f9" # Secure transfer to storage accounts should be enabled
      display = "SGSI-UVCG: Storage sólo HTTPS"
      params  = jsonencode({ effect = { value = var.effect } })
      message = "Las cuentas de almacenamiento deben exigir transferencia segura."
    }
    st-sin-acceso-anonimo = {
      id      = "4fa4b6c0-31ca-4c0d-b10d-24b96f62a751" # Storage account public access should be disallowed
      display = "SGSI-UVCG: Storage sin acceso anónimo"
      params  = jsonencode({ effect = { value = var.effect } })
      message = "No se permite acceso anónimo a blobs."
    }
    st-sin-clave-compartida = {
      id      = "8c6a50c6-9ffd-4ae7-986f-5fa6111f9a54" # Storage accounts should prevent shared key access
      display = "SGSI-UVCG: Storage sin claves compartidas"
      params  = jsonencode({ effect = { value = var.effect } })
      message = "Use Microsoft Entra ID y RBAC; las claves compartidas están prohibidas."
    }
    st-tls-minimo = {
      id      = "fe83a0eb-a853-422d-aac2-1bffd182c5d0" # Storage accounts should have the specified minimum TLS version
      display = "SGSI-UVCG: Storage TLS 1.2 mínimo"
      params  = jsonencode({ effect = { value = var.effect }, minimumTlsVersion = { value = "TLS1_2" } })
      message = "La versión mínima de TLS debe ser 1.2."
    }
    st-sin-red-publica = {
      id      = "b2982f36-99f2-4db5-8eff-283140c09693" # Storage accounts should disable public network access
      display = "SGSI-UVCG: Storage sin acceso de red público"
      params  = jsonencode({ effect = { value = var.effect } })
      message = "Acceso sólo por endpoint privado."
    }
    kv-proteccion-borrado = {
      id      = "0b60c0b2-2dc2-4e1c-b5c9-abbed971de53" # Key vaults should have deletion protection enabled
      display = "SGSI-UVCG: Key Vault con purge protection"
      params  = jsonencode({ effect = { value = var.effect } })
      message = "Key Vault debe tener protección contra purga."
    }
    kv-sin-red-publica = {
      id      = "405c5871-3e91-4644-8a63-58e19d68ff5b" # Azure Key Vault should disable public network access
      display = "SGSI-UVCG: Key Vault sin acceso público"
      params  = jsonencode({ effect = { value = var.effect } })
      message = "Key Vault sólo accesible por endpoint privado."
    }
    kv-rbac = {
      id      = "12d4fa5e-1f9f-4c21-97a9-b99b3c6611b5" # Azure Key Vault should use RBAC permission model
      display = "SGSI-UVCG: Key Vault con modelo RBAC"
      params  = jsonencode({ effect = { value = var.effect } })
      message = "Key Vault debe usar el modelo de permisos RBAC."
    }
  }

  tag_assignments = {
    for t in var.required_tags : "etiqueta-${t}" => {
      id      = "871b6d14-10aa-478d-b590-94f262ecfa99" # Require a tag on resources (Deny)
      display = "SGSI-UVCG: etiqueta obligatoria ${t}"
      params  = jsonencode({ tagName = { value = t } })
      message = "Todo recurso debe tener la etiqueta '${t}'."
    }
  }

  assignments = { for k, v in merge(local.fixed_assignments, local.tag_assignments) : k => v if var.enable_policies }
}

resource "azurerm_resource_group_policy_assignment" "this" {
  for_each             = local.assignments
  name                 = "pa-${each.key}"
  display_name         = each.value.display
  resource_group_id    = var.resource_group_id
  policy_definition_id = "${local.builtin}/${each.value.id}"
  parameters           = each.value.params
  enforce              = true
  description          = "Asignación del SGSI UVCG (${var.name}); definición integrada de Azure Policy."

  non_compliance_message {
    content = each.value.message
  }
}
