#!/bin/bash
# export $(grep -v '^#' .env | xargs)
source .env
docker-compose -p "${PROJECT_CONTEXT:-feasibility-deploy}" up -d
