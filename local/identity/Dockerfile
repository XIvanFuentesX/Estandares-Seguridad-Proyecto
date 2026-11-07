FROM quay.io/keycloak/keycloak:26.8.1 AS builder

ENV KC_DB=postgres \
    KC_HEALTH_ENABLED=true \
    KC_METRICS_ENABLED=true \
    KC_HTTP_RELATIVE_PATH=/auth

RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:26.8.1
COPY --from=builder /opt/keycloak/ /opt/keycloak/

ENV KC_HTTP_RELATIVE_PATH=/auth

USER 1000
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD ["bash", "-c", "{ printf 'GET /auth/health/ready HTTP/1.0\\r\\n\\r\\n' >&0; grep 'HTTP/1.0 200'; } 0<>/dev/tcp/127.0.0.1/9000"]
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
