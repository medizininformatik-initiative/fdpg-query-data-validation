#!/bin/bash
sh initialize-env-file.sh
export $(grep -v '^#' .env | xargs)
echo "Running test script"
docker-compose -p ${PROJECT_CONTEXT:-feasibility-deploy} -f docker-compose-extraction.yml up
echo "Tests concluded. Generated file can be found under ${REPORT_LOCATION}"