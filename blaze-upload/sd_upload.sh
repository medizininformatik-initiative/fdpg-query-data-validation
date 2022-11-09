#!/bin/bash
for i in {0..101}
do
  if [ "$i" -eq 101 ]
  then
    echo "Failed to connect to Blaze"
    exit 1
  fi
  echo "Waiting for Blaze ($i/100)"
  result=$(curl --fail http://localhost:"$BLAZE_SERVER_URL"/health || exit 1)
  exit_code=$?
  echo "$result"
  if [ "$exit_code" -eq 0 ]
  then
     break
  fi
  sleep 5
done
echo "Connected to Blaze@${BLAZE_SERVER_URL}"
# echo "$(python -m fhir_populator --endpoint ${BLAZE_SERVER_URL} --get-dependencies --non-interactive --only-put --package ${PACKAGES})"
echo "Uploading own StructureDefinition instances to Blaze@${BALZE_SERVER_URL}"
for file in -exec $(find ./profiles -name '*.json')
do
  curl -vX POST -d @"$file" -H "Content-Type: application/json" "${BLAZE_SERVER_URL}"
done
for file in -exec $(find ./profiles -name '*.xml')
do
  curl -vX POST -d @"$file" -H "Content-Type: application/xml" "${BLAZE_SERVER_URL}"
done
echo "Upload finished"