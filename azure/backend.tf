# Backend remoto DOCUMENTADO Y COMENTADO. Mientras no exista suscripción autorizada sólo se usa
# `terraform init -backend=false` y no se genera estado. El estado NUNCA se versiona (.gitignore).
#
# Requisitos previos (crear fuera de este código, una sola vez, con aprobación):
#   - Grupo de recursos rg-uvcg-sgsi-tfstate y cuenta de almacenamiento StorageV2 con:
#     shared_access_key_enabled = false, min_tls_version = TLS1_2, versionado + borrado suave,
#     cifrado de infraestructura, acceso de red restringido (IP del operador o endpoint privado)
#     y bloqueo CanNotDelete.
#   - Rol "Storage Blob Data Contributor" sólo sobre el contenedor "tfstate" para quien ejecute Terraform.
#   - El estado contiene datos sensibles (p. ej. la clave IPsec si se crea la conexión S2S):
#     sólo lectura para el equipo de plataforma, auditoría en Log Analytics.
#
# Para activarlo: descomente el bloque y ejecute
#   terraform init -backend-config=environments/backend-<ambiente>.hcl
#
# terraform {
#   backend "azurerm" {
#     resource_group_name  = "rg-uvcg-sgsi-tfstate"
#     storage_account_name = "REEMPLAZAR"          # p. ej. stuvcgtfstate01
#     container_name       = "tfstate"
#     key                  = "sgsi-uvcg/dev.tfstate" # una clave por ambiente
#     use_azuread_auth     = true                    # sin claves de acceso ni SAS
#   }
# }
