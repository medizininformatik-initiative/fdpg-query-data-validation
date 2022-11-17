#!/bin/bash
echo "Uploading profiles from Simplifier to Blaze@${BLAZE_SERVER_URL}"
python -m fhir_populator --endpoint "${BLAZE_SERVER_URL}" --get-dependencies --non-interactive --only-put --package ${PACKAGES}
echo "Uploading own StructureDefinition instances to Blaze@${BALZE_SERVER_URL}"
for file in -exec $(find ./fhir_profiles -name '*.json')
do
  curl -vX POST -d @"$file" -H "Content-Type: application/json" "${BLAZE_SERVER_URL}/StructureDefinition"
  echo "Uploading ${file}"
done
for file in -exec $(find ./fhir_profiles -name '*.xml')
do
  curl -vX POST -d @"$file" -H "Content-Type: application/xml" "${BLAZE_SERVER_URL}/StructureDefinition"
  echo "Uploading ${file}"
done
echo "Upload finished"
