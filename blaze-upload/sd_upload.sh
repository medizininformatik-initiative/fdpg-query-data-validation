#!/bin/bash
echo "Uploading profiles from Simplifier to Blaze@${BLAZE_SERVER_URL}"
echo "$(python -m fhir_populator --endpoint ${BLAZE_SERVER_URL} --get-dependencies --non-interactive --only-put --package de.medizininformatikinitiative.kerndatensatz.laborbefund@1.0.7-alpha1 de.medizininformatikinitiative.kerndatensatz.person@2.0.0-ballot2 de.medizininformatikinitiative.kerndatensatz.diagnose@2.0.0-alpha3 de.medizininformatikinitiative.kerndatensatz.medikation@1.0.11 de.medizininformatikinitiative.kerndatensatz.prozedur@2.0.0-alpha5 de.medizininformatikinitiative.kerndatensatz.biobank@1.0.3 de.einwilligungsmanagement@1.0.12)"
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
