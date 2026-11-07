# Plan de pruebas post-despliegue (Azure) — con plantillas VACÍAS

Ninguna de estas pruebas se ha ejecutado: requieren recursos desplegados. Las plantillas deben llenarse con evidencia real
(salida de comandos, consultas KQL, capturas propias); **no** se aceptan capturas simuladas.

## 1. Catálogo de pruebas

| ID | Área | Prueba | Procedimiento | Resultado esperado | Escenario |
|---|---|---|---|---|---|
| PT-AZ-01 | Conectividad | Peering hub-spoke | `az network vnet peering list` en ambas VNets | `Connected`/`FullyInSync` | 1-3 |
| PT-AZ-02 | Conectividad | Túnel S2S | `az network vpn-connection show` + `ping`/`Test-NetConnection` desde 192.168.50.0/24 hacia 10.21.60.x:443 | `Connected`; 443 abierto sólo hacia PE | 2-3 |
| PT-AZ-03 | Segmentación | Flujo permitido dmz→apps:443, apps→datos:5432 | Network Watcher *IP flow verify* | `Allow` por regla nombrada | 1-3 |
| PT-AZ-04 | Segmentación | Flujos denegados (dmz→datos, gestion→datos, onprem→apps) | *IP flow verify* | `Deny` por `denegar-resto-entrante` | 1-3 |
| PT-AZ-05 | Segmentación | Salida a Internet desde datos/privateendpoints | *IP flow verify* destino 8.8.8.8:443 | `Deny` por `denegar-internet-salida` | 1-3 |
| PT-AZ-06 | Firewall | UDR efectiva | `az network nic show-effective-route-table` | Próximo salto = IP privada del firewall | 3 |
| PT-AZ-07 | DNS privado | Resolución de PaaS | `nslookup <cuenta>.blob.core.windows.net` desde la red privada | IP 10.21.60.x | 1-3 |
| PT-AZ-08 | Acceso público denegado | Storage/KV desde Internet | `curl -I https://<cuenta>.blob.core.windows.net/` ; `az keyvault secret list` desde fuera | 403 / `ForbiddenByConnection` | 1-3 |
| PT-AZ-09 | Storage | Acceso anónimo y claves compartidas | `az storage blob list --auth-mode key` | Error `KeyBasedAuthenticationNotPermitted` | 1-3 |
| PT-AZ-10 | Storage | TLS mínimo | `openssl s_client -tls1_1` contra el endpoint privado | Handshake rechazado | 1-3 |
| PT-AZ-11 | RBAC | Identidad de intercambio limitada | Escribir en `intercambio-hibrido` (OK) y en `evidencias-sgsi` (403) | 201 / 403 | 1-3 |
| PT-AZ-12 | RBAC | Separación de funciones | Usuario del grupo *operadores_respaldo* intenta editar NSG | `AuthorizationFailed` | 1-3 |
| PT-AZ-13 | MFA | Inicio de sesión administrativo | Iniciar sesión en el portal con cuenta del grupo de seguridad | MFA exigido (Security defaults o Acceso Condicional si hay P1) | 1-3 |
| PT-AZ-14 | Puertos | Superficie pública | `az network public-ip list`; escaneo externo autorizado | Sólo IPs de gateway/firewall/App GW/Bastion habilitados | 1-3 |
| PT-AZ-15 | Políticas | Región no permitida | Crear recurso en `westeurope` | `RequestDisallowedByPolicy` | 1-3 |
| PT-AZ-16 | Políticas | NIC con IP pública / recurso sin etiqueta | Crear NIC con IP pública; crear recurso sin `propietario` | Denegado por política | 1-3 |
| PT-AZ-17 | Registro | Actividad y diagnósticos | KQL `AzureActivity \| take 10`; `AzureDiagnostics \| summarize count() by ResourceType` | Datos de cada recurso con diagnóstico | 1-3 |
| PT-AZ-18 | Alertas | Alerta de cambio RBAC | Crear y borrar una asignación de prueba (Reader) | Correo del grupo de acciones en < 15 min | 1-3 |
| PT-AZ-19 | Alertas | Presupuesto | Revisar *Cost Management > Budgets* | Umbrales 50/80/100 % configurados (no bloquean) | 1-3 |
| PT-AZ-20 | Respaldo | Subida y verificación de copia cifrada ficticia | Subir `.dump.enc` + `.sha256`, descargar, comparar hash | Hash idéntico | 1-3 |
| PT-AZ-21 | Recuperación | Versión previa / borrado suave | Sobrescribir y borrar blob de prueba; restaurar versión | Blob recuperado | 1-3 |
| PT-AZ-22 | Recuperación | Restauración desde vault (MARS) | Restaurar archivo de prueba al host aislado | Restauración exitosa; tiempo medido vs. RTO | 2-3 |
| PT-AZ-23 | Key Vault | Purga bloqueada | `az keyvault delete` + `az keyvault purge` | Purga rechazada (purge protection) | 1-3 |
| PT-AZ-24 | Costo | Costo real vs. estimado | *Cost Management* por grupo de recursos, 7 días | Desviación documentada vs. `costos-escenarios-20261024.md` | 1-3 |
| PT-AZ-25 | Arc | Incorporación del host | `azcmagent show`; recurso `Microsoft.HybridCompute/machines` | Estado `Connected`; sin puertos entrantes | 2 |

## 2. Plantilla de evidencia (copiar una por prueba)

```
ID de prueba:
Fecha/hora (UTC):
Ejecutor:                     Revisor:
Suscripción/RG (sin IDs sensibles):
Commit/versión de Terraform aplicada:
Precondiciones verificadas:
Comando o procedimiento exacto:
Salida obtenida (adjuntar archivo):
Resultado esperado:
Resultado obtenido:           [ ] Cumple  [ ] No cumple  [ ] No ejecutable
Desviación / hallazgo:
Riesgo asociado (RC-/R-):
Acción correctiva:
Archivo de evidencia:
```

## 3. Registro de ejecución (vacío)

| ID | Fecha | Ejecutor | Resultado | Evidencia | Observaciones |
|---|---|---|---|---|---|
| PT-AZ-01 | | | | | |
| PT-AZ-02 | | | | | |
| PT-AZ-03 | | | | | |
| PT-AZ-04 | | | | | |
| PT-AZ-05 | | | | | |
| PT-AZ-06 | | | | | |
| PT-AZ-07 | | | | | |
| PT-AZ-08 | | | | | |
| PT-AZ-09 | | | | | |
| PT-AZ-10 | | | | | |
| PT-AZ-11 | | | | | |
| PT-AZ-12 | | | | | |
| PT-AZ-13 | | | | | |
| PT-AZ-14 | | | | | |
| PT-AZ-15 | | | | | |
| PT-AZ-16 | | | | | |
| PT-AZ-17 | | | | | |
| PT-AZ-18 | | | | | |
| PT-AZ-19 | | | | | |
| PT-AZ-20 | | | | | |
| PT-AZ-21 | | | | | |
| PT-AZ-22 | | | | | |
| PT-AZ-23 | | | | | |
| PT-AZ-24 | | | | | |
| PT-AZ-25 | | | | | |
