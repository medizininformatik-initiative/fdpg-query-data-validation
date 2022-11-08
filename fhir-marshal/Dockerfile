FROM ghcr.io/itcr-uni-luebeck/fhir-marshal:latest

COPY ./application.yml application.yml

EXPOSE 8081

ENTRYPOINT ["java", "-Dserver.port=8081", "-jar", "fhir-marshal.jar", "--spring.config.location=file:application.yml"]