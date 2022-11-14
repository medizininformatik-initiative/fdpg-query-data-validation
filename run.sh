#!/bin/bash
export "$(cat .env | xargs)"
REPORT_LOCATION:-${REPORT_LOCATION}
echo "Running test script"
docker-compose -p ${PROJECT_CONTEXT:-feasibility-deploy} -f docker-compose-extraction.yml up
echo "Tests concluded. Generated file can be found under ${REPORT_LOCATION}"