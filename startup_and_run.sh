#!/bin/bash
export "$(cat .env | xargs)"
docker-compose -p ${PROJECT_CONTEXT:-feasibility-deploy} up -d -f docker-compose-validation.yml
for i in {0..101}
do
  if [ "$i" -eq 101 ]
  then
    echo "Failed to start FHIR Marshal"
    exit 1
  fi
  echo "Waiting for FHIR Marshal ($i/100)"
  result=$(curl --fail http://localhost:"$VALIDATOR_PORT"/fhir/metadata || exit 1)
  exit_code=$?
  echo "$result"
  if [ "$exit_code" -eq 0 ]
  then
     break
  fi
  sleep 10
done
echo "FHIR Marshal successfully started"
echo "Starting Validation Profile Mapper"
docker-compose -p ${PROJECT_CONTEXT:-feasibility-deploy} up -d -f docker-compose-vms.yml
for i in {0..101}
do
  if [ "$i" -eq 101 ]
  then
    echo "Failed to start Validation Profile Mapper"
    exit 1
  fi
  echo "Waiting for Validation Profile Mapper ($i/100)"
  result=$(curl --fail http://localhost:"$VALIDATOR_PORT"/validate || exit 1)
  exit_code=$?
  echo "$result"
  if [ "$exit_code" -eq 0 ]
  then
     break
  fi
  sleep 10
done
echo "Validation Profile Mapper successfully started"
REPORT_LOCATION:-${REPORT_LOCATION}
echo "Running test script"
docker-compose -p ${PROJECT_CONTEXT:-feasibility-deploy} -f docker-compose-extraction.yml up
echo "Tests concluded. Generated file can be found under ${REPORT_LOCATION}"