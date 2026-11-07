# Validación local del SGSI — 2026-10-24

Hora de cierre: `2026-10-24 08:19:02 -06:00` (America/Guatemala).

## Estado verificado

- `docker compose -f compose.yaml config --quiet`: retorno 0.
- API: en ejecución y `healthy`.
- PostgreSQL: en ejecución y `healthy`.
- Nginx: en ejecución, con healthcheck, y publicado solamente como `127.0.0.1:8080->8080/tcp`.
- Gunicorn 23.0.0: escuchando en el puerto 8000 con dos workers (PID 7 y PID 8 en el arranque observado).
- `pip check`: `No broken requirements found`.
- `nginx -t`: sintaxis correcta y prueba exitosa.

## Causa del incidente

Los logs previos mostraron `password authentication failed for user "sgsi_demo"`. El volumen de PostgreSQL ya estaba inicializado con otra contraseña; cambiar `POSTGRES_PASSWORD` en `.env` no modifica automáticamente el rol almacenado. Se sincronizó el rol existente con la credencial actual sin recrear ni eliminar el volumen.

Además, `DATABASE_URL` interpolaba la contraseña sin codificación. Aunque la contraseña observada durante esta ejecución no contenía caracteres reservados de URI, el diseño fallaría con valores como `@`, `:`, `/`, `?`, `#` o `%`. La API ahora pasa host, puerto, base, usuario y contraseña como parámetros separados a psycopg.

## Operaciones de datos

- No se ejecutó `down -v`, `system prune`, eliminación de volúmenes ni borrado de base de datos.
- Se reinició únicamente el contenedor `db` para la prueba de persistencia.
- PostgreSQL detectó el volumen existente y omitió la inicialización, como corresponde.

## Limitación de auditoría

Docker Scout 1.21.0 está instalado, pero el análisis de CVE no pudo ejecutarse porque exige iniciar sesión con Docker ID. No se afirma ausencia de vulnerabilidades.
