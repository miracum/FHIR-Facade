# syntax=docker/dockerfile:1

FROM python:3.10-slim

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV FHIR_SERVER_URL=${FHIR_SERVER_URL:-http://host.docker.internal:8080/fhir/}
ENV FACADE_PORT=${FACADE_PORT:-8082}
ENV PAGE_SIZE=${PAGE_SIZE:-50}
ENV PAGE_STORE_TIME=${PAGE_STORE_TIME:-1200}
ENV PAGING_STORE=${PAGING_STORE:-LOCAL}
ENV MONGO_DB_URL=${MONGO_DB_URL:-mongodb://host.docker.internal:27017}
ENV LOG_LEVEL=${LOG_LEVEL:-INFO}
ENV BA_USER_NAME=${BA_USER_NAME}
ENV BA_PASSWORD=${BA_PASSWORD}
ENV PROVISION_CONFIG=${PROVISION_CONFIG}
ENV RESOURCE_CONFIG=${RESOURCE_CONFIG}
ENV SSL_CERT=${SSL_CERT}
ENV SSL_KEY=${SSL_KEY}
ENV GUNICORN_WORKERS=${GUNICORN_WORKERS:-1}
ENV PROCESSES_PER_WORKER=${PROCESSES_PER_WORKER:-1}
ENV INTERNAL_PAGE_SIZE=${INTERNAL_PAGE_SIZE:-2000}
ENV CONSENT_CACHE_TIME=${CONSENT_CACHE_TIME:-60}

ENV USER_UID=1111

RUN chmod +x run.sh && \
    chown ${USER_UID}:${USER_UID} run.sh

RUN mkdir -p /data/ssl && \
    chown -R ${USER_UID}:${USER_UID} /data && \
    chown -R ${USER_UID}:${USER_UID} /pages

USER ${USER_UID}:${USER_UID}

RUN openssl genrsa -out /data/ssl/gen_foobar.key 2048
RUN openssl req -new -key /data/ssl/gen_foobar.key -out /data/ssl/gen_foobar.csr -subj "/C=GB/ST=London/L=London/O=Global Security/OU=IT Department/CN=example.com"
RUN openssl x509 -req -days 365 -in /data/ssl/gen_foobar.csr -signkey /data/ssl/gen_foobar.key -out /data/ssl/gen_foobar.crt

EXPOSE ${FACADE_PORT}

CMD ["./run.sh"]
