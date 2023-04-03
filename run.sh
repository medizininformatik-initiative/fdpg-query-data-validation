#!/bin/bash
set -o allexport
source .env
set +o allexportsource .env
docker compose -p "${PROJECT_CONTEXT:-feasibility-deploy}" restart fhir-data-extraction