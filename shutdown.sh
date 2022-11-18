#!/bin/bash
export $(grep -v '^#' .env | xargs)
docker-compose -p "${PROJECT_CONTEXT}" -f docker-compose.yml down
echo "Shutdown finished"
