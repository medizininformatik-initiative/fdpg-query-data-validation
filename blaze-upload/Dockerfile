FROM python:3.10-alpine

ENV PACKAGES ""
ENV BLAZE_SERVER_URL "http://localhost:8090/fhir"

VOLUME ["/app/profiles"]

# Install FHIR Populator
RUN python -m pip install fhir-populator

COPY . /app

CMD sh sd_upload.sh
