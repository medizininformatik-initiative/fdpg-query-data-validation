FROM python:3.10-alpine

ENV PACKAGES ""
ENV BLAZE_SERVER_URL "http://localhost:8090/fhir"

VOLUME ["/app/profiles"]
RUN apk add curl
RUN apk add jq
RUN apk add --no-cache bash

# Install FHIR Populator
RUN python -m pip install fhir-populator

COPY . /app
WORKDIR /app

CMD bash sd_upload.sh
