#!/bin/bash
export $(grep -v '^#' .env | xargs)
docker compose -p "${PROJECT_CONTEXT}" -f docker-compose.yml down
docker volume rm validation-structure-definition-server-data
echo "Shutdown finished"
