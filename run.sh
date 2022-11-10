#!/bin/bash
export "$(cat .env | xargs)"
echo "Running test script"
docker-compose -p feasibility-deploy -f docker-compose2.yml up
echo "Tests concluded. Generated file can be found under $REPORT_LOCATION"