# syntax=docker/dockerfile:1

FROM python:3.10-alpine
ENV FHIR_SERVER_URL: ${FHIR_SERVER_URL}
ENV TOTAL: 500
ENV COUNT: 500
ENV VALIDATION_URL: "http://localhost:8092/validate"
ENV REPORT_LOCATION: ${REPORT_LOCATION}
ENV USERNAME: ""
ENV PASSWORD: ""
ENV FHIR_TOKEN: ${FHIR_TOKEN}
ENV HTTP_PROXY: ${HTTP_PROXY}
ENV HTTPS_PROXY: ${HTTPS_PROXY}

VOLUME ["/app/report"]
VOLUME ["/app/maps"]

COPY . /app

WORKDIR /app
RUN pip3 install -r requirements.txt

ENTRYPOINT python main.py ${FHIR_SERVER_URL} -u ${USERNAME} -p ${PASSWORD} -ft ${FHIR_TOKEN} --http-proxy${HTTP_PROXY} --https-proxy ${HTTPS_PROXY} -t ${TOTAL} -c ${COUNT} -v ${VALIDATION_URL}