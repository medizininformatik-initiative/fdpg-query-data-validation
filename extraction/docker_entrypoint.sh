#!/bin/bash
export $(grep -v '^#' .env | xargs)
CA_FILE=${CA_FILE}
FHIR_SERVER_URL=${FHIR_SERVER_URL:-"http://localhost:8080/fhir"}
TOTAL=${TOTAL:-500}
COUNT=${COUNT:-500}
VALIDATION_URL=${VALIDATION_URL:-"http://localhost:8092/validate"}
FHIR_USERNAME=${FHIR_USERNAME:-""}
FHIR_PASSWORD=${FHIR_PASSWORD:-""}
FHIR_TOKEN=${FHIR_TOKEN}
HTTP_PROXY=${HTTP_PROXY}
HTTPS_PROXY=${HTTPS_PROXY}

echo "${FHIR_SERVER_URL}"

if [ -f "certificates/$CA_FILE_NAME" ]; then
    echo "Using certificate $CA_FILE_NAME"
    export REQUESTS_CA_BUNDLE="certificates/$CA_FILE_NAME"
fi

python main.py "${FHIR_SERVER_URL}" -u "${FHIR_USERNAME}" -p "${FHIR_PASSWORD}" -ft "${FHIR_TOKEN}" --http-proxy "${FHIR_HTTP_PROXY}" --https-proxy "${FHIR_HTTPS_PROXY}" --cert "${REQUESTS_CA_BUNDLE}" -t "${TOTAL}" -c "${COUNT}" -v "${VALIDATION_URL}" --verify "${VERIFY_SSL_CERT}"