FROM python:3.10-alpine

ENV PACKAGES ""
ENV BLAZE_SERVER_URL "http://localhost:8090/fhir"

VOLUME ["/app/profiles"]

# Install FHIR Populator
RUN python -m pip install fhir-populator

COPY . /app

CMD python -m fhir_populator --endpoint ${BLAZE_SERVER_URL} --get-dependencies --non-interactive --only-put --package ${PACKAGES} && sh own_sd_upload.sh
