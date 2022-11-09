#!/bin/bash
export "$(cat .env | xargs)"
echo "Running test script"
docker-compose up -f docker-compose2.yml
docker-compose down -f docker-compose2.yml
echo "Tests concluded. Generated file can be found under $REPORT_LOCATION"