# PostgreSQL 16 oficial sin gosu (VULN-001..026: Go stdlib embebido en /usr/local/bin/gosu).
# gosu sólo se usa cuando el entrypoint arranca como root; esta imagen arranca como UID 70,
# por lo que el entrypoint oficial omite el cambio de usuario y el binario no es necesario.
# Reversión: volver a "image: postgres:16-alpine" en compose.yaml.
FROM postgres:16-alpine
RUN rm -f /usr/local/bin/gosu && ! command -v gosu
USER 70:70
