FROM postgres:16-alpine

RUN apk add --no-cache openssl && rm -f /usr/local/bin/gosu
COPY backup-encrypted.sh /usr/local/bin/backup-encrypted.sh
RUN chmod 0555 /usr/local/bin/backup-encrypted.sh

USER 70:70
HEALTHCHECK NONE
