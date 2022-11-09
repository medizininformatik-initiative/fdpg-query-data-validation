FROM python:3.10

ENV PACKAGES ""
ENV BLAZE_SERVER_URL "http://localhost:8090/fhir"

VOLUME ["/app/profiles"]
RUN apt-get -y install curl

# Install FHIR Populator
RUN python -m pip install fhir-populator

COPY . /app

CMD sh /app/sd_upload.sh
