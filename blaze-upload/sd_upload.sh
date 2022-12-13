#!/bin/bash
shopt -s globstar
echo "Uploading profiles from Simplifier to Blaze@${BLAZE_SERVER_URL}"
http_proxy=''
https_proxy=''
if [[ -z "${HTTP_PACKAGE_DOWNLOAD_PROXY}"]]; then
  http_proxy="${HTTP_PACKAGE_DOWNLOAD_PROXY}"
fi
if [[ -z "${HTTPS_PACKAGE_DOWNLOAD_PROXY}"]]; then
  https_proxy="${HTTPS_PACKAGE_DOWNLOAD_PROXY}"
fi
python -m fhir_populator --endpoint "${BLAZE_SERVER_URL}" --get-dependencies --non-interactive --only-put --http-proxy ${http_proxy} --https-proxy ${https_proxy} --package ${PACKAGES}
echo "Uploading own StructureDefinition instances to Blaze@${BALZE_SERVER_URL}"
for file in ./fhir_profiles/**/*.json
do
  id="$(cat $file | jq -r '.id')"
  curl -vX PUT -d @"$file" -H "Content-Type: application/json" "${BLAZE_SERVER_URL}/StructureDefinition/${id}"
  echo "Uploading ${file}"
done
echo "Upload finished"
