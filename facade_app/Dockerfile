# syntax=docker/dockerfile:1

FROM python:3.10

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

ENV USER_UID=1111

RUN mkdir -p /data/ssl && \
    chown -R ${USER_UID}:${USER_UID} /data && \
    chown -R ${USER_UID}:${USER_UID} /pages

USER ${USER_UID}:${USER_UID}

RUN openssl genrsa -out /data/ssl/foobar.key 2048
RUN openssl req -new -key /data/ssl/foobar.key -out /data/ssl/foobar.csr -subj "/C=GB/ST=London/L=London/O=Global Security/OU=IT Department/CN=example.com"
RUN openssl x509 -req -days 365 -in /data/ssl/foobar.csr -signkey /data/ssl/foobar.key -out /data/ssl/foobar.crt

EXPOSE ${FACADE_PORT}

CMD ["uwsgi", "wsgi.ini"]
