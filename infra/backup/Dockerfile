FROM python:3.11-slim

# Install PostgreSQL client tools + AWS CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    ca-certificates \
    gzip \
    && pip install --no-cache-dir awscli \
    && rm -rf /var/lib/apt/lists/*

# Install supercronic (reliable cron for containers)
ARG SUPERCRONIC_VERSION=0.2.29
ARG SUPERCRONIC_SHA1SUM=cd48d45c4b10f3f0bfdd3a57d054cd05ac96812b
RUN curl -fsSL "https://github.com/aptible/supercronic/releases/download/v${SUPERCRONIC_VERSION}/supercronic-linux-amd64" \
    -o /usr/local/bin/supercronic \
    && echo "${SUPERCRONIC_SHA1SUM}  /usr/local/bin/supercronic" | sha1sum -c - \
    && chmod +x /usr/local/bin/supercronic

COPY backup.sh /usr/local/bin/backup.sh
COPY crontab /etc/supercronic/crontab

RUN chmod +x /usr/local/bin/backup.sh

VOLUME ["/backups"]

CMD ["/usr/local/bin/supercronic", "/etc/supercronic/crontab"]
