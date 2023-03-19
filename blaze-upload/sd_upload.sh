#!/bin/bash
shopt -s globstar
echo "Uploading profiles from Simplifier to Blaze@${BLAZE_SERVER_URL}"
http_proxy=''
https_proxy=''
if [[ -n "${HTTP_PACKAGE_DOWNLOAD_PROXY}" ]]
then
  http_proxy="--http-proxy ${HTTP_PACKAGE_DOWNLOAD_PROXY} "
fi
if [[ -n "${HTTPS_PACKAGE_DOWNLOAD_PROXY}" ]]
then
  https_proxy="--https-proxy ${HTTPS_PACKAGE_DOWNLOAD_PROXY} "
fi
python -m fhir_populator --endpoint "${BLAZE_SERVER_URL}" --get-dependencies --non-interactive --log-level ERROR --only-put ${http_proxy}${https_proxy}--package ${PACKAGES}
