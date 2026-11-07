FROM nginx:stable-alpine

# Incorpora parches de seguridad publicados entre reconstrucciones de la imagen base.
RUN apk upgrade --no-cache

USER 101:101
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:8080/healthz || exit 1
