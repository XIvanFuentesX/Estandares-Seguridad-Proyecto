# Riesgos cloud (RC-) — componentes Azure del SGSI UVCG

Escala 1–5 (probabilidad × impacto), coherente con `governance/matriz-riesgos.csv`. Valoraciones de escritorio, pendientes
de validación con responsables. Relación con riesgos existentes: R-011, R-014, R-016, R-017, R-018.

| ID | Amenaza / escenario | Activo | P | I | Inherente | Controles en el código | P res. | I res. | Residual | Tratamiento | Responsable |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---|---|
| RC-01 | Gasto no controlado al habilitar un recurso costoso o dejarlo encendido (el presupuesto no bloquea) | Presupuesto del proyecto | 4 | 4 | 16 | Banderas `false`, prueba sin costo, presupuesto 50/80/100 %, `revisar_plan.py`, desactivación segura | 2 | 3 | 6 | Mitigar | Responsable SGSI + Finanzas |
| RC-02 | Exposición pública por error de configuración (red pública en PaaS, NSG abierto) | KV, Storage, servicios | 3 | 5 | 15 | PE, `public_network_access_enabled = false`, Deny 4096, políticas Deny, Trivy | 1 | 5 | 5 | Mitigar | Cloud/DevSecOps |
| RC-03 | Compromiso de cuenta administrativa de Azure | Plano de control | 3 | 5 | 15 | MFA (Security defaults), alertas RBAC, sin roles privilegiados en código | 2 | 5 | 10 | Mitigar; requiere P1/P2 para CA/PIM | Responsable IAM |
| RC-04 | Privilegios excesivos o sin separación de funciones | Suscripción | 3 | 4 | 12 | Roles mínimos por alcance, validación SoD, alerta de cambios RBAC | 2 | 3 | 6 | Mitigar | Responsable IAM |
| RC-05 | Exposición o pérdida del estado de Terraform (contiene IDs y la PSK) | Estado IaC | 3 | 4 | 12 | Backend Entra ID sin claves, `.gitignore`, sin estado local | 2 | 4 | 8 | Mitigar | Operador de plataforma |
| RC-06 | Fuga de PSK o túnel IPsec débil | Canal híbrido | 2 | 4 | 8 | Política IPsec explícita, PSK sólo por variable de entorno | 1 | 4 | 4 | Mitigar (migrar a certificados) | Redes |
| RC-07 | Vault de respaldo con red pública para MARS | Copias en Azure | 3 | 3 | 9 | Datos cifrados AES-256 en origen, inmutabilidad, alertas | 2 | 3 | 6 | Aceptar en demo; VPN+PE en institucional | Continuidad |
| RC-08 | Pérdida de visibilidad por tope diario de ingesta o retención mínima | Registros | 3 | 3 | 9 | Retención ≥ 30 d, alerta de fallos, SIEM local paralelo | 2 | 3 | 6 | Aceptar (costo) / ajustar tope | Analista de seguridad |
| RC-09 | Indisponibilidad regional o del enlace único (LRS, un ISP) | Respaldos y canal | 2 | 4 | 8 | Copias locales + nube; GRS en institucional | 2 | 3 | 6 | Mitigar parcialmente | Continuidad |
| RC-10 | Deriva de configuración por cambios manuales en el portal | Toda la infraestructura | 3 | 3 | 9 | IaC, políticas, alertas de cambios, `plan` periódico | 2 | 2 | 4 | Mitigar | DevSecOps |
| RC-11 | Residencia de datos fuera de Guatemala / requisitos legales | Información personal | 2 | 5 | 10 | Sólo datos ficticios; región restringida; política de ubicaciones | 1 | 5 | 5 | Evitar datos reales | Responsable legal/SGSI |
| RC-12 | Bloqueo operativo por purge protection/inmutabilidad (nombres retenidos, costos de retención) | KV, vault | 3 | 2 | 6 | Inmutabilidad *Unlocked*, sufijo único, documentación | 2 | 2 | 4 | Aceptar | Operador |
| RC-13 | Cambio de precios o retiro de SKU (p. ej. SKU de VPN no-AZ, Bastion Developer) | Presupuesto/diseño | 3 | 2 | 6 | Precios con fecha, script de consulta reproducible, SKU AZ | 2 | 2 | 4 | Aceptar con revisión mensual | Finanzas |
| RC-14 | Exposición de servicios Docker al implementar la conectividad híbrida | Laboratorio local | 2 | 5 | 10 | Arc saliente, VPN sólo hacia PE, NSG sin entrada desde on-prem a apps/datos | 1 | 5 | 5 | Evitar (no abrir puertos) | Redes + Seguridad |
| RC-15 | Licencias insuficientes (Entra ID P1/P2, Intune) impiden Acceso Condicional/PIM/MDM | Identidades administrativas | 4 | 3 | 12 | Security defaults, MFA de Keycloak, revisión manual de roles | 3 | 3 | 9 | Aceptar temporalmente / transferir (licenciamiento) | Dirección TI |
| RC-16 | Cambio de planes de Defender a nivel de suscripción afecta otras cargas | Suscripción compartida | 2 | 3 | 6 | `manage_defender_plans` desactivable; suscripción dedicada | 1 | 3 | 3 | Mitigar | Seguridad |
