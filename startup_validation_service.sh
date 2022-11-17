#!/bin/bash
export $(grep -v '^#' .env | xargs)
docker-compose -p ${PROJECT_CONTEXT:-feasibility-deploy} -f docker-compose-validation.yml up -d