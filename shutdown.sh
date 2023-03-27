#!/bin/bash
# Load environment variables from .env file
set -o allexport
source .env
set +o allexport
docker compose -p "${PROJECT_CONTEXT}" -f docker-compose.yml down
docker volume rm validation-structure-definition-server-data
echo "Shutdown finished"
