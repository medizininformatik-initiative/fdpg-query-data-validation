FROM python:3.10-alpine

ENV PACKAGES ""
ENV BLAZE_SERVER_URL "http://localhost:8090/fhir"

VOLUME ["/app/profiles"]
RUN apk add curl
RUN apk add jq
RUN apk add --no-cache bash

# Install FHIR Populator
RUN pip install virtualenv
RUN python -m venv .venv
RUN source .venv/bin/activate
RUN python -m pip install --upgrade fhir-populator==1.3.0

COPY . /app
WORKDIR /app

CMD bash sd_upload.sh
