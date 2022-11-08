FROM ghcr.io/itcr-uni-luebeck/validation-profile-mapper:latest

ENV PYTHON_DEPS: "${PYTHON_DEPS}"
ENV SERVICE_PORT: "${SERVICE_PORT}"
ENV BLAZE_PORT: "${BLAZE_PORT}"
ENV VALIDATOR_PORT: "${VALIDATOR_PORT}"
ENV PACKAGES "${PACKAGES}"

VOLUME ["/app/profiles"]
VOLUME ["/app/terminology_data"]

COPY ./upload.sh /app/upload.sh
WORKDIR /app
RUN python -m pip install fhir-populator
# Run FHIR Populator and validation service to upload StructureDefinitions to server and have service available
ENTRYPOINT sh upload.sh && python -m fhir_populator --endpoint http://blaze:8080/fhir --get-dependencies --non-interactive --only-put --package ${PACKAGES} && python -m ABIDE_validation 8082 -v http://fhir-marshal:8081 -s http://blaze:8080/fhir/ && flask run --host 0.0.0.0 --port 8082