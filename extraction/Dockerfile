# syntax=docker/dockerfile:1

FROM python:3.10-alpine
ENV FHIR_SERVER_URL: "http://localhost:8080/fhir"
ENV TOTAL: 500
ENV COUNT: 50
ENV VALIDATION_URL: "http://localhost:8092/validate"
ENV REPORT_LOCATION: "/app/report"
ENV USERNAME: ""
ENV PASSWORD: ""
ENV FHIR_TOKEN: ${FHIR_TOKEN}
ENV FHIR_HTTP_PROXY: ${FHIR_HTTP_PROXY}
ENV FHIR_HTTPS_PROXY: ${FHIR_HTTPS_PROXY}
ENV CA_FILE_NAME: ""
ENV VERIFY_SSL_CERT: "true"

COPY . /app

# RUN useradd -r -s /bin/false -u 10001 10001
RUN chown -R 1000:1000 app/report

WORKDIR /app
RUN pip3 install -r requirements.txt

RUN chmod -R u=rwx report
RUN chmod u=x docker_entrypoint.sh
USER 1000

ENTRYPOINT sh docker_entrypoint.sh