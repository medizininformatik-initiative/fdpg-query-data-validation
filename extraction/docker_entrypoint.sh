#!/bin/bash
export "$(cat .env | xargs)"
CA_FILE=${CA_FILE}
FHIR_SERVER_URL=${FHIR_SERVER_URL:-"http://localhost:8080/fhir"}
TOTAL=${TOTAL:-500}
COUNT=${COUNT:-500}
VALIDATION_URL=${VALIDATION_URL:-"http://localhost:8092/validate"}
REPORT_LOCATION=${REPORT_LOCATION:-"/app/report"}
FHIR_USERNAME=${FHIR_USERNAME:-""}
FHIR_PASSWORD=${FHIR_PASSWORD:-""}
FHIR_TOKEN=${FHIR_TOKEN}
HTTP_PROXY=${HTTP_PROXY}
HTTPS_PROXY=${HTTPS_PROXY}

if [ -f "certificates/$CA_FILE_NAME" ]; then
    echo "Using certificate $CA_FILE_NAME"
    export REQUESTS_CA_BUNDLE="certificates/$CA_FILE_NAME"
fi

echo $(python main.py ${FHIR_SERVER_URL} -u ${USERNAME} -p ${PASSWORD} -ft ${FHIR_TOKEN} --http-proxy${HTTP_PROXY} --https-proxy ${HTTPS_PROXY} --cert ${REQUESTS_CA_BUNDLE} -t ${TOTAL} -c ${COUNT} -v ${VALIDATION_URL})