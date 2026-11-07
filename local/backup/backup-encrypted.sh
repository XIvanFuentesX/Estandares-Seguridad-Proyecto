#!/bin/sh
set -eu

: "${PGHOST:?PGHOST requerido}"
: "${PGUSER:?PGUSER requerido}"
: "${PGPASSWORD:?PGPASSWORD requerido}"
: "${PGDATABASE:?PGDATABASE requerido}"
: "${BACKUP_PREFIX:?BACKUP_PREFIX requerido}"
: "${BACKUP_ENCRYPTION_PASSWORD:?BACKUP_ENCRYPTION_PASSWORD requerido}"

backup_once() {
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  base="${BACKUP_PREFIX}-${stamp}"
  plain="/tmp/${base}.dump"
  encrypted="/backups/${base}.dump.enc"
  start="$(date +%s)"
  umask 077
  trap 'rm -f "$plain"' EXIT INT TERM
  if ! pg_dump --format=custom --compress=9 --no-owner --no-acl --file="$plain"; then return 1; fi
  if ! pg_restore --list "$plain" > "/backups/${base}.toc"; then return 1; fi
  if ! openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
    -in "$plain" -out "$encrypted" -pass env:BACKUP_ENCRYPTION_PASSWORD; then return 1; fi
  sha256sum "$encrypted" > "/backups/${base}.dump.enc.sha256"
  if ! test -s "$encrypted"; then return 1; fi
  hash="$(sha256sum "$encrypted" | awk '{print $1}')"
  bytes="$(wc -c < "$encrypted" | tr -d ' ')"
  elapsed="$(( $(date +%s) - start ))"
  printf '{"timestamp":"%s","target":"%s","file":"%s.dump.enc","sha256":"%s","bytes":%s,"elapsed_seconds":%s,"encrypted":true,"result":"success"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$BACKUP_PREFIX" "$base" "$hash" "$bytes" "$elapsed" \
    > "/backups/${base}.json"
  printf '%s target=%s result=success file=%s.dump.enc bytes=%s elapsed_seconds=%s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$BACKUP_PREFIX" "$base" "$bytes" "$elapsed" \
    >> /backups/execution.log
  rm -f "$plain"
  trap - EXIT INT TERM
  echo "OK: target=$BACKUP_PREFIX encrypted=true bytes=$bytes elapsed_seconds=$elapsed"
}

log_failure() {
  rm -f /tmp/"${BACKUP_PREFIX}"-*.dump
  printf '%s target=%s result=failure\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$BACKUP_PREFIX" >> /backups/execution.log
}

if [ "${1:-}" = "--once" ]; then
  if ! backup_once; then
    log_failure
    echo "ERROR: target=$BACKUP_PREFIX result=failure" >&2
    exit 1
  fi
  exit 0
fi

interval="${BACKUP_INTERVAL_SECONDS:-86400}"
case "$interval" in *[!0-9]*|'') echo "Intervalo inválido" >&2; exit 2;; esac
while true; do
  if ! backup_once; then
    log_failure
  fi
  sleep "$interval"
done
