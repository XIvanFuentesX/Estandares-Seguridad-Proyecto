# Matriz de acceso Zero Trust — UVCG

Toda solicitud protegida requiere token OIDC vigente emitido por el realm `uvcg`, audiencia/cliente permitido, MFA TOTP y rol suficiente. La red de origen o pertenencia a una red interna no concede confianza implícita.

| Recurso | Administrador | Docente | Estudiante | Administrativo | Sin token / token inválido |
|---|---:|---:|---:|---:|---:|
| `GET /health` | Permitir | Permitir | Permitir | Permitir | Permitir, sin datos sensibles |
| `GET /cursos` | Permitir | Permitir | Permitir | Permitir | Denegar 401 |
| `GET /perfil` | Permitir | Permitir | Permitir | Permitir | Denegar 401 |
| `GET /docencia` | Permitir | Permitir | Denegar 403 | Denegar 403 | Denegar 401 |
| `GET /administracion` | Permitir | Denegar 403 | Denegar 403 | Denegar 403 | Denegar 401 |
| Métodos de escritura en Nginx | Denegar 403 | Denegar 403 | Denegar 403 | Denegar 403 | Denegar 403 |

Controles complementarios:

- Keycloak exige TOTP a los cuatro usuarios ficticios y aplica política de contraseña.
- Flask valida firma mediante JWKS, emisor, expiración y cliente autorizado antes del rol.
- Las decisiones permitidas y denegadas se registran como eventos JSON sin tokens.
- Nginx es el único punto publicado y PostgreSQL permanece en una red interna independiente.
- Las sesiones administrativas no se publican directamente; el acceso pasa por el proxy TLS local.
- Los contenedores usan mínimo privilegio, capacidades reducidas y sistemas de archivos de solo lectura donde corresponde.

La matriz fue verificada por `scripts/pruebas_identidad.py`; no representa una implementación completa de acceso condicional por postura de dispositivo, que queda pendiente de un MDM/IdP empresarial.
