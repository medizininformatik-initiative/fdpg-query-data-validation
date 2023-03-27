#!/bin/bash

# Load environment variables from .env file
set -o allexport
source .env
set +o allexport

# Run Docker Compose
docker compose -f docker-compose_pdf_report.yml up -d