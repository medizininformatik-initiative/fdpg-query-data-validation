#!/bin/bash
export $(grep -v '^#' .env | xargs)
docker-compose -p "${PROJECT_CONTEXT}" -f docker-compose-validation.yml down
docker-compose -p "${PROJECT_CONTEXT}" -f docker-compose-vms.yml down
echo "Shutdown finished"