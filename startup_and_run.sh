#!/bin/bash
export $(grep -v '^#' .env | xargs)
docker-compose -p "${PROJECT_CONTEXT:-feasibility-deploy}" up -d
