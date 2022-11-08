for json_file in terminology_data/*.json
do
  curl -vX POST -d @$json_file -H "Content-Type: application/json" http://terminology-service:8083/fhir/ValueSet
done