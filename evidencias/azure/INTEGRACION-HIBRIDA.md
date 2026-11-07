# Diseño de integración híbrida — laboratorio local ↔ Azure

Estado: **diseño preparado, no implementado** (no hay suscripción). Ningún servicio Docker del laboratorio se expone.

## 0. Aclaración

Un endpoint HTTPS en `https://127.0.0.1:8443` (Nginx del laboratorio) **no es conectividad híbrida**: sólo es accesible
desde el propio host y no establece canal, identidad ni registro con Azure. Tampoco lo sería abrir puertos del router
hacia Docker. La conectividad híbrida exige un canal autenticado y cifrado entre el entorno local y la nube, con identidad
autorizada y registro en ambos extremos.

## 1. Opciones evaluadas

| Criterio | A. VPN S2S (IPsec) | B. Azure Arc (agente saliente) | C. Intercambio por Storage con identidad |
|---|---|---|---|
| Recurso Terraform | `modules/hybrid-connectivity` (gateway, LNG, conexión) | Rol `Azure Connected Machine Onboarding`; incorporación con `azcmagent` | `modules/storage` + rol en contenedor `intercambio-hibrido` |
| Requisito local | Router/firewall con IPsec IKEv2 e IP pública fija | Host Windows con salida HTTPS 443 | Herramienta con Entra ID (az CLI/AzCopy) |
| Exposición entrante | Ninguna en Docker; el router acepta IPsec (UDP 500/4500) | **Ninguna** (sólo saliente) | Ninguna |
| Cifrado en tránsito | IKEv2 AES-256/SHA-256, DH14, PFS2048, GCM-AES-256 | TLS 1.2+ hacia Azure | TLS 1.2 (Storage exige mínimo 1.2) |
| Identidad | PSK (débil; mejor certificados) | Identidad administrada del servidor Arc | Identidad del servidor Arc o principal con RBAC por contenedor |
| Acceso a PaaS privado | Sí (DNS privado + PE vía túnel) | No por sí solo (Storage sin red pública) | Requiere A, o habilitar temporalmente red pública restringida por IP (no recomendado) |
| Costo (eastus2) | 0.21 USD/h gateway + 0.005 USD/h IP + 0.015 USD/h S2S | 0 USD/h plano de control (API); Defender P1 4.91 USD/mes opcional | Por GB y operaciones (céntimos) |
| Recomendación | Demostración puntual (40 h) | **Base permanente de bajo costo** | Sólo combinada con A o con Arc + Private Link Scope (no incluido) |

**Diseño recomendado (Escenario 2)**: Arc permanente para identidad, inventario, Defender y registro del host; VPN S2S sólo en
la ventana de demostración para mover respaldos **ya cifrados** de datos **ficticios** al contenedor privado por el
endpoint privado. Fuera de la ventana, el gateway se destruye (`enable_vpn_gateway = false`).

## 2. Cómo se demostraría cada propiedad sin exponer Docker

| Propiedad | Evidencia a capturar (cuando exista suscripción) | Origen |
|---|---|---|
| Cifrado en tránsito | `Get-AzVirtualNetworkGatewayConnection` con `IpsecPolicies` y estado `Connected`; métricas `TunnelIngressBytes`; para Arc/Storage, `minimumTlsVersion = TLS1_2` y prueba fallida con TLS 1.0 | Azure + router |
| Identidad autorizada | Asignación `Storage Blob Data Contributor` sólo en `intercambio-hibrido` a la identidad del servidor Arc; intento de escritura en `evidencias-sgsi` → 403 (`AuthorizationPermissionMismatch`) | Log Analytics `StorageBlobLogs` |
| Registro | `AzureActivity` (incorporación Arc, cambios RBAC), `StorageBlobLogs` (PutBlob con `AuthenticationType = OAuth`), diagnósticos del gateway (`TunnelDiagnosticLog`) | Log Analytics |
| Respaldo de datos ficticios | Subir el `.dump.enc` existente (AES-256) y su `.sha256`; descargar y comparar hash; restaurar en el laboratorio aislado | Scripts locales existentes (`scripts/backup_postgres.ps1`, `restaurar_prueba.ps1`) — sin modificarlos |
| Sin exposición | `Test-NetConnection` desde Internet a la IP pública del laboratorio: puertos 8443/8080/5432 cerrados; NSG `snet-apps`/`snet-datos` sin regla desde on-premises | Escaneo externo autorizado |

## 3. Flujo de intercambio (opción combinada A+B+C)

1. El host local (Arc) obtiene token de su identidad administrada (sin secretos en disco).
2. El respaldo ya cifrado con AES-256 (clave local, nunca enviada) y su hash SHA-256 se suben a `intercambio-hibrido`
   por `https://<cuenta>.blob.core.windows.net` resuelto por DNS privado a la IP del PE (sólo a través de la VPN).
3. Storage registra la operación (`StorageBlobLogs`) y aplica versionado/borrado suave; la regla de ciclo de vida elimina el blob a los 30 días.
4. La verificación descarga el blob, recalcula SHA-256 y restaura en el entorno aislado local.
5. El gateway VPN se elimina al terminar la ventana.

## 4. Parámetros del extremo local (no secretos)

- Prefijo local ficticio: `192.168.50.0/24` (variable `onprem_address_spaces`; no debe solaparse con 10.20/16 ni 10.21/16).
- IP pública del router: variable `onprem_gateway_address` (sin valor en el repositorio).
- PSK: **sólo** `TF_VAR_vpn_shared_key` desde un gestor de secretos; queda en el estado de Terraform → backend protegido (RC-05, RC-06).
- Política IPsec obligatoria en ambos extremos: IKEv2, AES256/SHA256, DHGroup14, GCMAES256, PFS2048, SA 27,000 s / 102,400,000 KB, DPD 45 s.

## 5. Limitaciones

- No se probó ningún túnel ni incorporación Arc (sin suscripción ni autorización de red).
- Arc + Storage privado sin VPN requiere *Azure Arc Private Link Scope* y endpoints adicionales (no incluidos; costo adicional no calculado).
- El agente MARS necesita acceso al vault: en `demo.tfvars.example` se habilita la red pública del vault (riesgo aceptado RC-07).
