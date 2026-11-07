# Inventario de activos del SGSI UVCG

Generado: 2026-11-07T11:23:29-06:00. Supuestos académicos pendientes de validación y aprobación por responsables institucionales; no provienen de entrevistas ni de datos financieros reales.

Escala CIA: 1 insignificante, 2 baja, 3 moderada, 4 alta, 5 crítica. Criticidad del activo = máximo de C/I/A, ajustado por dependencia transversal.

Clasificación por estado real: **Implementado** = existe y se prueba en el laboratorio; **Planificado** = diseñado o requerido, sin despliegue; **Académico no implementado** = sólo forma parte del escenario universitario.

Resumen: Académico no implementado: 3; Implementado: 18; Planificado: 12.

| id | activo | tipo | propietario | custodio | ubicacion | informacion_procesada | confidencialidad_1_5 | integridad_1_5 | disponibilidad_1_5 | criticidad | dependencias | estado_real |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ACT-001 | Host Windows/Docker Desktop | Infraestructura | TI UVCG | Administrador del laboratorio | Local | Contenedores y volúmenes del SGSI | 3 | 5 | 5 | Crítica | Energía; hardware; Docker Desktop | Implementado |
| ACT-002 | Redes Docker segmentadas | Red | Seguridad TI | Administrador del laboratorio | Local | Flujos entre DMZ, aplicaciones, datos e identidad | 3 | 5 | 5 | Crítica | ACT-001; compose.yaml | Implementado |
| ACT-003 | API académica Flask/Gunicorn | Aplicación | Dirección Académica | TI Aplicaciones | Red apps | Cursos y decisiones RBAC | 4 | 5 | 4 | Alta | ACT-005; ACT-006; ACT-002 | Implementado |
| ACT-004 | Proxy Nginx/TLS | Aplicación perimetral | Seguridad TI | TI Infraestructura | DMZ Docker | Solicitudes HTTPS y logs de acceso | 3 | 5 | 5 | Crítica | ACT-003; ACT-013; ACT-002 | Implementado |
| ACT-005 | PostgreSQL académico | Base de datos | Dirección Académica | DBA/TI | Red datos | Información académica ficticia | 5 | 5 | 5 | Crítica | ACT-001; ACT-010 | Implementado |
| ACT-006 | Keycloak | Identidad | Seguridad TI | IAM/TI | Red identidad/apps | Identidades, roles y eventos de autenticación ficticios | 5 | 5 | 5 | Crítica | ACT-007; ACT-004 | Implementado |
| ACT-007 | PostgreSQL de identidad | Base de datos | Seguridad TI | DBA/IAM | Red identidad | Configuración, usuarios y credenciales derivadas | 5 | 5 | 5 | Crítica | ACT-001; ACT-010 | Implementado |
| ACT-008 | SIEM ligero SQLite | Monitoreo | Seguridad TI | Analista de Seguridad | Host local | Eventos saneados y alertas | 4 | 5 | 4 | Alta | Docker logs; ACT-009 | Implementado |
| ACT-009 | Suricata offline (7 reglas) | IDS | Seguridad TI | Analista de Seguridad | Perfil Docker aislado (sin red) | PCAP sintético y alertas EVE | 3 | 5 | 3 | Alta | Reglas IDS; ACT-008 | Implementado parcial (offline) |
| ACT-010 | Repositorio local de backups cifrados | Respaldo | TI UVCG | DBA/TI | Disco local | Copias cifradas de ACT-005 y ACT-007 | 5 | 5 | 5 | Crítica | ACT-001; ACT-011 | Implementado |
| ACT-011 | Secretos locales .env | Información de autenticación | Seguridad TI | Administrador del laboratorio | Host local, ignorado por Git | Claves de DB, IAM y cifrado | 5 | 5 | 5 | Crítica | ACL del host; gestión manual | Implementado laboratorio |
| ACT-012 | Código y configuración SGSI | Software/Información | TI UVCG | DevSecOps | Workspace local | Código, Compose, Terraform y políticas | 4 | 5 | 4 | Alta | ACT-001; control de versiones futuro | Implementado |
| ACT-013 | Certificado y clave TLS de laboratorio | Criptográfico | Seguridad TI | TI Infraestructura | Host/volumen TLS | Identidad TLS autofirmada del laboratorio | 5 | 5 | 4 | Alta | ACT-004; ACT-011 | Implementado laboratorio |
| ACT-014 | Evidencias técnicas y documentos SGSI | Información | Responsable SGSI | Equipo del proyecto | Workspace local | Resultados, matrices y reportes saneados | 4 | 5 | 4 | Alta | ACT-001; ACT-012 | Implementado |
| ACT-015 | Entorno híbrido AWS (VPC multi-AZ) | Cloud | TI UVCG | Cloud/DevSecOps | AWS us-east-1 | Redes, IAM, monitoreo y recuperación | 4 | 5 | 5 | Crítica | Cuenta AWS, presupuesto, conectividad | Planificado |
| ACT-016 | Repositorio offsite/inmutable | Respaldo | TI UVCG | DBA/Continuidad | Por definir | Segunda copia y retención institucional | 5 | 5 | 5 | Crítica | Proveedor/ubicación aprobados | Planificado |
| ACT-017 | SIEM empresarial | Seguridad | Seguridad TI | SOC/Proveedor | Por definir | Telemetría institucional y casos de uso | 5 | 5 | 5 | Crítica | Licencia, almacenamiento, personal | Planificado |
| ACT-018 | MDM/EDR institucional | Endpoint | Seguridad TI | Soporte/SOC | Dispositivos institucionales | Postura, cumplimiento y respuesta endpoint | 5 | 5 | 4 | Alta | Licencias y enrolamiento | Planificado |
| ACT-019 | Plataforma virtual de aprendizaje | Aplicación | Dirección Académica | TI Aplicaciones | Escenario institucional | Contenido, evaluaciones y actividad docente | 5 | 5 | 5 | Crítica | Identidad; red; proveedores | Académico no implementado |
| ACT-020 | Sistema financiero/pagos | Aplicación | Dirección Financiera | TI/Finanzas | Escenario institucional | Pagos y registros financieros | 5 | 5 | 5 | Crítica | Banca; identidad; cumplimiento | Académico no implementado |
| ACT-021 | Correo/comunicaciones | Servicio | Comunicación Institucional | TI/Proveedor | Escenario institucional | Mensajes y notificaciones | 4 | 4 | 5 | Alta | Proveedor; DNS; identidad | Académico no implementado |
| ACT-022 | Monitor de disponibilidad continuo (uptime-monitor) | Monitoreo | Seguridad TI | Analista de Seguridad | Red DMZ Docker | Estado y latencia de Nginx, API y Keycloak | 2 | 4 | 4 | Media | ACT-004; ACT-008 | Implementado |
| ACT-023 | Laboratorio PITR y archivo WAL aislado | Respaldo | TI UVCG | DBA/Continuidad | Volúmenes sgsi_pitr_* (red recovery/none) | Respaldos base y segmentos WAL de réplicas | 5 | 5 | 4 | Alta | ACT-010; ACT-011 | Implementado (réplicas); principales preparado |
| ACT-024 | Registro operativo del SGSI | Información | Responsable SGSI | Equipo del proyecto | evidencias/gestion | Incidentes, cambios, accesos, activos y evaluaciones | 4 | 5 | 3 | Alta | ACT-014 | Implementado |
| ACT-030 | Cuenta AWS del SGSI (plan Free) | Servicio cloud | Dirección TI | Operador de plataforma | AWS us-east-1 | Recursos del laboratorio híbrido | 3 | 4 | 3 | Alta | ACT-015 | Planificado |
| ACT-031 | VPC, subredes y grupos de seguridad AWS | Red | Seguridad TI | Operador de plataforma | AWS us-east-1 | Flujos DMZ/apps/datos/endpoints privados | 3 | 5 | 4 | Alta | ACT-030; ACT-015 | Planificado |
| ACT-032 | AWS KMS / Secrets Manager del SGSI | Criptográfico | Seguridad TI | Administrador de seguridad | AWS us-east-1 | Secretos y certificados | 5 | 5 | 4 | Crítica | ACT-030; ACT-031 | Planificado |
| ACT-033 | Bucket S3 privado (evidencias e intercambio) | Información | Responsable SGSI | Operador de plataforma | AWS us-east-1 | Evidencias y copias cifradas ficticias | 4 | 5 | 3 | Alta | ACT-031; ACT-032; ACT-011 | Planificado |
| ACT-034 | CloudTrail / GuardDuty / Security Hub | Monitoreo | Seguridad TI | Analista de seguridad | AWS us-east-1 | Registros de actividad y diagnósticos | 4 | 5 | 3 | Alta | ACT-030 | Planificado |
| ACT-035 | AWS Backup / S3 Object Lock | Respaldo | TI UVCG | Operador de respaldo | AWS us-east-1 | Copias de servidores locales | 5 | 5 | 4 | Alta | ACT-030; ACT-001 | Planificado |
| ACT-036 | Conectividad híbrida (AWS Site-to-Site VPN) | Red | Redes | Operador de redes | AWS + campus | Tráfico cifrado campus-AWS | 4 | 5 | 3 | Alta | ACT-001; ACT-031 | Planificado |
| ACT-037 | Código IaC y estado de Terraform | Software/Información | DevSecOps | Operador de plataforma | Repositorio + backend Storage | Definición de infraestructura; estado sensible | 4 | 5 | 3 | Alta | ACT-030 | Implementado (código validado); estado inexistente |
| ACT-038 | Guardrails AWS (Budgets, AWS Config) y presupuesto | Gobierno | Responsable SGSI | Finanzas/SGSI | AWS | Reglas de cumplimiento y alertas de gasto | 2 | 4 | 2 | Media | ACT-030 | Planificado |