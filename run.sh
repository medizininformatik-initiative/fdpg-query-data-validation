#!/bin/bash
set -o allexport
source .env
set +o allexport
docker compose -p "${PROJECT_CONTEXT:-feasibility-deploy}" restart fhir-data-extraction