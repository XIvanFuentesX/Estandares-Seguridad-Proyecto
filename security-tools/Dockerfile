FROM python:3.12-alpine
HEALTHCHECK NONE

RUN addgroup -g 10001 -S scanner \
    && adduser -u 10001 -S scanner -G scanner \
    && pip install --no-cache-dir --no-compile \
       bandit==1.8.6 \
       pip-audit==2.10.1 \
       detect-secrets==1.5.0

USER 10001:10001
WORKDIR /workspace
ENTRYPOINT []
CMD ["python", "--version"]
