# syntax=docker/dockerfile:1

FROM python:3.10

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV FHIR_SERVER_URL=${FHIR_SERVER_URL:-http://localhost:8080/fhir/}
ENV FACADE_PORT=${FACADE_PORT:-8082}

RUN openssl genrsa -out foobar.key 2048
RUN openssl req -new -key foobar.key -out foobar.csr -subj "/C=GB/ST=London/L=London/O=Global Security/OU=IT Department/CN=example.com"
RUN openssl x509 -req -days 365 -in foobar.csr -signkey foobar.key -out foobar.crt

EXPOSE ${FACADE_PORT:-8082}

CMD ["uwsgi", "wsgi.ini"]
