#!/bin/bash
export "$(grep -v '^#' .env | xargs)"
docker-compose -p "${PROJECT_CONTEXT}" -f validation_service/docker-compose-validation.yml down
docker-compose -p "${PROJECT_CONTEXT}" -f validation_mapper_service/docker-compose-vms.yml down
echo "Shutdown finished"