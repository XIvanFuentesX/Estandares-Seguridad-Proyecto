// Genera documento/Proyecto_Final_SGSI_UVCG.docx a partir de las matrices de governance/ y de las
// evidencias del laboratorio. Uso: node documento/generar_documento.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Header, AlignmentType, PageNumber, PageOrientation,
  TableOfContents, LevelFormat, PageBreak, NumberFormat, SectionType,
} = require("docx");
const L = require("./lib");
const { p, bullet, numbered, h1, h2, h3, table, figure, capturePlaceholder, note, readCsv, runs } = L;

const OUT = path.join(__dirname, "Proyecto_Final_SGSI_UVCG.docx");

// ---------- Datos del repositorio ----------
const activos = readCsv("governance/inventario-activos.csv");
const bia = readCsv("governance/bia.csv");
const riesgos = readCsv("governance/matriz-riesgos.csv");
const tratamiento = readCsv("governance/plan-tratamiento.csv");
const soa = readCsv("governance/declaracion-aplicabilidad.csv");
const soaById = Object.fromEntries(soa.map((r) => [r.control_id, r]));
const riesgoById = Object.fromEntries(riesgos.map((r) => [r.id, r]));

const nivel = (v) => (v <= 4 ? "Bajo" : v <= 9 ? "Moderado" : v <= 15 ? "Alto" : "Crítico");
const FILL = { Bajo: "C6EFCE", Moderado: "FFEB9C", Alto: "F8CBAD", "Crítico": "FF8B8B" };
const fillNivel = (v) => {
  const k = Object.keys(FILL).find((n) => String(v).includes(n));
  return k ? FILL[k] : undefined;
};
const contar = (arr, f) => arr.reduce((acc, x) => { const k = f(x); acc[k] = (acc[k] || 0) + 1; return acc; }, {});
const soaEstado = contar(soa, (r) => r.implementation_status);
const nImpl = soaEstado["Implementado/validado en laboratorio"] || 0;
const nParc = soaEstado["Parcial/preparado"] || 0;
const nPend = soaEstado["Pendiente de implementación institucional"] || 0;
const resNiv = contar(riesgos, (r) => r.nivel_residual);
const inhNiv = contar(riesgos, (r) => r.nivel_inherente);

// ---------- Portada y tabla de contenido ----------
function portada() {
  const c = (text, opts = {}) => new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: opts.after ?? 120, before: opts.before ?? 0, line: 240 },
    children: runs(text, { size: opts.size || 24, bold: opts.bold }),
  });
  return [
    c("[[NOMBRE DE LA UNIVERSIDAD QUE IMPARTE LA MAESTRÍA]]", { bold: true, size: 28, before: 600 }),
    c("Maestría en Seguridad Informática"),
    c("Curso: Estándares de Seguridad", { after: 1400 }),
    c("Proyecto Final", { bold: true, size: 28 }),
    c("Diseño e implementación de un Sistema de Gestión de Seguridad de la Información (SGSI) para la universidad ficticia UVCG en una arquitectura de nube híbrida con AWS",
      { bold: true, size: 28, after: 1400 }),
    c("Docente: [[NOMBRE DEL DOCENTE]]"),
    c("Integrantes del grupo:", { before: 240 }),
    c("[[Nombre completo — carné]]"),
    c("[[Nombre completo — carné]]"),
    c("[[Nombre completo — carné]]", { after: 1400 }),
    c("Guatemala, noviembre de 2026"),
  ];
}

function indice() {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: "Tabla de contenido", bold: true, font: L.FONT })] }),
    new TableOfContents("Tabla de contenido", { hyperlink: true, headingStyleRange: "1-2" }),
  ];
}

// ---------- 1. Introducción ----------
function introduccion() {
  return [
    h1("1. Introducción"),
    p("Las universidades concentran información de alto valor —expedientes académicos, credenciales, datos financieros y propiedad intelectual— y la exponen a una población de usuarios amplia, rotativa y que trabaja desde dispositivos propios. A esa superficie se suma la adopción de servicios en la nube, que traslada parte del control a un proveedor y exige gobernar la responsabilidad compartida. En ese contexto, la seguridad no puede limitarse a productos aislados: requiere un sistema de gestión que identifique qué proteger, por qué, con qué prioridad y cómo demostrar que los controles funcionan."),
    p("Este documento presenta el diseño y la implementación de un Sistema de Gestión de Seguridad de la Información (SGSI) para la UVCG, una universidad privada ficticia de Guatemala con unos 3,000 estudiantes, 180 docentes y 120 colaboradores administrativos. La solución adopta una **arquitectura de nube híbrida**: un sitio principal en el campus y servicios de **Amazon Web Services (AWS)** como nube pública, con soporte para computadoras, teléfonos móviles y tabletas institucionales y personales (BYOD)."),
    p("El trabajo sigue un enfoque basado en riesgos. Parte del contexto y del inventario de activos, analiza el impacto de la interrupción de los procesos críticos (BIA), evalúa los riesgos con NIST SP 800-30 e ISO/IEC 27005 y los contrasta con OCTAVE Allegro, y deriva de allí el plan de tratamiento, los controles de ISO/IEC 27002, las políticas, la arquitectura Zero Trust, la continuidad según ISO 22301, el gobierno con COBIT 2019 e ITIL 4 y las buenas prácticas de centro de datos según TIA-942."),
    p("Una característica central del proyecto es la **trazabilidad verificable**: cada control implementado cuenta con una prueba automatizada y una evidencia identificada en el repositorio del proyecto. Para cumplir con los criterios de originalidad del curso, el documento distingue de forma explícita entre componentes **implementados y probados**, **preparados** (configuración lista y validada, sin desplegar) y **diseñados** (sólo documentados). Ninguna evidencia fue simulada como si fuera real; cuando un resultado proviene de un ejercicio o de datos sintéticos, se indica."),
    p("El documento se organiza así: el capítulo 2 resume el marco de referencia y cómo se aplicó cada estándar; el capítulo 3 describe la metodología; el capítulo 4 presenta los veinte resultados mínimos exigidos; el capítulo 5 desarrolla la discusión académica del grupo; el capítulo 6 expone las conclusiones, y los anexos contienen las matrices completas y el registro de evidencias."),
  ];
}

// ---------- 2. Marco teórico ----------
function marcoTeorico() {
  const filas = [
    ["ISO/IEC 27001:2022", "Requisitos del SGSI (cláusulas 4 a 10) y Anexo A.", "Contexto y alcance (4.2), objetivos (4.3), tratamiento de riesgos y declaración de aplicabilidad de 93 controles (4.12), mejora continua (6.5).", "governance/declaracion-aplicabilidad.csv"],
    ["ISO/IEC 27002:2022", "Guía de implementación de los 93 controles.", "Selección de controles por riesgo en el plan de tratamiento y la matriz de controles (4.10 y 4.12).", "governance/plan-tratamiento.csv"],
    ["ISO/IEC 27005:2022", "Proceso de gestión del riesgo de seguridad de la información.", "Criterios de aceptación, identificación, análisis, evaluación, tratamiento y seguimiento de 22 riesgos (4.7).", "governance/matriz-riesgos.md"],
    ["NIST SP 800-30 Rev. 1", "Evaluación de riesgos basada en amenaza, vulnerabilidad, probabilidad e impacto.", "Escalas 1–5, riesgo inherente y residual, efectividad de controles (4.7).", "governance/matriz-riesgos.csv"],
    ["OCTAVE Allegro", "Evaluación de riesgos centrada en activos de información y sus contenedores.", "Ocho pasos aplicados a cinco activos críticos y ocho escenarios priorizados en tres grupos (4.8).", "governance/octave-allegro.md"],
    ["NIST CSF 2.0", "Resultados de ciberseguridad organizados en seis funciones.", "Perfil actual y objetivo de la UVCG por función (4.12).", "Tabla de perfil CSF"],
    ["NIST SP 800-207 (ZTA)", "Arquitectura de confianza cero: verificación explícita por solicitud.", "Matriz de acceso por recurso y rol, validación de token y MFA en cada petición, segmentación (4.14).", "policies/matriz-acceso-zero-trust.md"],
    ["ISO 22301:2019", "Sistema de gestión de la continuidad del negocio.", "BIA con RTO, RPO y MTPD, BCP, DRP, pruebas de recuperación medidas (4.6 y 4.18).", "governance/bcp.md, drp.md"],
    ["COBIT 2019", "Gobierno y gestión de la información y la tecnología.", "Trece objetivos de gobierno y gestión con autoevaluación de capacidad (4.19).", "governance/marcos-cobit-itil-tia942.md"],
    ["ITIL 4", "Prácticas de gestión de servicios.", "Incidentes, cambios, solicitudes, activos, configuración, continuidad y seguridad con registros reales del laboratorio (4.19).", "governance/registros-operativos.md"],
    ["ANSI/TIA-942-B", "Infraestructura de telecomunicaciones de centros de datos y niveles de disponibilidad.", "Buenas prácticas de energía, climatización, cableado, seguridad física e incendios para el centro de datos del campus (4.20).", "Sección 4.20"],
  ];
  return [
    h1("2. Marco teórico"),
    p("El enunciado del proyecto exige demostrar cómo se aplicó cada estándar y no presentar definiciones teóricas. Por ello, este capítulo resume en una sola tabla el propósito de cada marco y remite a la sección de resultados donde se aplica y a la evidencia que lo respalda. Los marcos se usaron de forma complementaria: ISO/IEC 27001 aporta el sistema de gestión; ISO/IEC 27005, NIST SP 800-30 y OCTAVE Allegro, el análisis de riesgos; ISO/IEC 27002 y NIST CSF, el catálogo y la organización de controles; NIST SP 800-207, el modelo de acceso; ISO 22301, la continuidad; COBIT 2019 e ITIL 4, el gobierno y la operación, y TIA-942, la infraestructura física."),
    ...table("Estándares de referencia y su aplicación en el proyecto", ["Estándar / marco", "Propósito", "Aplicación concreta en la UVCG", "Evidencia"],
      filas, [16, 22, 40, 22]),
    h2("2.1 Conceptos operativos utilizados"),
    p("Para evitar ambigüedades en la defensa, el grupo adoptó las siguientes definiciones de trabajo. **Riesgo** es la combinación de la probabilidad de que una amenaza explote una vulnerabilidad y el impacto resultante sobre la confidencialidad, integridad o disponibilidad (ISO/IEC 27005). **Riesgo inherente** es el valorado sin controles y **riesgo residual** el que permanece tras los controles existentes, ajustado por su efectividad comprobada. **RTO** (tiempo objetivo de recuperación) es el plazo máximo para restablecer un proceso; **RPO** (punto objetivo de recuperación) es la pérdida de datos máxima tolerable medida en tiempo, y **MTPD** (periodo máximo tolerable de interrupción) es el umbral a partir del cual el impacto se vuelve inaceptable (ISO 22301)."),
    p("En la clasificación del estado de cada componente se usan cuatro categorías: **Implementado** (en funcionamiento y verificado por una prueba reproducible), **Parcial** (funciona con limitaciones declaradas), **Preparado** (código o configuración listos y validados estáticamente, sin despliegue) y **Diseñado** (documentado en la arquitectura objetivo, sin construcción)."),
  ];
}

// ---------- 3. Metodología ----------
function metodologia() {
  return [
    h1("3. Metodología"),
    h2("3.1 Enfoque y ciclo de mejora"),
    p("El proyecto siguió el ciclo Planificar-Hacer-Verificar-Actuar en el que se apoya ISO/IEC 27001. En **Planificar** se definieron el contexto, el alcance, el inventario, el BIA, los riesgos y el plan de tratamiento. En **Hacer** se construyó el laboratorio y se configuraron los controles. En **Verificar** se ejecutaron pruebas automatizadas que producen evidencias con fecha y resultado. En **Actuar** los hallazgos de las pruebas se registraron como incidentes o cambios y alimentaron nuevamente la matriz de riesgos."),
    h2("3.2 Fases del proyecto"),
    ...table("Fases del enunciado, actividades y entregables", ["Fase", "Actividades realizadas", "Entregable", "Sección"], [
      ["1. Diseño de infraestructura", "Arquitectura híbrida campus + AWS, zonas, direccionamiento, flujos, redundancia y continuidad inicial", "E1", "4.3 y 4.4"],
      ["2. Construcción del ambiente", "Laboratorio con 7 servicios en Docker, redes segmentadas, IAM/MFA, monitoreo, respaldo y recuperación; IaC de AWS validada", "E2", "4.17"],
      ["3. Modelo de gestión", "Alcance, contexto, activos, procesos críticos, riesgos, controles, políticas, Zero Trust, incidentes, continuidad y gobierno", "E3", "4.1 a 4.2 y 4.11 a 4.19"],
      ["4. Gestión de riesgos", "Inventario (33 activos), BIA (7 procesos), matriz NIST SP 800-30 (22 riesgos), OCTAVE Allegro, matriz de calor y plan de tratamiento", "E4.1 a E4.6", "4.5 a 4.10"],
      ["5. Políticas y controles", "Políticas por dominio, matriz de controles vinculada a riesgos y buenas prácticas", "E5.1 a E5.3", "4.11 a 4.13"],
      ["6. Gobierno y servicios", "COBIT 2019 e ITIL 4 aplicados con registros operativos reales", "E6", "4.19"],
      ["7. Continuidad y data center", "BCP, DRP, pruebas de recuperación medidas y buenas prácticas TIA-942", "E7", "4.18 y 4.20"],
    ], [20, 50, 12, 18]),
    h2("3.3 Fuentes de información y naturaleza de los datos"),
    p("Al tratarse de una organización ficticia, no fue posible realizar entrevistas ni talleres con responsables reales. Los valores del BIA, las escalas de impacto, las prioridades de OCTAVE y los responsables son **supuestos académicos** construidos por el grupo a partir del escenario y deben validarse con los propietarios de procesos en una implantación real. En cambio, los resultados técnicos (tiempos de recuperación, detecciones, bloqueos, conteos de eventos) provienen de **ejecuciones reales** en el laboratorio y están respaldados por archivos de evidencia con marca de tiempo. Los datos personales usados en las pruebas son sintéticos."),
    h2("3.4 Herramientas"),
    p("El laboratorio se construyó en un equipo con Windows 11 y Docker Desktop (16 GB de RAM). Se usaron Nginx, Flask/Gunicorn, PostgreSQL 16 con una imagen endurecida propia, Keycloak 26.8.1 como proveedor de identidad, Suricata 7.0 como IDS, Trivy, Bandit y pip-audit para gestión de vulnerabilidades, y scripts propios en Python y PowerShell para el SIEM ligero, la compuerta DLP, la vigilancia de contenedores, la integridad de configuración y el registro operativo. La infraestructura de AWS se definió con Terraform 1.9+ y se validó con `terraform validate`, `terraform test`, TFLint y Trivy."),
    h2("3.5 Validación y trazabilidad"),
    p("El script `scripts/validar_sgsi.ps1` ejecuta en una sola corrida las pruebas de todos los módulos y clasifica cada control como exitoso, fallido, omitido o no verificable. El script `scripts/validar_trazabilidad.py` comprueba 21 reglas de coherencia entre las matrices: que cada riesgo apunte a activos existentes, que cada riesgo tenga tratamiento, que los controles citados existan en la declaración de aplicabilidad y que el BIA cumpla RPO ≤ RTO < MTPD, entre otras. Ambas validaciones se ejecutaron con resultado satisfactorio; las excepciones se informan en la sección 4.17."),
  ];
}

// ---------- 4. Resultados ----------
function escenario() {
  return [
    h2("4.1 Descripción del escenario"),
    p("La UVCG es una universidad privada ficticia con sede central en la Ciudad de Guatemala y oferta presencial, semipresencial y virtual. Atiende a cerca de **3,000 estudiantes** de grado y posgrado, con **180 docentes** y **120 colaboradores administrativos**. Durante los periodos de inscripción y de evaluaciones la demanda sobre los servicios digitales se multiplica, y una parte relevante de los estudiantes accede desde teléfonos móviles y redes domésticas."),
    ...table("Estructura organizacional de la UVCG (escenario)", ["Unidad", "Función", "Relación con el SGSI"], [
      ["Rectoría y Consejo Directivo", "Dirección estratégica", "Aprueba la política, el apetito de riesgo y los recursos"],
      ["Comité de Seguridad de la Información", "Vicerrectoría, TI, Legal, Registro y Finanzas", "Supervisa el SGSI, revisa riesgos e indicadores trimestralmente"],
      ["Vicerrectoría Académica", "Cuatro facultades, docencia y aprendizaje virtual", "Propietaria de PROC-002 y PROC-003"],
      ["Registro Académico", "Matrícula, expedientes y certificaciones", "Propietario de PROC-001"],
      ["Dirección Financiera", "Cobros, conciliación y pagos", "Propietaria de PROC-005"],
      ["Dirección de Tecnología (TI)", "Infraestructura, aplicaciones, mesa de servicio", "Custodio técnico; incluye el área de Seguridad TI"],
      ["Oficial de Seguridad de la Información", "Responsable del SGSI", "Coordina riesgos, políticas, incidentes y auditoría interna"],
      ["Asesoría Legal", "Cumplimiento y contratos", "Requisitos legales, cláusulas con proveedores y notificación de brechas"],
      ["Comunicación Institucional", "Canales internos y externos", "Propietaria de PROC-007 y de la comunicación en crisis"],
    ], [28, 34, 38]),
    ...table("Usuarios y actores", ["Actor", "Cantidad aprox.", "Dispositivos", "Acceso requerido"], [
      ["Estudiantes", "3,000", "Móviles y portátiles personales (BYOD)", "Portal, LMS, consulta de notas y pagos"],
      ["Docentes", "180", "Portátiles institucionales y móviles BYOD", "LMS, registro de calificaciones, correo"],
      ["Personal administrativo", "120", "PC institucionales", "Sistemas financieros, matrícula y RR. HH."],
      ["Administradores de TI", "8", "Estaciones de gestión dedicadas", "Acceso privilegiado con MFA y registro"],
      ["Terceros", "Variable", "Equipos del proveedor", "Soporte remoto limitado en tiempo y alcance"],
      ["Proveedor de nube (AWS)", "—", "—", "Responsabilidad compartida sobre la infraestructura cloud"],
    ], [24, 14, 30, 32]),
    ...table("Servicios tecnológicos y necesidades de seguridad", ["Servicio", "Proceso", "Necesidad principal"], [
      ["Identidad y autenticación (SSO)", "PROC-004", "Disponibilidad y confidencialidad de credenciales; MFA obligatorio"],
      ["Portal académico y API", "PROC-001, PROC-002", "Integridad de calificaciones y expedientes"],
      ["Plataforma virtual de aprendizaje (LMS)", "PROC-003", "Disponibilidad en periodos de evaluación"],
      ["Sistema financiero y de pagos", "PROC-005", "Integridad y confidencialidad de datos de pago"],
      ["Correo y comunicaciones", "PROC-007", "Disponibilidad como canal de crisis; protección contra suplantación"],
      ["Respaldo y recuperación", "Transversal", "Copias cifradas, verificadas y fuera del sitio"],
    ], [32, 20, 48]),
  ];
}

function alcance() {
  return [
    h2("4.2 Alcance del SGSI y contexto de la organización"),
    p("**Alcance.** El SGSI cubre los procesos de inscripción y matrícula, gestión académica, aprendizaje virtual, identidad y autenticación, gestión financiera, servicios administrativos y comunicaciones (PROC-001 a PROC-007); la información que estos procesan; la infraestructura del centro de datos del campus; los servicios en la cuenta de AWS de la universidad, y los dispositivos institucionales y personales que acceden a información interna o superior. Quedan fuera del alcance los sistemas de investigación aislados de las facultades y la red de invitados, que no procesan información clasificada."),
    p("**Cuestiones externas e internas (cláusula 4.1).** Externamente, la UVCG enfrenta ataques de robo de credenciales dirigidos al sector educativo, la dependencia de proveedores SaaS y de nube, y un marco legal guatemalteco sin ley general de protección de datos personales, pero con obligaciones constitucionales y penales. Internamente, cuenta con un equipo de TI reducido, una alta proporción de dispositivos BYOD, presupuesto limitado y picos estacionales de carga."),
    ...table("Partes interesadas y requisitos (cláusula 4.2)", ["Parte interesada", "Requisito o expectativa", "Cómo lo atiende el SGSI"], [
      ["Estudiantes", "Privacidad del expediente y disponibilidad en inscripción y exámenes", "RBAC, MFA, BIA con RTO de 4 h para PROC-001 y PROC-003"],
      ["Docentes", "Integridad de las calificaciones registradas", "Rol docente acotado, registro de accesos, respaldos verificados"],
      ["Dirección y Consejo", "Continuidad y reputación institucional", "BCP/DRP, matriz de riesgos e indicadores"],
      ["Entes reguladores de educación superior", "Conservación de expedientes y certificaciones", "Retención y recuperación probadas"],
      ["Bancos y pasarelas de pago", "Protección de datos de tarjetas", "Clasificación restringida y bloqueo DLP de números de tarjeta"],
      ["Proveedor de nube (AWS)", "Uso conforme al modelo de responsabilidad compartida", "IAM de mínimo privilegio, cifrado, registro y presupuesto"],
    ], [24, 38, 38]),
    ...table("Objetivos de seguridad de la información (cláusula 6.2)", ["Objetivo", "Indicador", "Meta"], [
      ["Proteger el acceso a la información académica", "% de cuentas con MFA activo", "100 % de cuentas privilegiadas y del personal"],
      ["Garantizar la recuperación de datos críticos", "Pruebas de restauración exitosas", "1 prueba semanal automatizada; 100 % exitosas"],
      ["Detectar incidentes oportunamente", "Reglas de correlación con detección verificada", "≥ 10 reglas probadas con eventos reales"],
      ["Reducir el riesgo residual crítico", "Riesgos residuales en nivel crítico", "0 al cierre del primer año (hoy: " + (resNiv["Crítico"] || 0) + ")"],
      ["Mantener vulnerabilidades bajo control", "Hallazgos críticos sin tratar en imágenes en uso", "0 con corrección disponible"],
    ], [38, 34, 28]),
  ];
}

function arquitectura() {
  return [
    h2("4.3 Diagrama de infraestructura"),
    p("La Figura 1 muestra la arquitectura híbrida objetivo y diferencia con colores lo implementado, lo preparado y lo diseñado. La Figura 2 muestra el laboratorio efectivamente construido, que materializa las zonas DMZ, aplicaciones, identidad y datos del sitio principal mediante redes Docker aisladas."),
    ...figure("Arquitectura híbrida objetivo de la UVCG (campus + AWS)", "documento/figuras/arquitectura-hibrida.png",
      "Elaboración propia. Verde: implementado y probado en el laboratorio; azul: desplegado en AWS con Terraform y probado (13/13); gris punteado: diseñado. El diagrama fue presentado al docente para aprobación el [[FECHA DE APROBACIÓN DEL DIAGRAMA]]."),
    ...figure("Laboratorio implementado en Docker Desktop", "documento/figuras/laboratorio-implementado.png",
      "Elaboración propia a partir de local/compose.yaml. Subredes asignadas por Docker y verificadas con docker network inspect el 7 de noviembre de 2026."),
    h2("4.4 Explicación de la arquitectura"),
    h3("4.4.1 Componentes"),
    ...table("Componentes de la arquitectura y estado", ["Componente", "Función", "Tecnología", "Estado"], [
      ["Servidores", "Ejecutan aplicaciones e identidad", "Hosts de virtualización N+1 (diseño); contenedores Docker (lab)", "Implementado (lab)"],
      ["Bases de datos", "Datos académicos y de identidad separados", "PostgreSQL 16 endurecido, redes internas distintas", "Implementado"],
      ["Almacenamiento", "Volúmenes y copias", "SAN/NAS RAID 10 (diseño); volúmenes Docker y S3 privado en AWS", "Implementado (S3) / diseñado (SAN)"],
      ["Switches", "Acceso y núcleo con VLAN y 802.1X", "Switches apilados de capa 3", "Diseñado"],
      ["Routers", "Borde con doble ISP", "Routers redundantes con BGP/estático", "Diseñado"],
      ["Firewall NGFW", "Filtrado por aplicación, IPS en línea, VPN", "Clúster activo/pasivo", "Diseñado"],
      ["IDS/IPS", "Detección de patrones de ataque", "Suricata 7.0 con 7 reglas propias", "Implementado (offline)"],
      ["DMZ", "Única zona expuesta", "Proxy inverso Nginx con TLS", "Implementado"],
      ["Segmentación", "Separación por función", "VLAN (diseño); 5 redes Docker, 4 internas (lab); VPC con 6 subredes (AWS)", "Implementado (lab)"],
      ["Virtualización / contenedores", "Aislamiento y portabilidad", "Docker con contenedores de sólo lectura y sin privilegios", "Implementado"],
      ["IAM y MFA", "Identidad central, OIDC, TOTP, roles", "Keycloak 26.8.1; IAM de AWS con STS", "Implementado"],
      ["Zero Trust", "Verificación explícita por solicitud", "Validación de JWT, MFA y rol en cada ruta", "Implementado (parcial)"],
      ["SIEM", "Correlación de eventos", "SIEM ligero propio (SQLite) con 11 reglas", "Implementado (parcial)"],
      ["Respaldo", "Copias cifradas y verificadas", "AES-256 + SHA-256 diario; PITR con WAL en réplicas", "Implementado"],
      ["Redundancia y alta disponibilidad", "Eliminar puntos únicos de falla", "Par NGFW, ISP doble, N+1, RDS Multi-AZ", "Diseñado"],
      ["Continuidad y recuperación", "Recuperar dentro del RTO", "BCP/DRP, restauración aislada semanal", "Implementado (lab)"],
    ], [20, 26, 36, 18]),
    h3("4.4.2 Direccionamiento y segmentación"),
    ...table("Plan de direccionamiento", ["Zona", "Diseño institucional", "Laboratorio (Docker)", "AWS (VPC 10.30.0.0/16)"], [
      ["DMZ", "VLAN 10 · 10.10.10.0/24", "dmz · 172.23.0.0/16", "Públicas 10.30.0.0/24 y 10.30.1.0/24"],
      ["Aplicaciones", "VLAN 20 · 10.10.20.0/24", "apps · 172.24.0.0/16 (interna)", "Apps 10.30.10.0/24 y 10.30.11.0/24"],
      ["Datos", "VLAN 30 · 10.10.30.0/24", "datos · 172.25.0.0/16 (interna)", "Datos 10.30.20.0/24 y 10.30.21.0/24"],
      ["Identidad", "VLAN 40 · 10.10.40.0/24", "identity · 172.26.0.0/16 (interna)", "IAM Identity Center (servicio regional)"],
      ["Gestión", "VLAN 50 · 10.10.50.0/24", "Host (scripts)", "Acceso por consola/CLI con MFA"],
      ["Seguridad / SIEM", "VLAN 60 · 10.10.60.0/24", "Host (SIEM ligero)", "CloudTrail, GuardDuty, Security Hub"],
      ["Recuperación", "VLAN 70 · 10.10.70.0/24", "recovery · 172.27.0.0/16 (interna)", "Bucket S3 / AWS Backup"],
      ["Usuarios", "VLAN 100–130: administrativos, docentes, estudiantes, invitados", "—", "—"],
    ], [16, 30, 27, 27]),
    h3("4.4.3 Flujos de comunicación"),
    ...table("Flujos permitidos (todo lo demás se deniega)", ["N.º", "Origen", "Destino", "Puerto / protocolo", "Control"], [
      ["F1", "Usuarios (Internet)", "Proxy DMZ", "TCP 443 (HTTP 80 sólo redirige)", "TLS 1.2+, cabeceras de seguridad, sólo GET/HEAD"],
      ["F2", "Proxy DMZ", "API académica", "TCP 8000", "Red apps interna; la API valida el JWT"],
      ["F3", "Proxy DMZ", "Keycloak", "TCP 8080 (/auth)", "Consola de administración no expuesta"],
      ["F4", "API académica", "PostgreSQL académico", "TCP 5432", "Red datos interna; usuario de aplicación sin privilegios de administrador"],
      ["F5", "Keycloak", "PostgreSQL de identidad", "TCP 5432", "Red identity interna separada"],
      ["F6", "Respaldo", "Bases de datos", "TCP 5432", "Sólo los contenedores de respaldo; copias cifradas"],
      ["F7", "Campus", "AWS VPC", "IPsec (UDP 500/4500)", "Site-to-Site VPN con dos túneles (diseño)"],
      ["F8", "Operador / respaldo", "Amazon S3", "TCP 443", "Credenciales temporales STS; política que niega TLS < 1.2"],
      ["F9", "Proxy ↔ base de datos", "—", "—", "Bloqueado y verificado por prueba (segmentación)"],
    ], [7, 20, 20, 20, 33]),
    h3("4.4.4 Mecanismos de redundancia y alta disponibilidad"),
    bullet("**Perímetro:** par de NGFW activo/pasivo con sincronización de sesiones y dos proveedores de Internet."),
    bullet("**Cómputo:** hosts de virtualización en esquema N+1; en el laboratorio, política `restart: unless-stopped` y verificaciones de salud que reinician servicios caídos (recuperación medida de la API en 12 s)."),
    bullet("**Datos:** respaldos diarios cifrados, archivado WAL para recuperación a un punto en el tiempo y copia fuera del sitio en S3 con bloqueo de objetos (diseño)."),
    bullet("**Nube:** VPC distribuida en dos zonas de disponibilidad con balanceador y base de datos Multi-AZ como sitio de recuperación (diseño)."),
    bullet("**Energía y climatización:** UPS de doble conversión, generador y aire acondicionado de precisión redundante (sección 4.20)."),
    h3("4.4.5 Estrategia inicial de continuidad y recuperación"),
    p("La estrategia prioriza la identidad, porque todos los procesos dependen de ella, seguida de matrícula, aprendizaje virtual y gestión académica. Se combinan respaldos cifrados locales para recuperaciones rápidas, archivado WAL para cumplir RPO de minutos y una copia inmutable en AWS para sobrevivir a la pérdida del sitio o a un ataque de ransomware. El detalle está en la sección 4.18."),
    h3("4.4.6 Justificación técnica"),
    p("Se eligió una **arquitectura híbrida** porque los sistemas académicos y la identidad requieren baja latencia y control local, mientras que la recuperación ante desastres y la copia fuera del sitio son más económicas y resilientes en la nube que en un segundo centro de datos propio. Se seleccionó **AWS** frente a Azure y Google Cloud porque su modelo de responsabilidad compartida está ampliamente documentado, ofrece una cuenta con plan gratuito que permite demostrar el componente cloud sin costo, y porque los controles necesarios —S3 con bloqueo de acceso público y cifrado, IAM con credenciales temporales, CloudTrail y AWS Budgets— están disponibles sin licencias adicionales. La región es us-east-2 (Ohio): es la habilitada para la cuenta de la universidad y ofrece latencia adecuada desde Guatemala."),
    p("La segmentación en zonas sigue el principio de mínima exposición: sólo el proxy de la DMZ es alcanzable desde fuera, y las bases de datos residen en redes internas sin salida. Esta decisión reduce el riesgo R-001 (acceso no autorizado) y fue verificada por pruebas que confirman que el proxy no puede resolver ni alcanzar la base de datos. La alternativa de exponer la API directamente se descartó porque eliminaba el punto único de inspección y control de cabeceras."),
  ];
}

function inventario() {
  const porTipo = contar(activos, (a) => a.criticidad);
  return [
    h2("4.5 Inventario de activos"),
    p(`Se inventariaron **${activos.length} activos** de información, tecnológicos y organizacionales, con identificador, tipo, propietario, custodio, ubicación, información procesada, valoración de confidencialidad, integridad y disponibilidad (escala 1–5), criticidad y dependencias. Por criticidad: ${Object.entries(porTipo).map(([k, v]) => `${v} ${k.toLowerCase()}`).join(", ")}. La columna de estado distingue los activos implementados en el laboratorio de los planificados para la arquitectura objetivo. La Tabla ${L.nextTable()} resume los activos críticos; el inventario completo está en el Anexo A.`),
    ...table("Activos de criticidad crítica", ["ID", "Activo", "Tipo", "Propietario", "C", "I", "D", "Estado"],
      activos.filter((a) => a.criticidad === "Crítica").map((a) => [a.id, a.activo, a.tipo, a.propietario, a.confidencialidad_1_5, a.integridad_1_5, a.disponibilidad_1_5, a.estado_real]),
      [8, 26, 14, 14, 4, 4, 4, 26], { center: [4, 5, 6], note: "C, I y D en escala 1 (bajo) a 5 (muy alto). Fuente: governance/inventario-activos.csv." }),
  ];
}

function biaSec() {
  return [
    h2("4.6 Análisis de impacto en el negocio (BIA)"),
    p("Se analizaron siete procesos. Para cada uno se valoraron cinco dimensiones de impacto en escala 1–5 —operativo, financiero (con umbrales en quetzales), académico, reputacional y legal— y se fijaron RTO, RPO y MTPD. La criticidad se asigna como **Crítica** si dos o más dimensiones alcanzan 5, y **Alta** si el máximo es 4 o una sola dimensión vale 5. El script de trazabilidad verifica automáticamente que RPO ≤ RTO < MTPD y que el RTO no supere el 50 % del MTPD, para dejar margen a la detección y la decisión."),
    ...table("Escalas de impacto del BIA", ["Nivel", "Operativo", "Financiero", "Académico", "Reputacional", "Legal"], [
      ["1", "Sin efecto perceptible", "< Q10,000", "Sin efecto", "Sin difusión", "Sin incumplimiento"],
      ["2", "Demora menor con alternativa", "Q10,000–50,000", "Reprogramación menor", "Quejas aisladas", "Incumplimiento interno menor"],
      ["3", "Proceso degradado < 1 día", "Q50,000–250,000", "Un grupo de cursos", "Difusión local", "Observación de un ente regulador"],
      ["4", "Proceso detenido en periodo normal", "Q250,000–1,000,000", "Una facultad o evaluación", "Medios regionales", "Sanción o reclamo formal probable"],
      ["5", "Proceso detenido en periodo crítico", "> Q1,000,000", "Toda la población estudiantil", "Cobertura nacional", "Sanción grave o exposición de datos personales"],
    ], [7, 19, 17, 19, 17, 21], { size: 16 }),
    ...table("Resultados del BIA", ["ID", "Proceso", "Responsable", "Op.", "Fin.", "Acad.", "Rep.", "Legal", "RTO (h)", "RPO (h)", "MTPD (h)", "Criticidad"],
      bia.map((b) => [b.id, b.proceso, b.responsable, b.impacto_operativo_1_5, b.impacto_financiero_1_5, b.impacto_academico_1_5,
        b.impacto_reputacional_1_5, b.impacto_legal_1_5, b.rto_horas, b.rpo_horas, b.mtpd_horas, b.criticidad]),
      [9, 17, 15, 5, 5, 6, 5, 6, 7, 7, 8, 10], { size: 16, center: [3, 4, 5, 6, 7, 8, 9, 10], fillFn: (v, i) => (i === 11 ? (v === "Crítica" ? FILL["Crítico"] : FILL.Alto) : undefined),
        note: "Valores propuestos por el grupo como supuestos académicos; deben validarse con los propietarios de proceso. Fuente: governance/bia.csv." }),
    p("El proceso de **identidad y autenticación (PROC-004)** obtuvo los objetivos más exigentes (RTO de 2 h, RPO de 15 min y MTPD de 4 h) porque su caída bloquea a todos los demás. El BIA reveló además una brecha cuantificable: con respaldos diarios el RPO real es de 24 h, incompatible con los 15 min de PROC-004 y las 4 h de PROC-002. Esa brecha se registró como el riesgo R-019 y motivó la implementación del archivado WAL, que en las pruebas sobre réplicas alcanzó un RPO observado de unos 56 segundos."),
  ];
}

function riesgosSec() {
  return [
    h2("4.7 Análisis de riesgos (NIST SP 800-30 e ISO/IEC 27005)"),
    p("El proceso siguió las etapas de ISO/IEC 27005: establecer el contexto y los criterios, identificar, analizar, evaluar, tratar, aceptar, comunicar y dar seguimiento. El análisis aplicó el modelo de NIST SP 800-30: para cada escenario se identificó el activo, la fuente de amenaza, la vulnerabilidad que la habilita y el resultado sobre la información. La **probabilidad** y el **impacto** se valoraron de 1 a 5, y el riesgo como su producto (1 a 25). El riesgo residual se recalculó tras valorar la efectividad de los controles existentes, que sólo se consideró alta cuando una prueba del laboratorio la demostraba."),
    ...table("Criterios de probabilidad e impacto", ["Valor", "Probabilidad", "Impacto (máximo de las dimensiones del BIA)"], [
      ["1", "Muy baja: no se espera en 5 años", "Insignificante"],
      ["2", "Baja: una vez en 2–5 años", "Menor"],
      ["3", "Media: una vez al año", "Moderado"],
      ["4", "Alta: varias veces al año", "Mayor"],
      ["5", "Muy alta: mensual o continua", "Severo"],
    ], [10, 45, 45]),
    p("**Criterios de aceptación.** Riesgo de 1 a 4: **Bajo**, aceptable con seguimiento anual. De 5 a 9: **Moderado**, aceptable con controles vigentes y revisión semestral. De 10 a 15: **Alto**, requiere plan de tratamiento con responsable y plazo. De 16 a 25: **Crítico**, requiere tratamiento inmediato y conocimiento de la Dirección; no puede aceptarse sin aprobación formal del Consejo."),
    p(`Resultado: de ${riesgos.length} riesgos, el inherente se distribuyó en ${inhNiv["Crítico"] || 0} críticos y ${inhNiv["Alto"] || 0} altos. Tras los controles existentes, el residual quedó en ${resNiv["Crítico"] || 0} críticos, ${resNiv["Alto"] || 0} altos, ${resNiv["Moderado"] || 0} moderados y ${resNiv["Bajo"] || 0} bajo. La matriz completa con escenario, controles existentes, efectividad y responsable está en el Anexo B.`),
  ];
}

function riesgosTabla() {
  return [
    ...table("Matriz de análisis de riesgos", ["ID", "Activo(s)", "Amenaza", "Vulnerabilidad", "P", "I", "Riesgo inherente", "Controles existentes", "P res.", "I res.", "Riesgo residual"],
      riesgos.map((r) => [r.id, r.activo, r.amenaza, r.vulnerabilidad, r.probabilidad_1_5, r.impacto_1_5, `${r.riesgo_inherente} ${r.nivel_inherente}`,
        r.controles_existentes, r.probabilidad_residual_1_5, r.impacto_residual_1_5, `${r.riesgo_residual} ${r.nivel_residual}`]),
      [6, 10, 13, 17, 3, 3, 8, 24, 4, 4, 8], { landscape: true, size: 14, center: [4, 5, 8, 9],
        fillFn: (v, i) => (i === 6 || i === 10 ? fillNivel(v) : undefined),
        note: "P = probabilidad, I = impacto (1–5). Riesgo = P × I. Fuente: governance/matriz-riesgos.csv." }),
  ];
}

function octave() {
  return [
    h2("4.8 Evaluación OCTAVE Allegro"),
    p("**Metodología.** Se eligió la variante **OCTAVE Allegro** del Software Engineering Institute porque se centra en activos de información y en los contenedores donde se almacenan, transportan y procesan, y porque puede aplicarse con un equipo reducido. Se ejecutaron sus ocho pasos como ejercicio de escritorio del grupo: (1) criterios de medición del riesgo, (2) perfil de activos críticos, (3) identificación de contenedores, (4) áreas de preocupación, (5) escenarios de amenaza, (6) consecuencias, (7) análisis del riesgo relativo y (8) enfoque de mitigación."),
    ...table("Paso 1: prioridad de las áreas de impacto", ["Área de impacto", "Prioridad (6 = más importante)"], [
      ["Académico", "6"], ["Reputación y confianza", "5"], ["Legal y regulatorio", "4"], ["Financiero", "3"], ["Productividad y operación", "2"], ["Seguridad y salud", "1"],
    ], [70, 30], { center: [1] }),
    ...table("Pasos 2 y 3: activos críticos de información y contenedores", ["ID", "Activo de información", "Contenedores técnicos", "Requisito principal", "Propietario"], [
      ["IA-01", "Expedientes y gestión académica", "API, PostgreSQL académico, respaldos", "Integridad", "Dirección Académica"],
      ["IA-02", "Identidades, credenciales y roles", "Keycloak, BD de identidad, secretos, certificado TLS", "Confidencialidad", "Seguridad TI"],
      ["IA-03", "Copias de respaldo", "Repositorio local, secretos, repositorio offsite", "Disponibilidad", "TI UVCG"],
      ["IA-04", "Registros y alertas de seguridad", "SIEM, IDS, evidencias", "Integridad", "Seguridad TI"],
      ["IA-05", "Información financiera y de pagos", "Sistema financiero, identidad", "Integridad", "Dirección Financiera"],
    ], [8, 26, 32, 16, 18]),
    ...table("Pasos 5 a 8: escenarios de amenaza, puntaje relativo y enfoque", ["Escenario", "Activo", "Actor y medio", "Puntaje", "Grupo", "Enfoque", "Riesgos"], [
      ["OS-03", "IA-02", "Atacante externo explota vulnerabilidad en imagen", "58", "1", "Mitigar", "R-009, R-010"],
      ["OS-04", "IA-03", "Fallo técnico o ransomware corrompe copias en el mismo host", "57", "1", "Mitigar", "R-007, R-011, R-019"],
      ["OS-07", "IA-01", "Evento físico o ambiental destruye el único host", "57", "1", "Mitigar", "R-004, R-014"],
      ["OS-02", "IA-02", "Atacante externo: credential stuffing contra Keycloak", "52", "1", "Mitigar", "R-002"],
      ["OS-01", "IA-01", "Usuario interno abusa de su rol en la API", "48", "2", "Mitigar", "R-001"],
      ["OS-05", "IA-03", "Insider o robo de equipo obtiene la clave de cifrado", "48", "2", "Mitigar", "R-015"],
      ["OS-08", "IA-05", "Falla o brecha de un proveedor externo", "47", "2", "Transferir", "R-018"],
      ["OS-06", "IA-04", "Atacante evade la detección por falta de agentes", "38", "3", "Diferir / mitigar", "R-012"],
    ], [10, 8, 38, 9, 8, 12, 15], { center: [3, 4], note: "Puntaje = Σ (Alto 3, Medio 2, Bajo 1 por área × prioridad), entre 21 y 63. Grupo 1 ≥ 50; grupo 2 entre 40 y 49; grupo 3 < 40. Fuente: governance/octave-allegro.md." }),
    p("**Resultados.** Los escenarios de mayor puntaje se concentran en las credenciales e identidades (IA-02), las copias de respaldo alojadas en el mismo equipo (IA-03) y la pérdida del sitio (IA-01). OCTAVE confirmó de forma independiente lo que mostró el análisis NIST: los riesgos críticos residuales R-011 (sin sitio alterno ni copia externa) y R-013 (sin MDM/EDR) y la brecha de RPO R-019. Esta convergencia entre dos metodologías da mayor confianza a la priorización. Como limitación, la evaluación no incluyó talleres con los propietarios, por lo que las prioridades del Paso 1 deben validarse."),
  ];
}

function heatTable(title, pKey, iKey, noteText) {
  const grid = {};
  riesgos.forEach((r) => { const k = `${r[pKey]}-${r[iKey]}`; (grid[k] = grid[k] || []).push(r.id); });
  const rows = [];
  for (let i = 5; i >= 1; i--) {
    rows.push([`Impacto ${i}`, ...[1, 2, 3, 4, 5].map((pr) => (grid[`${pr}-${i}`] || []).join(", ") || "—")]);
  }
  return table(title, ["Impacto \\ Probabilidad", "1", "2", "3", "4", "5"], rows, [16, 17, 17, 17, 17, 16], {
    size: 16, center: [1, 2, 3, 4, 5],
    fillFn: (v, col, row) => {
      if (col === 0) return "F2F2F2";
      const imp = Number(row[0].split(" ")[1]);
      return FILL[nivel(col * imp)];
    },
    note: noteText,
  });
}

function calor() {
  return [
    h2("4.9 Matriz de calor"),
    p("La matriz de calor ubica cada riesgo según su probabilidad (columnas) e impacto (filas). Los colores siguen los criterios de la sección 4.7: verde para Bajo (1–4), amarillo para Moderado (5–9), naranja para Alto (10–15) y rojo para Crítico (16–25). Se presentan dos matrices para visualizar el efecto de los controles: la del riesgo inherente y la del residual."),
    ...heatTable("Matriz de calor del riesgo inherente", "probabilidad_1_5", "impacto_1_5", "Cada celda lista los riesgos con esa combinación de probabilidad e impacto."),
    ...heatTable("Matriz de calor del riesgo residual", "probabilidad_residual_1_5", "impacto_residual_1_5", "Los riesgos se desplazan hacia la zona verde-amarilla cuando los controles son efectivos. R-011 y R-013 permanecen en rojo porque sus controles aún no están implementados."),
    p("La comparación muestra que los controles implementados en el laboratorio —MFA, RBAC, segmentación, respaldos cifrados con restauración probada, imagen endurecida de PostgreSQL— redujeron la mayoría de los riesgos a niveles moderados. Los que no se movieron dependen de inversiones aún no realizadas: la copia fuera del sitio y el sitio alterno (R-011, R-014), y la protección de dispositivos con MDM/EDR (R-013). Esto orienta la prioridad del plan de tratamiento."),
  ];
}

function tratamientoSec() {
  const est = contar(tratamiento, (t) => t.estrategia);
  return [
    h2("4.10 Plan de tratamiento de riesgos"),
    p(`Cada riesgo recibió una estrategia (${Object.entries(est).map(([k, v]) => `${k}: ${v}`).join("; ")}), un control de ISO/IEC 27001/27002:2022, un responsable, una prioridad, un plazo, un estado y el riesgo residual esperado tras completar el tratamiento. Se eligió **mitigar** cuando existía un control técnico viable; **transferir** cuando el riesgo depende de terceros o de eventos físicos asegurables (R-014, R-018); **evitar** para el riesgo de configuración cloud insegura, no desplegando hasta revisar el plan y los costos (R-017), y **aceptar** parcialmente sólo en R-022, condicionado a la decisión presupuestaria sobre licencias.`),
  ];
}

function tratamientoTabla() {
  return table("Plan de tratamiento de riesgos", ["Riesgo", "Tratamiento", "Control", "Ref. ISO/IEC 27002", "Responsable", "Prioridad", "Plazo", "Estado", "Residual esperado"],
    tratamiento.map((t) => [t.riesgo_id, t.estrategia, t.control_propuesto, t.referencia_iso_27001_27002_2022, t.responsable, t.prioridad, t.plazo_academico, t.estado, t.riesgo_residual_esperado]),
    [6, 9, 25, 12, 10, 7, 9, 12, 10], { landscape: true, size: 14, fillFn: (v, i) => (i === 8 ? fillNivel(v) : undefined),
      note: "Fuente: governance/plan-tratamiento.csv. Los plazos son académicos y parten de la aprobación del plan." });
}

function politicas() {
  const pol = (titulo, items) => [h3(titulo), ...items.map((t) => bullet(t))];
  return [
    h2("4.11 Políticas de seguridad"),
    p("Las políticas se organizan en una política general aprobada por la Rectoría y políticas específicas por dominio. Cada una indica qué parte se ejecuta en el laboratorio y qué parte es normativa propuesta. Las políticas son de cumplimiento obligatorio para todo el personal, estudiantes y terceros dentro del alcance; su incumplimiento se trata conforme al reglamento disciplinario. Se revisan una vez al año o tras un cambio significativo."),
    ...pol("4.11.1 Dominio e identidad", [
      "**Administración de identidades:** toda identidad se crea a partir de una fuente autorizada (Registro Académico para estudiantes, RR. HH. para personal) y se desactiva automáticamente al terminar la relación. No existen cuentas compartidas. *Laboratorio:* realm `uvcg` de Keycloak con cuatro usuarios nominales y solicitudes de acceso registradas (ACC-001 denegada por mínimo privilegio, ACC-002 aprobada).",
      "**Autenticación:** el acceso a cualquier sistema con información interna o superior se realiza mediante el proveedor de identidad central con OIDC. Las aplicaciones no almacenan contraseñas propias. *Laboratorio:* la API valida firma (JWKS), emisor, expiración y cliente en cada solicitud.",
      "**Autorización:** se basa en roles (RBAC) aprobados por el propietario de la información y revisados trimestralmente. *Laboratorio:* matriz de cuatro roles verificada con respuestas 200/401/403.",
      "**MFA:** obligatoria para el 100 % del personal, administradores y accesos remotos; recomendada y progresivamente obligatoria para estudiantes. *Laboratorio:* TOTP obligatorio para todos los usuarios; el inicio de sesión sin segundo factor es rechazado.",
      "**Privilegios:** las cuentas administrativas son distintas de las de uso diario, se usan desde estaciones de gestión dedicadas y requieren doble control para cambios críticos. Se registran todas sus acciones.",
    ]),
    ...pol("4.11.2 Grupos", [
      "**Administradores:** grupo restringido (máximo 8 personas), MFA con factor resistente a phishing cuando esté disponible, acceso sólo desde la VLAN de gestión o el bastión, revisión mensual de membresía y de eventos administrativos.",
      "**Usuarios (estudiantes):** acceso a portal, LMS y consultas propias; sin acceso a datos de otros estudiantes; sesión con expiración; acceso desde BYOD sólo por navegador o aplicación gestionada.",
      "**Personal académico (docentes):** acceso a cursos asignados y registro de calificaciones; los cambios de notas fuera de plazo requieren aprobación de la coordinación y quedan registrados. *Laboratorio:* el rol docente accede a `/docencia` y no a `/administracion`.",
      "**Personal administrativo:** acceso por función (matrícula, finanzas, RR. HH.) con segregación de funciones: quien registra un pago no lo concilia.",
      "**Terceros:** acceso sólo con contrato que incluya cláusulas de confidencialidad y seguridad, cuenta nominal temporal con fecha de expiración, MFA, alcance mínimo y supervisión; se revoca al terminar el servicio.",
    ]),
    ...pol("4.11.3 Equipos", [
      "**Hardening:** todo servidor, contenedor y estación se configura según una línea base aprobada (CIS Benchmarks como referencia). *Laboratorio:* contenedores con sistema de archivos de sólo lectura, sin usuario root, sin capacidades (`cap_drop: ALL`) y `no-new-privileges`; línea base de configuración con verificación SHA-256 de 22 archivos.",
      "**Gestión de parches:** vulnerabilidades críticas con corrección disponible se corrigen en 15 días; altas en 30 días; el resto en el ciclo mensual. Las imágenes se escanean mensualmente. *Laboratorio:* Trivy sobre imágenes en uso; la imagen de PostgreSQL se reconstruyó sin el componente vulnerable `gosu` (de 1 crítica y 25 altas a 0).",
      "**EDR:** todo equipo institucional con sistema operativo soportado debe tener un agente EDR activo y reportando a la consola central. *Laboratorio:* vigilancia de procesos y deriva en contenedores; el EDR en estaciones es una brecha registrada (R-013).",
      "**Cifrado:** discos de portátiles y móviles institucionales cifrados (BitLocker, FileVault, cifrado nativo); información confidencial cifrada en tránsito (TLS 1.2+) y en reposo; respaldos con AES-256.",
      "**Control de aplicaciones:** sólo se instala software autorizado desde el catálogo institucional; las estaciones administrativas aplican listas de aplicaciones permitidas.",
    ]),
    ...pol("4.11.4 Usuarios", [
      "**Contraseñas:** mínimo 12 caracteres con mayúscula, minúscula, número y carácter especial; no reutilizar las últimas 5; bloqueo temporal ante intentos repetidos. *Laboratorio:* política aplicada en Keycloak `length(12) and digits(1) and lowerCase(1) and upperCase(1) and specialChars(1) and passwordHistory(5)`.",
      "**MFA:** el usuario es responsable de proteger su segundo factor y de reportar su pérdida a la mesa de servicio de inmediato.",
      "**Mínimo privilegio:** cada usuario recibe sólo los permisos necesarios para su función; los accesos adicionales se solicitan, se justifican y se aprueban (registro ACC).",
      "**Acceso remoto:** sólo mediante el portal con OIDC y MFA o VPN institucional; prohibido exponer servicios internos directamente a Internet. *Laboratorio:* el proxy publica únicamente en la interfaz local.",
      "**Uso aceptable:** los recursos tecnológicos se usan para fines académicos y administrativos; está prohibido compartir credenciales, instalar software no autorizado, extraer información confidencial a servicios personales y eludir controles de seguridad.",
    ]),
    ...pol("4.11.5 Nube", [
      "**Control de acceso:** no se usa el usuario raíz de AWS para operar; el acceso se realiza con identidades con MFA y roles con credenciales temporales (STS). No se crean claves de acceso permanentes. *Preparado:* roles `uploader` y `auditor` con políticas de mínimo privilegio y denegaciones explícitas.",
      "**Configuración segura:** toda la infraestructura cloud se define como código, se valida (Terraform validate, TFLint, Trivy) y pasa por una compuerta de revisión del plan antes de aplicarse. Los buckets bloquean el acceso público, exigen TLS 1.2+ y cifran en reposo.",
      "**Segmentación:** cargas separadas en subredes públicas, de aplicación y de datos, con grupos de seguridad de mínimo acceso y sin IP públicas en las capas internas.",
      "**Registro:** CloudTrail habilitado en todas las regiones usadas; los registros se conservan al menos 90 días y se integran al SIEM.",
      "**Monitoreo:** presupuesto con alerta de gasto, revisión de hallazgos de GuardDuty y Security Hub (diseño) y prueba de configuración después de cada despliegue.",
    ]),
    ...pol("4.11.6 Dispositivos móviles", [
      "**MDM:** los dispositivos que accedan a información interna o superior deben inscribirse en la plataforma MDM institucional y cumplir la política de cumplimiento; los no conformes sólo acceden a información pública. *Laboratorio:* simulación de evaluación de cumplimiento con 5 dispositivos ficticios (3 conformes, 2 no conformes con acceso restringido).",
      "**DLP:** la información confidencial o restringida no puede copiarse a aplicaciones personales ni transferirse por canales externos no aprobados. *Laboratorio:* compuerta DLP que bloquea credenciales, números de tarjeta y documentos de identificación ficticios.",
      "**Cifrado:** obligatorio en todo dispositivo inscrito; el MDM verifica su estado.",
      "**Bloqueo:** bloqueo automático tras 5 minutos de inactividad con PIN de al menos 6 dígitos o biometría.",
      "**Borrado remoto:** completo para dispositivos institucionales extraviados; selectivo (sólo el contenedor institucional) para BYOD, preservando los datos personales del usuario.",
      "**BYOD:** se permite con perfil de trabajo separado, sistema operativo soportado, sin root/jailbreak y aceptación firmada de la política; la universidad no accede a los datos personales del dispositivo.",
    ]),
    h3("4.11.7 Gestión de incidentes"),
    p("Todo evento de seguridad se reporta a la mesa de servicio o al Oficial de Seguridad. El procedimiento (`policies/procedimiento-investigacion-incidentes.md`) sigue siete pasos: registrar, validar, clasificar, contener, preservar evidencia, erradicar y recuperar, y cerrar con lecciones aprendidas. Los incidentes de severidad alta o crítica se escalan al propietario del servicio y al Coordinador de Continuidad; la exposición de datos personales activa a Asesoría Legal para evaluar notificaciones."),
  ];
}

function matrizControles() {
  // Matriz control → riesgos a partir del plan de tratamiento (cada control queda ligado al riesgo que trata).
  const map = {};
  tratamiento.forEach((t) => {
    t.referencia_iso_27001_27002_2022.split(/;\s*/).filter((c) => /^A\.\d/.test(c)).forEach((c) => {
      (map[c] = map[c] || new Set()).add(t.riesgo_id);
    });
  });
  const orden = (c) => c.replace("A.", "").split(".").map(Number);
  const ids = Object.keys(map).sort((a, b) => { const x = orden(a), y = orden(b); return x[0] - y[0] || x[1] - y[1]; });
  const filas = ids.map((c) => {
    const s = soaById[c] || {};
    return [c, s.control_name || "", [...map[c]].join(", "), s.implementation_status || "", (s.evidence || "").split(";")[0]];
  });
  const csf = [
    ["Gobernar (GV)", "Contexto, roles, política, gestión de riesgos de la cadena de suministro", "Alcance, partes interesadas, políticas, RACI, COBIT EDM03/APO12", "1 Parcial", "3 Repetible"],
    ["Identificar (ID)", "Inventario, evaluación de riesgos, mejora", "33 activos, BIA, 22 riesgos, OCTAVE", "2 Informado", "3 Repetible"],
    ["Proteger (PR)", "Identidad y acceso, concienciación, datos, plataformas, resiliencia", "OIDC, MFA, RBAC, TLS, cifrado, endurecimiento, DLP", "2 Informado", "3 Repetible"],
    ["Detectar (DE)", "Monitoreo continuo, análisis de eventos adversos", "SIEM ligero (11 reglas), IDS, monitor de disponibilidad, vigilancia de contenedores", "2 Informado", "3 Repetible"],
    ["Responder (RS)", "Gestión, análisis, mitigación y comunicación de incidentes", "Procedimiento, registro INC con auditoría encadenada", "1 Parcial", "3 Repetible"],
    ["Recuperar (RC)", "Ejecución del plan de recuperación y comunicación", "DRP, restauración aislada semanal, PITR", "2 Informado", "3 Repetible"],
  ];
  return [
    h2("4.12 Matriz de controles"),
    p(`La declaración de aplicabilidad evalúa los 93 controles del Anexo A de ISO/IEC 27001:2022: ${nImpl} implementados o validados en el laboratorio, ${nParc} parciales o preparados y ${nPend} pendientes de implementación institucional (Anexo C). No se excluyó ningún control porque el alcance es una universidad completa. La Tabla ${L.nextTable()} presenta la **matriz de controles seleccionados en el tratamiento**, en la que cada control queda relacionado con el riesgo que pretende tratar, tal como exige el enunciado.`),
    ...table("Matriz de controles seleccionados y riesgos tratados", ["Control", "Nombre (ISO/IEC 27002:2022)", "Riesgos tratados", "Estado", "Evidencia principal"], filas,
      [8, 30, 16, 20, 26], { size: 15, note: "Construida a partir de governance/plan-tratamiento.csv y governance/declaracion-aplicabilidad.csv." }),
    h3("4.12.1 Perfil NIST CSF 2.0"),
    p("Para comunicar el estado de la ciberseguridad a la Dirección se elaboró un perfil actual y objetivo según las seis funciones del NIST Cybersecurity Framework 2.0, usando sus niveles de implementación (1 Parcial, 2 Informado por el riesgo, 3 Repetible, 4 Adaptativo)."),
    ...table("Perfil actual y objetivo según NIST CSF 2.0", ["Función", "Resultados considerados", "Implementación en la UVCG", "Nivel actual", "Nivel objetivo (12 meses)"], csf, [14, 26, 34, 13, 13]),
  ];
}

function buenasPracticas() {
  const bp = [
    ["Identidad", "MFA para todos los accesos privilegiados y remotos; SSO con OIDC; eliminación de cuentas compartidas; revisión trimestral de roles."],
    ["Red", "Denegar por defecto; exponer sólo la DMZ; separar datos e identidad en redes sin salida; inspeccionar tráfico con IDS/IPS."],
    ["Aplicaciones", "Validar tokens en cada solicitud; restringir métodos HTTP; cabeceras de seguridad (HSTS, CSP, X-Frame-Options); registrar decisiones de acceso sin registrar secretos."],
    ["Contenedores", "Imágenes mínimas y escaneadas; usuario no root; sistema de archivos de sólo lectura; sin capacidades; límites de memoria; sin red del host (NIST SP 800-190)."],
    ["Datos", "Clasificar en cuatro niveles; cifrar en tránsito y en reposo; DLP en los canales de salida; datos sintéticos en pruebas."],
    ["Respaldo", "Regla 3-2-1-1-0: tres copias, dos medios, una fuera del sitio, una inmutable y cero errores en la verificación; restaurar en entorno aislado; nunca sobre la base activa."],
    ["Monitoreo", "Centralizar registros con marca de tiempo UTC; sellar la integridad de los eventos; reglas con umbral y ventana; probar cada regla con un evento real o controlado."],
    ["Cambios", "Registrar cada cambio con riesgo, plan de reversión y aprobación; tomar línea base de configuración antes y después; probar la reversión."],
    ["Nube", "No usar el usuario raíz; credenciales temporales; infraestructura como código revisada; presupuesto con alertas; retirar recursos al terminar."],
    ["Móviles", "Inscripción en MDM antes de acceder a información sensible; perfil de trabajo en BYOD; borrado selectivo; acceso condicional según cumplimiento."],
    ["Personas", "Capacitación anual y simulacros de phishing; acuerdos de confidencialidad; proceso de baja que revoca accesos el mismo día."],
    ["Continuidad", "Probar la recuperación con periodicidad definida y comparar el tiempo observado con el RTO; documentar lecciones aprendidas."],
  ];
  return [
    h2("4.13 Buenas prácticas de seguridad"),
    p("El documento de buenas prácticas (E5.3) recoge las prácticas que el grupo aplicó en el laboratorio o que recomienda para la operación institucional. Se derivan de ISO/IEC 27002, de las guías de NIST y de las lecciones aprendidas durante la construcción (por ejemplo, el incidente INC-008 llevó a tratar explícitamente la salida de error de Docker en los scripts de PowerShell)."),
    ...table("Buenas prácticas por dominio", ["Dominio", "Práctica"], bp, [16, 84]),
  ];
}

function zeroTrust() {
  return [
    h2("4.14 Zero Trust"),
    p("La arquitectura aplica los principios de NIST SP 800-207: ninguna solicitud se considera confiable por provenir de la red interna; cada acceso a un recurso se autoriza de forma individual según la identidad, el rol y el contexto. La Tabla " + L.nextTable() + " muestra cómo se materializó cada principio."),
    ...table("Principios de Zero Trust (NIST SP 800-207) y su implementación", ["Principio", "Implementación", "Estado"], [
      ["Todos los datos y servicios son recursos", "API, identidad y bases de datos se protegen individualmente", "Implementado"],
      ["Comunicación segura independientemente de la ubicación", "TLS en el perímetro; las redes internas no otorgan acceso sin token", "Implementado"],
      ["Acceso por sesión", "Tokens OIDC de corta duración validados en cada solicitud", "Implementado"],
      ["Política dinámica (identidad, dispositivo, contexto)", "Identidad + MFA + rol; la postura del dispositivo depende de MDM", "Parcial"],
      ["Monitoreo de la integridad y postura de los activos", "Vigilancia de contenedores, línea base de configuración, escaneo de vulnerabilidades", "Implementado (lab)"],
      ["Autenticación y autorización estrictas antes de cada acceso", "Firma JWKS, emisor, expiración, cliente y rol", "Implementado"],
      ["Recolección de información para mejorar la postura", "SIEM con eventos de acceso permitidos y denegados", "Implementado"],
    ], [32, 50, 18]),
    ...table("Matriz de acceso por recurso y rol", ["Recurso", "Administrador", "Docente", "Estudiante", "Administrativo", "Sin token o token inválido"], [
      ["GET /health", "Permitir", "Permitir", "Permitir", "Permitir", "Permitir (sin datos sensibles)"],
      ["GET /cursos", "Permitir", "Permitir", "Permitir", "Permitir", "Denegar 401"],
      ["GET /perfil", "Permitir", "Permitir", "Permitir", "Permitir", "Denegar 401"],
      ["GET /docencia", "Permitir", "Permitir", "Denegar 403", "Denegar 403", "Denegar 401"],
      ["GET /administracion", "Permitir", "Denegar 403", "Denegar 403", "Denegar 403", "Denegar 401"],
      ["Métodos de escritura", "Denegar 403", "Denegar 403", "Denegar 403", "Denegar 403", "Denegar 403"],
    ], [20, 15, 14, 14, 15, 22], { size: 16, fillFn: (v, i) => (i > 0 ? (String(v).startsWith("Permitir") ? "E2F0D9" : "FBE5D6") : undefined),
      note: "Verificada por scripts/pruebas_identidad.py en cada validación integral." }),
    p("En la nube, Zero Trust se aplica mediante roles de IAM con credenciales temporales en lugar de claves permanentes, políticas de bucket que niegan cualquier escritura que no provenga del rol autorizado y conexiones sin TLS 1.2, y la ausencia de IP públicas en las capas internas de la VPC. El componente pendiente es el **acceso condicional por postura de dispositivo**, que requiere integrar el MDM con el proveedor de identidad."),
  ];
}

function mdmDlp() {
  return [
    h2("4.15 MDM y DLP"),
    p("**Clasificación de la información.** La DLP parte de cuatro niveles: Pública (catálogo de cursos), Interna (procedimientos), Confidencial (expedientes) y Restringida (credenciales y datos financieros). El tratamiento mínimo de cada nivel define qué canal de transferencia está permitido."),
    p("**DLP implementada.** La compuerta `scripts/dlp_compuerta.py` inspecciona archivos antes de su transferencia, detecta etiquetas de clasificación, credenciales, números de tarjeta (con validación de Luhn) y números de documento de identificación ficticios, y decide permitir o bloquear según el canal. Cada bloqueo genera un incidente en el registro operativo (INC-001 a INC-006, de ejercicio). La Tabla " + L.nextTable() + " muestra el resultado de la última ejecución."),
    ...table("Resultado de la compuerta DLP hacia un canal externo", ["Archivo (sintético)", "Clasificación", "Detección", "Decisión"], [
      ["confidencial-ficticio.txt", "Confidencial", "—", "Bloqueado"],
      ["credencial-ficticia.txt", "Interna", "Credencial", "Bloqueado"],
      ["restringido-ficticio.txt", "Restringida", "Documento de identificación", "Bloqueado"],
      ["tarjeta-ficticia.txt", "Interna", "Número de tarjeta de pago", "Bloqueado"],
      ["publico.txt", "Pública", "—", "Permitido"],
    ], [34, 20, 28, 18], { fillFn: (v, i) => (i === 3 ? (v === "Permitido" ? "E2F0D9" : "FBE5D6") : undefined),
      note: "Evidencia: evidencias/dlp/compuerta-externo-20261107-111229.json." }),
    p("**MDM.** No se dispuso de una plataforma MDM con licencia, por lo que se implementó una **simulación** declarada como tal: `scripts/mdm_cumplimiento.py` evalúa un inventario de cinco dispositivos ficticios contra la política UVCG-BYOD-Cumplimiento-v1 (cifrado, bloqueo de pantalla, longitud del PIN, versión mínima del sistema operativo, antimalware, ausencia de root o jailbreak, borrado selectivo y perfil de trabajo) y decide el nivel de acceso permitido. Resultado: 3 dispositivos conformes con acceso completo con MFA y 2 no conformes, restringidos a información pública o navegación sin descargas."),
    p("**Arquitectura objetivo.** En producción, la UVCG adoptaría una plataforma MDM (por ejemplo, Microsoft Intune, que la universidad podría obtener con licenciamiento académico, o una alternativa de código abierto) integrada con el proveedor de identidad para acceso condicional, y DLP en el correo, los puntos finales y el almacenamiento en la nube. El riesgo residual R-013 (crítico) permanecerá hasta que esa plataforma opere."),
  ];
}

function siem() {
  return [
    h2("4.16 SIEM, EDR y XDR"),
    p("**SIEM.** Se evaluaron Wazuh y OpenSearch, pero ambos requieren más memoria de la disponible junto con los servicios del laboratorio (Wazuh recomienda al menos 8 GB para una instalación todo en uno). Se construyó un **SIEM ligero** propio, proporcional al hardware y auditable: recolecta registros de 12 fuentes (proxy, API, Keycloak, ambas bases de datos, respaldos, IDS, monitor de disponibilidad, DLP y vigilancia de contenedores), los normaliza con hora UTC, redacta tokens y contraseñas, calcula un hash SHA-256 por evento, los almacena en SQLite y sella los lotes en cadena para detectar alteraciones."),
    ...table("Reglas de correlación del SIEM y prueba que las disparó", ["Regla", "Detecta", "Umbral / ventana", "Prueba"], [
      ["SIEM-AUTH-001", "Ráfaga de autenticaciones fallidas", "3 en 300 s", "Credenciales y TOTP inválidos reales"],
      ["SIEM-RBAC-001", "Acceso denegado por rol", "1 en 300 s", "Rol insuficiente en /administracion"],
      ["SIEM-HTTP-001", "Ráfaga de respuestas 401/403", "5 en 120 s", "Solicitudes sin token"],
      ["SIEM-DB-001", "Fallo de autenticación en PostgreSQL", "1 en 300 s", "Conexión con usuario sintético inexistente"],
      ["SIEM-IDS-001", "Alerta de Suricata", "1 en 300 s", "Ingesta de eve.json"],
      ["SIEM-BACKUP-001", "Fallo de respaldo o restauración", "1 en 300 s", "Respaldo dirigido a host inexistente; fallo real de restauración"],
      ["SIEM-WAL-001", "Fallo de archivado WAL", "1 en 300 s", "Fallo inyectado en réplica"],
      ["SIEM-CFG-001", "Modificación no autorizada de configuración", "1 en 300 s", "Autoprueba de integridad"],
      ["SIEM-AVAIL-001", "Indisponibilidad del servicio", "1 en 300 s", "Interrupción controlada de la API"],
      ["SIEM-EDR-001", "Proceso inesperado en contenedor", "1 en 300 s", "Proceso `sleep` en la API"],
      ["SIEM-DLP-001", "Transferencia bloqueada por DLP", "1 en 300 s", "Archivos sintéticos clasificados"],
    ], [18, 34, 16, 32], { size: 16 }),
    p("**EDR.** En lugar de un agente comercial, se implementó una **vigilancia de contenedores** que compara los procesos en ejecución con una lista esperada, detecta deriva del sistema de archivos y verifica el endurecimiento de cada servicio. En la prueba, la introducción de un proceso no autorizado en la API se detectó y el intento de escritura fue bloqueado por el sistema de archivos de sólo lectura. Esta capacidad cubre los servidores contenedorizados, no las estaciones de los usuarios, que son la brecha R-013."),
    p("**XDR.** La arquitectura objetivo integra la telemetría de puntos finales (EDR), red (IDS/NGFW), identidad (Keycloak) y nube (CloudTrail, GuardDuty) en una plataforma de detección extendida que correlacione entre dominios y automatice respuestas. En el estado actual, el SIEM ligero ya correlaciona identidad, red y aplicación, lo que constituye la base de esa integración."),
    p("**Respuesta a incidentes.** El registro operativo (`evidencias/gestion/registro-sgsi.db`) contiene 13 incidentes, 8 cambios, 2 solicitudes de acceso y 4 eventos de activos, con una bitácora de auditoría encadenada por hash. Siete incidentes son reales —por ejemplo, INC-007 (copia antigua sin cifrar), INC-010 (permisos amplios del archivo de secretos), INC-011 (bases sin archivado WAL) e INC-013 (región de AWS bloqueada por la organización)— y seis son ejercicios de DLP rotulados como tales."),
  ];
}

function implementacion() {
  return [
    h2("4.17 Implementación tecnológica"),
    h3("4.17.1 Descripción de la implementación"),
    p("El ambiente se implementó como un laboratorio reproducible definido en `local/compose.yaml`. Cinco servicios permanentes —proxy, API, Keycloak y dos bases de datos— más los programadores de respaldo y el monitor de disponibilidad se ejecutan en redes Docker segmentadas; los servicios de restauración, PITR, IDS y escaneo se levantan bajo demanda mediante perfiles. Los secretos se generan localmente en un archivo `.env` excluido del control de versiones. La infraestructura de AWS se definió en `aws/` con tres módulos de Terraform."),
    ...table("Diferenciación entre componentes implementados, preparados y diseñados", ["Categoría", "Componentes"], [
      ["Implementado y probado", "Proxy TLS, API con RBAC, Keycloak con OIDC/MFA, 2 PostgreSQL endurecidos, 5 redes segmentadas, respaldos cifrados programados, restauración aislada semanal, PITR en réplicas, SIEM ligero, IDS offline, vigilancia de contenedores, compuerta DLP, integridad de configuración, registro operativo, escaneo de vulnerabilidades"],
      ["Parcial", "Zero Trust (sin postura de dispositivo), SIEM (ingesta por lotes), DLP (sin endpoint ni correo), certificados (autofirmados), gestión de secretos (permisos amplios del archivo, INC-010)"],
      ["Implementado en AWS", "Bucket S3 privado con cifrado, bloqueo público, TLS ≥ 1.2 y expiración; roles IAM uploader y auditor; presupuesto de gasto cero; compuerta de costo del plan; 13/13 pruebas posteriores al despliegue; procedimiento de retirada preparado"],
      ["Simulado (declarado)", "Cumplimiento MDM con dispositivos ficticios; retención de respaldos en modo de simulación"],
      ["Diseñado", "NGFW, VLAN físicas, VPN Site-to-Site, VPC multi-AZ, RDS, WAF, GuardDuty, Security Hub, copia inmutable, MDM y EDR comerciales, infraestructura física TIA-942"],
    ], [20, 80]),
    h3("4.17.2 Servicios implementados y controles configurados"),
    ...table("Servicios del laboratorio", ["Servicio", "Imagen", "Red(es)", "Exposición", "Controles configurados"], [
      ["proxy", "local-proxy (Nginx)", "dmz, apps", "127.0.0.1:8080/8443", "TLS 1.2/1.3, HSTS, CSP, sólo GET/HEAD, redirección HTTP→HTTPS"],
      ["api", "local-api (Flask/Gunicorn)", "apps, datos", "Ninguna", "Validación JWT por JWKS, RBAC por ruta, eventos JSON sin secretos"],
      ["keycloak", "local-keycloak 26.8.1", "apps, identity", "Sólo vía proxy", "Realm uvcg, TOTP obligatorio, política de contraseñas, eventos de inicio de sesión"],
      ["db", "local-postgres-hardened:16", "datos (interna)", "Ninguna", "Sin gosu, UID 70, sólo lectura, autenticación SCRAM"],
      ["identity-db", "local-postgres-hardened:16", "identity (interna)", "Ninguna", "Base separada para identidad"],
      ["backup-schedulers (2)", "local-backup-tool", "datos / identity", "Ninguna", "Copia diaria AES-256 + SHA-256, bitácora de ejecución"],
      ["uptime-monitor", "local-api", "dmz", "Ninguna", "Sondeo de disponibilidad cada 15 s"],
    ], [16, 20, 14, 14, 36], { size: 16, note: "Todos los servicios usan read_only, cap_drop ALL, no-new-privileges, usuario no root y límites de memoria." }),
    h3("4.17.3 Pruebas realizadas y resultados"),
    ...table("Pruebas de la validación integral", ["Control probado", "Prueba", "Resultado esperado", "Resultado observado", "Estado"], [
      ["HTTPS y perímetro", "pruebas_locales.py", "HTTP→HTTPS, 401 sin token, 403 en métodos no permitidos", "Conforme", "Exitoso"],
      ["IAM, MFA y RBAC", "pruebas_identidad.py", "MFA exigido; matriz 200/401/403 de 4 roles", "Conforme; eventos LOGIN/LOGIN_ERROR registrados", "Exitoso"],
      ["Segmentación", "validar_segmentacion.ps1", "Sólo el proxy publica; proxy no alcanza la base", "api→db permitido; proxy→db y db→proxy bloqueados", "Exitoso"],
      ["IDS", "Suricata sobre PCAP sintético", "7 detecciones; 0 en tráfico benigno", "7 verdaderos positivos, 0 falsos positivos", "Exitoso"],
      ["SIEM integrado", "siem_pipeline.py", "Reglas disparadas por eventos reales; 0 secretos", "12 fuentes, 10 reglas disparadas, 0 secretos", "Exitoso"],
      ["Respaldo y restauración", "restaurar_prueba.ps1", "SHA-256 válido; datos íntegros; sin tocar la base activa", "Académica 8.5 s (3 cursos); identidad 9.1 s (5 identidades)", "Exitoso"],
      ["PITR", "pitr_prueba.py", "Recuperación exacta al punto objetivo", "RTO ≈ 2.1 s; RPO observado ≈ 56 s", "Exitoso (réplicas)"],
      ["Continuidad API", "prueba_continuidad.ps1", "Recuperación automática dentro del RTO", "12.0 s; integridad preservada", "Exitoso"],
      ["Continuidad IAM", "prueba_continuidad.ps1", "Recuperación dentro de 2 h", "70.2 s", "Exitoso"],
      ["Vigilancia de contenedores", "vigilancia_contenedores.py", "Detección de proceso no autorizado", "Proceso detectado; escritura bloqueada", "Exitoso"],
      ["Integridad de configuración", "integridad_configuracion.py --self-test", "Detectar y restaurar un cambio", "Detección y restauración correctas", "Exitoso"],
      ["Vulnerabilidades", "Trivy sobre imágenes en uso", "0 críticas con corrección disponible", "PostgreSQL 0/0; Keycloak 2 altas sin corrección publicada", "Exitoso con excepción R-010"],
      ["DLP", "dlp_compuerta.py", "Bloquear confidencial y restringida hacia externo", "4 bloqueos, 1 permitido", "Exitoso"],
      ["Trazabilidad de gobierno", "validar_trazabilidad.py", "21 reglas de coherencia", "21/21", "Exitoso"],
      ["PITR en bases principales", "validar_sgsi.ps1", "archive_mode activo", "archive_mode=off (pendiente de autorización)", "No verificable"],
      ["AWS (nube)", "pruebas_aws.ps1", "Controles de S3 e IAM efectivos en la cuenta real", "13/13 pruebas exitosas", "Exitoso"],
    ], [16, 18, 22, 28, 16], { size: 15, fillFn: (v, i) => (i === 4 ? (String(v).startsWith("Exitoso") ? "E2F0D9" : "FFF2CC") : undefined),
      note: "Última corrida completa: evidencias/automatizacion/validacion-sgsi-20261024-112033.json (27 exitosos, 1 fallido por reestructuración de la IaC, 1 no verificable). Corrida del 7 de noviembre de 2026: 20 exitosos, 1 fallido (tarea programada interrumpida mientras el equipo estaba apagado), 5 omitidos por diseño, 1 no verificable." }),
    h3("4.17.4 Componente AWS"),
    p("La cuenta de AWS de la universidad (identificador `0054****4685`, plan FREE activo con 120 USD de crédito) se administra con el inicio de sesión de la consola y credenciales temporales: no se crearon usuarios IAM ni claves de acceso permanentes. Antes de crear recursos se verificó la identidad y el estado del plan, y el plan de Terraform pasó por una compuerta que sólo admite los recursos previstos y ninguna destrucción."),
    p("**Hallazgo durante el despliegue (INC-013).** El primer intento en us-east-1 creó los recursos globales (roles IAM y presupuesto), pero la creación del bucket fue rechazada por una política de control de servicios (SCP) de la organización que administra la cuenta, que sólo habilita la región us-east-2. Mediante consultas de sólo lectura se confirmó la restricción, se cambió la región, se generó un nuevo plan (6 recursos creados, 2 actualizados, 0 eliminados) y se aplicó tras revisarlo. El incidente se registró y cerró con su lección aprendida, y el despliegue quedó documentado como el cambio CHG-007. Este episodio demostró en la práctica un control preventivo de la nube (las SCP) actuando sobre la propia universidad."),
    ...table("Pruebas reales del componente AWS después del despliegue", ["Prueba", "Control verificado", "Resultado"], [
      ["PT-AWS-01", "El bucket existe en us-east-2", "Exitoso"],
      ["PT-AWS-02", "Bloqueo de acceso público en sus cuatro opciones", "Exitoso"],
      ["PT-AWS-03", "Cifrado predeterminado SSE-S3 (AES-256)", "Exitoso"],
      ["PT-AWS-04", "Carga por HTTPS con el rol uploader y credenciales temporales STS", "Exitoso"],
      ["PT-AWS-05", "Integridad SHA-256 del archivo descargado y cifrado en reposo", "Exitoso"],
      ["PT-AWS-06", "Carga fuera del prefijo laboratorio/ denegada", "Exitoso"],
      ["PT-AWS-07", "Borrado denegado al rol de carga", "Exitoso"],
      ["PT-AWS-08", "Transporte sin TLS denegado por la política del bucket", "Exitoso"],
      ["PT-AWS-09", "El rol auditor no puede leer objetos", "Exitoso"],
      ["PT-AWS-10", "El rol auditor sí puede leer la configuración", "Exitoso"],
      ["PT-AWS-11", "Acceso anónimo denegado (HTTP 403)", "Exitoso"],
      ["PT-AWS-12", "Eventos AssumeRole registrados en CloudTrail", "Exitoso"],
      ["PT-AWS-13", "La cuenta sigue en plan FREE tras el despliegue", "Exitoso"],
    ], [14, 70, 16], { size: 16, fillFn: (v, i) => (i === 2 ? "E2F0D9" : undefined),
      note: "Ejecutadas el 7 de noviembre de 2026 con aws/scripts/pruebas_aws.ps1: 13 exitosas, 0 fallidas. Una primera corrida tuvo 4 fallos atribuibles al propio script (rutas relativas y endpoint global de S3 que responde 307 fuera de us-east-1); se corrigió el script sin relajar ninguna prueba. Evidencia: evidencias/aws/pruebas-aws-20261107-130835.json, apply-20261107-130521.txt." }),
    p("**Alcance real del componente híbrido.** La integración demostrada es una transferencia cifrada por Internet con identidad temporal y mínimo privilegio; no es una VPN privada entre redes. La VPC multi-AZ, la VPN Site-to-Site, GuardDuty, Security Hub y la copia inmutable con Object Lock permanecen como diseño, porque su costo no está garantizado como cero en el plan gratuito."),
    ...capturePlaceholder("Consola de AWS: bucket S3 con bloqueo de acceso público y cifrado predeterminado", "Pestaña Permisos y Propiedades del bucket uvcg-sgsi-lab-*."),
    ...capturePlaceholder("Consola de IAM: roles uploader y auditor con sus políticas", "Lista de roles y política en línea de cada uno."),
    ...figure("Inicio de sesión con MFA en Keycloak (realm uvcg, usuario docente.lab)", "documento/figuras/keycloak-mfa.png",
      "Capturas reales del laboratorio en ejecución tomadas el 7 de noviembre de 2026 con documento/capturar_keycloak.py (Chrome automatizado); sólo se recortaron alrededor del formulario. La contraseña se muestra enmascarada y no se capturó ningún código válido. El rechazo por rol insuficiente (403) se verifica con scripts/pruebas_identidad.py (Tabla de pruebas de la validación integral)."),
  ];
}

function continuidad() {
  return [
    h2("4.18 Continuidad y recuperación"),
    p("El plan de continuidad (BCP) y el plan de recuperación ante desastres (DRP) se derivan del BIA siguiendo ISO 22301. La **estrategia de continuidad** combina recuperación técnica rápida en el sitio principal, alternativas manuales temporales para cada proceso y una copia inmutable en AWS como base para recuperar ante la pérdida del sitio."),
    ...table("Orden de recuperación y objetivos", ["Orden", "Proceso", "RTO (h)", "RPO (h)", "MTPD (h)", "Alternativa manual temporal"], [
      ["1", "PROC-004 Identidad y autenticación", "2", "0.25", "4", "Ninguna segura sin IAM; se prioriza su recuperación"],
      ["2", "PROC-001 Inscripción y matrícula", "4", "1", "12", "Formulario controlado y carga posterior"],
      ["3", "PROC-003 Aprendizaje virtual", "4", "1", "12", "Materiales por correo institucional"],
      ["4", "PROC-002 Gestión académica", "8", "4", "24", "Congelar cambios de calificaciones"],
      ["5", "PROC-005 Finanzas y pagos", "8", "1", "24", "Registro manual con conciliación posterior"],
      ["6", "PROC-007 Comunicaciones", "8", "4", "24", "Sitio web y mensajería oficial"],
      ["7", "PROC-006 Servicios administrativos", "24", "8", "72", "Diferir trámites no urgentes"],
    ], [8, 30, 9, 9, 10, 34], { size: 16, center: [0, 2, 3, 4] }),
    ...table("Niveles de activación del plan", ["Nivel", "Condición", "Decide"], [
      ["Alerta", "Alerta SIEM alta o crítica, fallo de respaldo o servicio degradado sin impacto confirmado", "Líder de TI"],
      ["Activación parcial", "Proceso crítico indisponible más del 50 % de su RTO o corrupción confirmada de datos", "Coordinador de Continuidad"],
      ["Activación total", "Pérdida del sitio, compromiso de la identidad o proyección de superar el MTPD", "Director de crisis"],
    ], [18, 60, 22]),
    ...table("Roles y responsabilidades (RACI)", ["Actividad", "Director de crisis", "Coord. Continuidad", "Líder TI", "Seguridad", "Propietario", "Comunicación", "Legal"], [
      ["Activar el plan", "A", "R", "C", "C", "I", "I", "I"],
      ["Recuperación técnica (DRP)", "I", "A", "R", "C", "I", "—", "—"],
      ["Contención y evidencia", "I", "I", "C", "R/A", "I", "—", "C"],
      ["Validación funcional", "I", "A", "C", "—", "R", "—", "—"],
      ["Comunicación interna y externa", "A", "C", "—", "C", "C", "R", "C"],
      ["Notificación de brecha de datos", "A", "I", "—", "C", "I", "C", "R"],
    ], [28, 11, 11, 9, 10, 11, 11, 9], { size: 16, center: [1, 2, 3, 4, 5, 6, 7], note: "R = responsable, A = aprobador, C = consultado, I = informado." }),
    h3("4.18.1 Procedimientos de recuperación (DRP)"),
    bullet("**DR-1 Caída de un contenedor (probado):** reiniciar el servicio, esperar el estado saludable y verificar `/health` y conteos de registros."),
    bullet("**DR-2 Corrupción de una base (probado en entorno aislado):** declarar el incidente, congelar cambios, verificar el SHA-256 de la copia cifrada, restaurar en una instancia aislada, validar conteos, MFA y RBAC, y migrar con autorización."),
    bullet("**DR-2b Error lógico con hora conocida (probado en réplicas):** restaurar el respaldo base y aplicar WAL hasta el instante anterior al error."),
    bullet("**DR-3 Compromiso de identidad:** aislar Keycloak, rotar secretos, restaurar desde una copia anterior al compromiso y forzar nueva inscripción de MFA."),
    bullet("**DR-4 Pérdida del sitio:** levantar un nuevo host o la VPC de recuperación en AWS, recuperar código y secretos desde custodia, restaurar las copias fuera del sitio y aplicar DR-2. Hoy no es recuperable dentro del RTO hasta desplegar la copia inmutable (R-011)."),
    bullet("**DR-5 Ransomware:** aislar el equipo, preservar evidencia, no pagar, reconstruir desde la copia inmutable y verificar la integridad de la configuración."),
    ...table("Pruebas de recuperación: tiempo observado frente al objetivo", ["Prueba", "Proceso", "RTO objetivo", "Observado", "Cumple"], [
      ["Interrupción de la API", "PROC-002", "8 h", "11.98 s", "Sí"],
      ["Interrupción de Keycloak", "PROC-004", "2 h", "70.24 s", "Sí"],
      ["Restauración aislada académica", "PROC-002", "8 h", "8.33 s", "Sí"],
      ["Restauración aislada de identidad", "PROC-004", "2 h", "8.97 s", "Sí"],
      ["PITR académica (réplica)", "PROC-002", "8 h", "2.1 s", "Sí"],
      ["PITR identidad (réplica)", "PROC-004", "2 h", "2.1 s", "Sí"],
      ["RPO con respaldo diario (académica)", "PROC-002", "RPO 4 h", "24 h", "No (R-019)"],
      ["RPO con respaldo diario (identidad)", "PROC-004", "RPO 15 min", "24 h", "No (R-019)"],
    ], [34, 14, 16, 16, 20], { size: 16, fillFn: (v, i) => (i === 4 ? (v === "Sí" ? "E2F0D9" : "FBE5D6") : undefined),
      note: "Tiempos de recuperación técnica de bases pequeñas en un solo equipo; no incluyen detección, decisión ni comunicación, por lo que no se extrapolan al RTO institucional. Fuente: evidencias/recovery/ y evidencias/pitr/." }),
    p("**Programa de pruebas.** Semanal: restauración aislada automatizada de ambas bases (tarea programada `SGSI-UVCG-Prueba-Recuperacion`, domingos a las 10:00). Mensual: salud y verificación de hashes. Semestral: interrupción controlada de la API y de la identidad. Anual: ejercicio de mesa con todos los roles y prueba de pérdida de sitio cuando exista el entorno alterno en AWS."),
  ];
}

function cobitItil() {
  return [
    h2("4.19 Gobierno y gestión de servicios de TI (COBIT 2019 e ITIL 4)"),
    p("COBIT 2019 se usó para definir **qué** debe gobernarse y gestionarse y con qué nivel de capacidad; ITIL 4 para definir **cómo** se operan los servicios en el día a día. La autoevaluación de capacidad (escala 0–5) es académica y no sustituye una evaluación formal."),
    ...table("Objetivos de COBIT 2019 aplicados", ["Objetivo", "Aspecto del enunciado", "Aplicación en la UVCG", "Capacidad"], [
      ["EDM01 Marco de gobierno", "Gobierno", "Comité de Seguridad, política general aprobada por la Rectoría, roles RACI", "1"],
      ["EDM03 Optimización del riesgo", "Gestión de riesgos", "Apetito y criterios de aceptación definidos (sección 4.7)", "1"],
      ["EDM04 Optimización de recursos", "Gestión de recursos", "Selección de herramientas proporcionales al hardware; plan Free de AWS con presupuesto de gasto cero", "2"],
      ["APO02 Estrategia", "Alineamiento estratégico", "Objetivos de seguridad ligados a procesos académicos críticos del BIA", "1"],
      ["APO12 Riesgo gestionado", "Gestión de riesgos", "22 riesgos con P × I, OCTAVE y trazabilidad automática", "2"],
      ["APO13 Seguridad gestionada", "Gestión de riesgos", "SGSI, declaración de aplicabilidad de 93 controles, validación integral", "2"],
      ["BAI06 Cambios gestionados", "Cumplimiento", "Registro CHG-001 a CHG-008 con reversión", "2"],
      ["BAI09 Activos gestionados", "Gestión de recursos", "Inventario de 33 activos y eventos de ciclo de vida", "2"],
      ["DSS02 Incidentes gestionados", "Desempeño", "Registro INC con auditoría encadenada", "2"],
      ["DSS04 Continuidad gestionada", "Desempeño", "BCP/DRP con pruebas semanales", "2"],
      ["DSS05 Servicios de seguridad", "Desempeño", "MFA, RBAC, TLS, segmentación, IDS, DLP", "2"],
      ["MEA01 Desempeño monitoreado", "Desempeño", "Indicadores de la validación integral (exitoso, fallido, omitido)", "2"],
      ["MEA03 Cumplimiento externo", "Cumplimiento", "Requisitos legales identificados (sección 5.3); análisis legal pendiente", "0"],
    ], [24, 16, 50, 10], { size: 16, center: [3] }),
    ...table("Prácticas de ITIL 4 aplicadas", ["Práctica", "Aplicación demostrable", "Evidencia"], [
      ["Gestión de incidentes", "Apertura, contención, cierre y lección aprendida de 13 incidentes", "governance/registros-operativos.md"],
      ["Habilitación de cambios", "Cambios estándar y normales con riesgo, reversión y aprobación", "CHG-001 a CHG-008"],
      ["Gestión de problemas", "Causa raíz de INC-008 e INC-009 corregida en los scripts", "registros-operativos.md"],
      ["Gestión de niveles de servicio", "RTO/RPO por proceso como objetivos de servicio; disponibilidad medida cada 15 s", "bia.csv, uptime-monitor"],
      ["Gestión de activos de TI", "Inventario y eventos de alta y cambio", "AST-001 a AST-004"],
      ["Gestión de la configuración", "Línea base SHA-256 y verificación de integridad", "evidencias/integridad/"],
      ["Gestión de la continuidad del servicio", "BIA, BCP, DRP y pruebas", "governance/bcp.md, drp.md"],
      ["Gestión de la seguridad de la información", "SGSI, políticas y controles", "declaracion-aplicabilidad.md"],
      ["Gestión de solicitudes de servicio", "Solicitudes de acceso con decisión de mínimo privilegio", "ACC-001, ACC-002"],
    ], [26, 46, 28], { size: 16 }),
  ];
}

function dataCenter() {
  return [
    h2("4.20 Data Center (TIA-942)"),
    p("El laboratorio se ejecuta en un único equipo y no constituye un centro de datos; por eso, las buenas prácticas de TIA-942 se aplican al **centro de datos del campus** de la arquitectura objetivo. Se propone un nivel equivalente a **Rated 2** (componentes redundantes en energía y climatización) para el sitio principal, complementado con la nube de AWS como sitio de recuperación. La decisión es coherente con el BIA: los RTO de 2 a 24 h no justifican el costo de un Rated 3 o 4 propio, pero sí exigen eliminar los puntos únicos de falla más probables."),
    ...table("Buenas prácticas TIA-942 para el centro de datos del campus", ["Aspecto", "Práctica propuesta", "Riesgo tratado"], [
      ["Energía", "Dos acometidas eléctricas cuando sea factible; tableros separados; circuitos dedicados por rack; PDU con medición", "R-004, R-014"],
      ["UPS", "UPS de doble conversión en configuración N+1 con autonomía mínima de 15 minutos a plena carga para la transferencia al generador", "R-004"],
      ["Generadores", "Generador diésel con transferencia automática, combustible para 24 h, prueba mensual con carga", "R-004, R-014"],
      ["Climatización", "Aire acondicionado de precisión N+1; pasillos frío y caliente; temperatura de entrada entre 18 y 27 °C (ASHRAE)", "R-014"],
      ["Cableado", "Cableado estructurado categoría 6A y fibra multimodo OM4 en el troncal; rutas separadas para energía y datos; etiquetado y documentación", "R-004"],
      ["Redundancia", "Dos switches de núcleo, par NGFW, dos ISP con rutas físicas distintas, almacenamiento en RAID 10", "R-004, R-011"],
      ["Seguridad física", "Sala sin ventanas, paredes de resistencia al fuego, ubicada fuera de zonas inundables y lejos de áreas públicas", "R-014"],
      ["Control de acceso", "Tarjeta + biometría, registro de entradas, videovigilancia con 30 días de retención, acompañamiento de visitantes", "R-014, R-016"],
      ["Protección contra incendios", "Detección temprana por aspiración (VESDA) y extinción por agente limpio que no daña equipos; extintores clase C", "R-014"],
      ["Monitoreo", "Sensores de temperatura, humedad, agua y energía integrados a la consola de monitoreo y al SIEM", "R-012, R-014"],
      ["Resiliencia", "Copia inmutable y sitio de recuperación en AWS en otra región geográfica; pruebas anuales de pérdida de sitio", "R-011"],
    ], [16, 66, 18], { size: 16 }),
    p("**Responsabilidad compartida en la nube.** Para los servicios alojados en AWS, la seguridad física, la energía y la climatización de los centros de datos son responsabilidad del proveedor. La UVCG no evalúa directamente esas instalaciones, sino que se apoya en los informes de auditoría independientes que AWS publica (por ejemplo, SOC 2 e ISO/IEC 27001) y que deben revisarse como parte de la gestión de proveedores (control A.5.23)."),
  ];
}

// ---------- 5. Discusión ----------
function discusion() {
  return [
    h1("5. Discusión"),
    p("Esta sección recoge la discusión académica del grupo sobre las seis preguntas del enunciado, contrastando la literatura con lo observado en el proyecto."),
    h2("5.1 Zero Trust en nube pública frente a entorno híbrido"),
    p("En una nube pública, el plano de control del proveedor ya es nativamente un punto de decisión de políticas: cada llamada a la API de AWS se autentica y autoriza con IAM, se registra en CloudTrail y puede condicionarse por atributos como el origen, el uso de MFA o el cifrado del transporte. Implementar Zero Trust allí consiste sobre todo en diseñar bien las políticas —roles con credenciales temporales, denegaciones explícitas, ausencia de recursos públicos— (Rose et al., 2020). En el proyecto, la política del bucket que niega cualquier escritura que no provenga del rol autorizado y cualquier conexión con TLS inferior a 1.2 es un ejemplo de verificación explícita por solicitud."),
    p("En un entorno híbrido el reto es mayor por tres razones. Primero, conviven sistemas heredados que confían en la ubicación de red y no soportan autenticación moderna, lo que obliga a interponer proxies o pasarelas de identidad. Segundo, la identidad suele estar fragmentada entre el directorio local y el de la nube, y sin federación se pierde la visibilidad unificada. Tercero, el enlace entre sitios (VPN) tiende a crear una zona de confianza implícita que contradice el modelo. La Agencia de Ciberseguridad y Seguridad de las Infraestructuras de EE. UU. propone avanzar por pilares —identidad, dispositivos, redes, aplicaciones y datos— con niveles de madurez (CISA, 2023). El grupo observó esa progresión: la identidad y las aplicaciones alcanzaron un nivel avanzado en el laboratorio, mientras que el pilar de dispositivos quedó inicial por la ausencia de MDM, lo que impide decisiones basadas en la postura del equipo."),
    h2("5.2 Buenas prácticas de MDM y DLP en dispositivos móviles"),
    p("NIST recomienda gestionar los móviles a lo largo de su ciclo de vida: definir la política, inscribir los dispositivos, verificar continuamente su cumplimiento, separar los datos institucionales de los personales y poder revocar el acceso o borrar selectivamente (Howell et al., 2023). En entornos universitarios con alta proporción de BYOD, el grupo considera que la práctica clave es el **contenedor o perfil de trabajo**, porque equilibra la protección de la información con la privacidad del estudiante o docente, que no aceptaría un borrado completo de su teléfono personal."),
    p("La DLP es eficaz sólo si existe una clasificación previa: sin etiquetas, las reglas se basan únicamente en patrones (números de tarjeta, documentos de identidad) y generan falsos positivos o dejan pasar documentos sensibles sin patrones reconocibles. Por eso el proyecto comenzó por la política de clasificación en cuatro niveles antes de construir la compuerta DLP. Otras buenas prácticas son aplicar la DLP en todos los canales de salida —correo, almacenamiento en la nube, portapapeles entre aplicaciones gestionadas y no gestionadas—, combinarla con el acceso condicional para que un dispositivo no conforme sólo vea información pública, y empezar en modo de monitoreo antes de bloquear para ajustar las reglas."),
    h2("5.3 Cumplimiento normativo local e internacional"),
    p("Guatemala no cuenta todavía con una ley general de protección de datos personales. Las obligaciones se derivan de la Constitución Política de la República, que protege la inviolabilidad de la correspondencia, documentos y libros (art. 24) y reconoce el derecho de las personas a conocer lo que consta de ellas en archivos y registros estatales (art. 31); de la Ley de Acceso a la Información Pública (Decreto 57-2008), que regula los datos sensibles en manos de sujetos obligados; de la Ley para el Reconocimiento de las Comunicaciones y Firmas Electrónicas (Decreto 47-2008), y del Código Penal, que tipifica delitos informáticos como la destrucción y alteración de registros informáticos (arts. 274 \"A\" a 274 \"G\")."),
    p("Al usar nube pública, la UVCG debe considerar además que los datos se alojan fuera del país, por lo que conviene definir contractualmente la región de almacenamiento, la propiedad de los datos, la notificación de incidentes y el procedimiento de salida. Si la universidad atiende a estudiantes de la Unión Europea o firma convenios con instituciones europeas, puede quedar sujeta al Reglamento General de Protección de Datos (Parlamento Europeo y Consejo de la Unión Europea, 2016). Las normas ISO/IEC 27017 e ISO/IEC 27018 ofrecen controles específicos para servicios en la nube y para la protección de datos personales en nubes públicas, y el modelo de responsabilidad compartida obliga a documentar qué controles aporta el proveedor y cuáles la universidad (Amazon Web Services, s.f.-a). El grupo identificó como brecha el objetivo MEA03 de COBIT, con capacidad 0, porque el análisis legal formal está pendiente."),
    h2("5.4 Contribución de SIEM, EDR y XDR frente a mecanismos tradicionales"),
    p("Los mecanismos tradicionales —antivirus por firmas, firewalls perimetrales y revisión manual de registros— actúan de forma aislada y sólo detectan lo conocido. Un SIEM centraliza los registros de múltiples fuentes, los normaliza y aplica reglas de correlación con ventanas temporales, lo que permite detectar patrones que ninguna fuente revela por sí sola, como una ráfaga de autenticaciones fallidas seguida de un acceso exitoso (González-Granadillo et al., 2021; Kent y Souppaya, 2006). En el proyecto, la regla SIEM-AUTH-001 combinó eventos de Keycloak y de la API que, por separado, no habrían generado alerta."),
    p("El EDR aporta visibilidad del comportamiento en el punto final —procesos, conexiones, cambios de archivos— y capacidad de respuesta, como aislar un equipo. El XDR extiende esa correlación a red, identidad, correo y nube con respuesta automatizada. Su contribución principal es reducir el tiempo de detección y de respuesta, así como la fatiga de alertas, al agrupar señales relacionadas en un solo incidente. Sin embargo, el grupo constató que estas herramientas no sustituyen el proceso: sin reglas probadas, responsables y un procedimiento de respuesta como el que propone NIST SP 800-61 Rev. 3 (Nelson et al., 2025), una plataforma avanzada sólo genera más alertas. También se evidenció que su costo y requerimientos (memoria, licencias, personal) pueden ser prohibitivos para una institución pequeña, lo que justifica soluciones proporcionales como el SIEM ligero construido."),
    h2("5.5 Mejora continua del SGSI después de la certificación ISO/IEC 27001"),
    p("La certificación no es un punto final: ISO/IEC 27001 exige mantener el sistema mediante seguimiento, medición, auditoría interna, revisión por la dirección y mejora continua (cláusulas 9 y 10), y el organismo certificador realiza auditorías de seguimiento anuales y una recertificación cada tres años. El grupo propone para la UVCG cinco mecanismos concretos: (1) ejecutar la validación integral automatizada al menos mensualmente y tratar cada resultado fallido como no conformidad; (2) revisar la matriz de riesgos trimestralmente y después de cada incidente o cambio mayor; (3) auditorías internas anuales por muestreo de controles; (4) una revisión por la dirección semestral con indicadores —porcentaje de cuentas con MFA, pruebas de restauración exitosas, tiempo de cierre de incidentes—, y (5) un registro de lecciones aprendidas que alimente cambios en los controles."),
    p("El laboratorio mostró este ciclo en pequeña escala: el fallo real de restauración (INC-008) se registró, se analizó su causa y se corrigió el script mediante un cambio controlado, y la siguiente prueba fue exitosa. Ese circuito de detectar, registrar, corregir y verificar es la esencia de la mejora continua."),
    h2("5.6 Complementariedad de COBIT 2019 e ITIL 4"),
    p("COBIT 2019 se sitúa en el nivel de gobierno: define objetivos de gobierno y gestión, establece quién decide y cómo se mide la capacidad, y vincula las metas de TI con las metas de la organización mediante su cascada de metas (ISACA, 2018). ITIL 4 se sitúa en el nivel operativo: describe prácticas para crear valor con los servicios, como la gestión de incidentes, cambios y niveles de servicio (AXELOS, 2019). Ambos se complementan porque COBIT dice qué debe lograrse y con qué control, mientras que ITIL dice cómo ejecutarlo."),
    p("En el proyecto esta relación se hizo explícita: el objetivo DSS02 de COBIT (solicitudes e incidentes gestionados) se operó con la práctica de gestión de incidentes de ITIL mediante el registro INC; BAI06 (cambios gestionados) con la práctica de habilitación de cambios; DSS04 (continuidad gestionada) con la gestión de la continuidad del servicio. Para alinear la seguridad con los objetivos institucionales, la cadena va desde la meta de la universidad —garantizar la continuidad académica— hasta la meta de TI —servicios disponibles y seguros— y, finalmente, a las prácticas ITIL con indicadores medibles como el RTO observado."),
  ];
}

function conclusiones() {
  return [
    h1("6. Conclusiones"),
    numbered("Se diseñó un SGSI para la UVCG con un enfoque basado en riesgos y trazabilidad completa entre activos, procesos, riesgos, controles y evidencias, verificada automáticamente con 21 reglas de coherencia sin fallos."),
    numbered(`El análisis con NIST SP 800-30 e ISO/IEC 27005 identificó ${riesgos.length} riesgos; los controles implementados redujeron los riesgos críticos de ${inhNiv["Crítico"] || 0} a ${resNiv["Crítico"] || 0}. OCTAVE Allegro, aplicado de forma independiente, priorizó los mismos escenarios, lo que valida la priorización.`),
    numbered("El BIA permitió cuantificar una brecha que de otro modo habría pasado inadvertida: los respaldos diarios no satisfacen el RPO de 15 minutos del proceso de identidad. El archivado WAL, probado en réplicas, reduce el RPO a menos de un minuto."),
    numbered("La implementación demostró en un laboratorio funcional IAM centralizado con MFA obligatorio, control de acceso por rol con principios de Zero Trust, segmentación de red, detección de intrusos, monitoreo centralizado, prevención de fuga de datos y recuperación probada con tiempos medidos muy inferiores a los objetivos."),
    numbered("La arquitectura híbrida con AWS se justificó por costo y resiliencia frente a un segundo centro de datos propio; su componente en AWS se desplegó con infraestructura como código y superó 13 de 13 pruebas de mínimo privilegio, cifrado, rechazo de acceso anónimo y registro, sin costo. Queda por desplegar la VPC de recuperación y la copia inmutable para cerrar el riesgo R-011."),
    numbered("Las principales brechas residuales —protección de dispositivos con MDM/EDR, copia fuera del sitio y sitio alterno— dependen de decisiones de inversión y no de capacidades técnicas, lo que confirma que la seguridad de la información es, ante todo, una decisión de gobierno."),
    numbered("Distinguir de forma explícita lo implementado, lo preparado y lo diseñado fortaleció la credibilidad del proyecto y permite sustentar cada afirmación durante la defensa con una prueba reproducible."),
  ];
}

// ---------- 7. Referencias (APA 7) ----------
function referencias() {
  const refs = [
    "Amazon Web Services. (s.f.-a). *Modelo de responsabilidad compartida*. Recuperado el 7 de noviembre de 2026, de https://aws.amazon.com/es/compliance/shared-responsibility-model/",
    "Amazon Web Services. (s.f.-b). *Pilar de seguridad: AWS Well-Architected Framework*. Recuperado el 7 de noviembre de 2026, de https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html",
    "American Psychological Association. (2020). *Publication manual of the American Psychological Association* (7.ª ed.). https://doi.org/10.1037/0000165-000",
    "AXELOS. (2019). *ITIL foundation: ITIL 4 edition*. TSO.",
    "Caralli, R. A., Stevens, J. F., Young, L. R. y Wilson, W. R. (2007). *Introducing OCTAVE Allegro: Improving the information security risk assessment process* (Informe técnico CMU/SEI-2007-TR-012). Software Engineering Institute, Carnegie Mellon University.",
    "Congreso de la República de Guatemala. (2008a). *Ley de Acceso a la Información Pública* (Decreto 57-2008).",
    "Congreso de la República de Guatemala. (2008b). *Ley para el Reconocimiento de las Comunicaciones y Firmas Electrónicas* (Decreto 47-2008).",
    "Cybersecurity and Infrastructure Security Agency. (2023). *Zero trust maturity model* (versión 2.0). https://www.cisa.gov/zero-trust-maturity-model",
    "González-Granadillo, G., González-Zarzosa, S. y Diaz, R. (2021). Security information and event management (SIEM): Analysis, trends, and usage in critical infrastructures. *Sensors, 21*(14), Artículo 4759. https://doi.org/10.3390/s21144759",
    "Howell, G., Franklin, J. M., Sritapan, V., Souppaya, M. y Scarfone, K. (2023). *Guidelines for managing the security of mobile devices in the enterprise* (NIST Special Publication 800-124 Rev. 2). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-124r2",
    "International Organization for Standardization. (2019). *Security and resilience — Business continuity management systems — Requirements* (ISO 22301:2019).",
    "International Organization for Standardization e International Electrotechnical Commission. (2015). *Information technology — Security techniques — Code of practice for information security controls based on ISO/IEC 27002 for cloud services* (ISO/IEC 27017:2015).",
    "International Organization for Standardization e International Electrotechnical Commission. (2019). *Information technology — Security techniques — Code of practice for protection of personally identifiable information (PII) in public clouds acting as PII processors* (ISO/IEC 27018:2019).",
    "International Organization for Standardization e International Electrotechnical Commission. (2022a). *Information security, cybersecurity and privacy protection — Information security management systems — Requirements* (ISO/IEC 27001:2022).",
    "International Organization for Standardization e International Electrotechnical Commission. (2022b). *Information security, cybersecurity and privacy protection — Information security controls* (ISO/IEC 27002:2022).",
    "International Organization for Standardization e International Electrotechnical Commission. (2022c). *Information security, cybersecurity and privacy protection — Guidance on managing information security risks* (ISO/IEC 27005:2022).",
    "ISACA. (2018). *COBIT 2019 framework: Governance and management objectives*. ISACA.",
    "Joint Task Force Transformation Initiative. (2012). *Guide for conducting risk assessments* (NIST Special Publication 800-30 Rev. 1). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-30r1",
    "Kent, K. y Souppaya, M. (2006). *Guide to computer security log management* (NIST Special Publication 800-92). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-92",
    "National Institute of Standards and Technology. (2024). *The NIST Cybersecurity Framework (CSF) 2.0* (NIST CSWP 29). https://doi.org/10.6028/NIST.CSWP.29",
    "Nelson, A., Rekhi, S., Souppaya, M. y Scarfone, K. (2025). *Incident response recommendations and considerations for cybersecurity risk management: A CSF 2.0 community profile* (NIST Special Publication 800-61 Rev. 3). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-61r3",
    "Parlamento Europeo y Consejo de la Unión Europea. (2016). Reglamento (UE) 2016/679 relativo a la protección de las personas físicas en lo que respecta al tratamiento de datos personales y a la libre circulación de estos datos. *Diario Oficial de la Unión Europea, L 119*, 1–88.",
    "Rose, S., Borchert, O., Mitchell, S. y Connelly, S. (2020). *Zero trust architecture* (NIST Special Publication 800-207). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-207",
    "Souppaya, M., Morello, J. y Scarfone, K. (2017). *Application container security guide* (NIST Special Publication 800-190). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-190",
    "Swanson, M., Bowen, P., Phillips, A. W., Gallup, D. y Lynes, D. (2010). *Contingency planning guide for federal information systems* (NIST Special Publication 800-34 Rev. 1). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-34r1",
    "Telecommunications Industry Association. (2017). *Telecommunications infrastructure standard for data centers* (ANSI/TIA-942-B).",
  ];
  return [
    h1("7. Referencias"),
    ...refs.map((r) => new Paragraph({
      children: runs(r), indent: { left: 720, hanging: 720 }, spacing: { line: 240, after: 120 }, alignment: AlignmentType.LEFT,
    })),
  ];
}

// ---------- 8. Anexos ----------
function anexosIntro() {
  return [
    h1("8. Anexos"),
    p("Los anexos contienen las matrices completas generadas desde el repositorio del proyecto, el registro de evidencias y la declaración de uso de inteligencia artificial. Todas las matrices se regeneran con `python scripts/generar_gobernanza_sgsi.py` y se validan con `python scripts/validar_trazabilidad.py`."),
  ];
}

function anexoA() {
  return [
    h2("Anexo A. Inventario completo de activos"),
    ...table("Inventario de activos (E4.1)", ["ID", "Activo", "Tipo", "Propietario", "Custodio", "Ubicación", "Información procesada", "C", "I", "D", "Criticidad", "Dependencias", "Estado"],
      activos.map((a) => [a.id, a.activo, a.tipo, a.propietario, a.custodio, a.ubicacion, a.informacion_procesada, a.confidencialidad_1_5, a.integridad_1_5, a.disponibilidad_1_5, a.criticidad, a.dependencias, a.estado_real]),
      [6, 13, 8, 8, 9, 8, 12, 3, 3, 3, 7, 10, 10], { landscape: true, size: 13, center: [7, 8, 9], fillFn: (v, i) => (i === 10 ? (v === "Crítica" ? FILL["Crítico"] : v === "Alta" ? FILL.Alto : FILL.Moderado) : undefined) }),
  ];
}

function anexoB() {
  return [
    h2("Anexo B. Matriz de riesgos completa"),
    ...table("Matriz de riesgos con escenario, efectividad de controles y responsable", ["ID", "Proceso", "Escenario", "Efectividad del control (1–5)", "Responsable", "Evidencia"],
      riesgos.map((r) => [r.id, r.proceso, r.escenario, r.efectividad_control_1_5, r.responsable, r.evidencia]),
      [6, 9, 38, 10, 13, 24], { landscape: true, size: 14, center: [3] }),
  ];
}

function anexoC() {
  return [
    h2("Anexo C. Declaración de aplicabilidad (ISO/IEC 27001:2022, Anexo A)"),
    ...table("Declaración de aplicabilidad de los 93 controles", ["Control", "Nombre", "Aplica", "Estado", "Riesgos", "Evidencia"],
      soa.map((s) => [s.control_id, s.control_name, s.applicable, s.implementation_status, s.related_risks, s.evidence]),
      [7, 28, 6, 18, 14, 27], { landscape: true, size: 13,
        fillFn: (v, i) => (i === 3 ? (v.startsWith("Implementado") ? "E2F0D9" : v.startsWith("Parcial") ? "FFF2CC" : "FBE5D6") : undefined),
        note: "Los controles sin riesgo específico son controles de base exigidos por el alcance institucional (políticas, roles, seguridad física, recursos humanos)." }),
  ];
}

function anexoD() {
  const ev = [
    ["EV-01", "IAM, MFA y RBAC", "scripts/pruebas_identidad.py; evidencias/siem/consulta-auth-denied-*.json"],
    ["EV-02", "HTTPS y perímetro", "scripts/pruebas_locales.py; evidencias/pruebas-funcionales-20261024.txt"],
    ["EV-03", "Segmentación", "evidencias/network/segmentacion-20261107-111221.json"],
    ["EV-04", "IDS", "evidencias/ids/REPORTE-IDS.md; resultado.json; eve.json"],
    ["EV-05", "SIEM y monitoreo", "evidencias/siem/REPORTE-SIEM.md; pipeline-siem-*.json; tablero-siem-*.html"],
    ["EV-06", "EDR (vigilancia de contenedores)", "evidencias/edr/vigilancia-20261024-110442-malicioso-proceso.json"],
    ["EV-07", "DLP", "evidencias/dlp/compuerta-externo-20261107-111229.json"],
    ["EV-08", "MDM (simulación)", "evidencias/mdm/cumplimiento-mdm-20261107-111229.json"],
    ["EV-09", "Respaldo", "evidencias/backup/REPORTE-BACKUP-RECUPERACION.md; backups-programados-*.json"],
    ["EV-10", "Recuperación", "evidencias/recovery/continuidad-*.json; restauracion-dual-*.json"],
    ["EV-11", "PITR", "evidencias/pitr/pitr-20261024-111423.json"],
    ["EV-12", "Integridad de configuración", "evidencias/integridad/verificacion-*.json"],
    ["EV-13", "Vulnerabilidades", "evidencias/security/; evidencias/postgres-upgrade/"],
    ["EV-14", "Registros operativos", "governance/registros-operativos.md; evidencias/gestion/registro-sgsi.db"],
    ["EV-15", "Trazabilidad de gobierno", "evidencias/gobernanza/trazabilidad-*.json"],
    ["EV-16", "Validación integral", "evidencias/automatizacion/validacion-sgsi-*.json"],
    ["EV-17", "IaC de AWS", "evidencias/aws/validacion-terraform-aws-20261024.txt; trivy-config-aws.json"],
    ["EV-18", "Despliegue y pruebas AWS", "evidencias/aws/plan-20261107-130521.txt; apply-20261107-130521.txt; pruebas-aws-20261107-130835.json"],
  ];
  return [
    h2("Anexo D. Registro de evidencias"),
    p("Cada evidencia se identifica con un código y se relaciona con el elemento del proyecto que demuestra. Las evidencias no contienen contraseñas, tokens ni datos personales reales; los secretos se redactan automáticamente antes de almacenarse."),
    ...table("Registro de evidencias", ["Código", "Elemento demostrado", "Archivo(s) en el repositorio"], ev, [10, 26, 64], { size: 16 }),
    h2("Anexo E. Reproducción del laboratorio"),
    numbered("Iniciar Docker Desktop y, desde la carpeta `local`, ejecutar `docker compose -f compose.yaml up -d`.", "pasos"),
    numbered("Ejecutar `scripts\\validar_sgsi.ps1` para la validación sin interrupciones, o agregar `-IncludeIds -IncludeRecovery -IncludeSecurity -IncludeContinuity` para la validación completa.", "pasos"),
    numbered("Abrir `https://localhost:8443/auth/realms/uvcg/account/` para el inicio de sesión con MFA.", "pasos"),
    numbered("Regenerar las matrices con `python scripts\\generar_gobernanza_sgsi.py` y validarlas con `python scripts\\validar_trazabilidad.py`.", "pasos"),
    numbered("Detener con `docker compose -f compose.yaml down` (sin `-v`, para conservar los datos).", "pasos"),
    h2("Anexo F. Declaración de uso de inteligencia artificial"),
    p("De acuerdo con la sección 18 del enunciado, el grupo declara que utilizó un asistente de inteligencia artificial generativa (Claude, de Anthropic) como apoyo para estructurar el documento, redactar borradores de secciones, generar scripts de automatización y diagramas, y revisar la coherencia entre matrices. Todas las evidencias técnicas provienen de ejecuciones reales en el laboratorio del grupo y no fueron generadas ni alteradas por la herramienta. El grupo verificó la información, validó las referencias y es responsable del contenido presentado y de su defensa oral. [[Revisar y ajustar esta declaración según el uso real del grupo.]]"),
  ];
}

// ---------- Ensamblado ----------
const header = new Header({
  children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ children: [PageNumber.CURRENT], font: L.FONT, size: 24 })] })],
});
const emptyHeader = new Header({ children: [new Paragraph({ children: [] })] });

const portrait = { size: { width: L.PAGE.width, height: L.PAGE.height }, margin: L.MARGIN };
const landscape = { size: { width: L.PAGE.width, height: L.PAGE.height, orientation: PageOrientation.LANDSCAPE }, margin: L.MARGIN };

const resultadosA = () => [h1("4. Resultados"), ...escenario(), ...alcance(), ...arquitectura(), ...inventario(), ...biaSec(), ...riesgosSec()];
const resultadosB = () => [...octave(), ...calor(), ...tratamientoSec()];
const resultadosC = () => [...politicas(), ...matrizControles(), ...buenasPracticas(), ...zeroTrust(), ...mdmDlp(), ...siem(), ...implementacion(),
  ...continuidad(), ...cobitItil(), ...dataCenter()];

const body = (children, orient, first = false) => ({
  properties: {
    type: SectionType.NEXT_PAGE,
    page: { ...(orient === "l" ? landscape : portrait), ...(first ? { pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } : {}) },
  },
  headers: { default: header },
  children,
});

const doc = new Document({
  creator: "Grupo del proyecto final — Estándares de Seguridad",
  title: "SGSI UVCG — Proyecto final",
  description: "Diseño e implementación de un SGSI para la universidad ficticia UVCG",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: L.FONT, size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: L.FONT, size: 24, bold: true }, paragraph: { spacing: { before: 240, after: 120, line: 240 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: L.FONT, size: 24, bold: true }, paragraph: { spacing: { before: 200, after: 120, line: 240 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: L.FONT, size: 24, bold: true, italics: true }, paragraph: { spacing: { before: 160, after: 100, line: 240 }, keepNext: true, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1080, hanging: 360 } } } }] },
      { reference: "numeros", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "pasos", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [
    { properties: { page: portrait }, headers: { default: emptyHeader }, children: portada() },
    { properties: { type: SectionType.NEXT_PAGE, page: portrait }, headers: { default: emptyHeader }, children: indice() },
    body([...introduccion(), ...marcoTeorico(), ...metodologia(), ...resultadosA()], "p", true),
    body(riesgosTabla(), "l"),
    body(resultadosB(), "p"),
    body([tratamientoTabla()].flat(), "l"),
    body([...resultadosC(), ...discusion(), ...conclusiones(), ...referencias(), new Paragraph({ children: [new PageBreak()] }), ...anexosIntro()], "p"),
    body([...anexoA(), ...anexoB(), ...anexoC()], "l"),
    body(anexoD(), "p"),
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("OK:", OUT, `${(buf.length / 1024).toFixed(0)} KB`);
});
