#!/bin/bash
export "$(cat .env | xargs)"
docker-compose up -d -f docker-compose0.yml
for i in {0..101}
do
  if [ "$i" -eq 101 ]
  then
    echo "Failed to start FHIR Marshal"
    exit 1
  fi
  echo "Waiting for Validation API ($i/100)"
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
echo "Starting Validation API"
docker-compose up -d -f docker-compose1.yml
for i in {0..101}
do
  if [ "$i" -eq 101 ]
  then
    echo "Failed to start Validation API"
    exit 1
  fi
  echo "Waiting for Validation API ($i/100)"
  result=$(curl --fail http://localhost:"$VALIDATOR_PORT"/fhir/metadata || exit 1)
  exit_code=$?
  echo "$result"
  if [ "$exit_code" -eq 0 ]
  then
     break
  fi
  sleep 10
done
echo "Validation API successfully started"