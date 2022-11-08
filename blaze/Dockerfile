FROM samply/blaze:0.17
ARG BLAZE_PORT
ARG JAVA_TOOL_OPTIONS
# Install curl for healthcheck
USER root
RUN apt-get -y update && apt-get -y install curl
# Run Blaze
ENV STORAGE="standalone"
ENV INDEX_DB_DIR="/app/data/index"
ENV TRANSACTION_DB_DIR="/app/data/transaction"
ENV RESOURCE_DB_DIR="/app/data/resource"
CMD ["java", "-jar", "blaze-standalone.jar", "-m", "blaze.core"]