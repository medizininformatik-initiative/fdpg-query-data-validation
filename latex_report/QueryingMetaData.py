import glob
import json


class QueryingMetaData:
    def __init__(self, json_file):
        with open(json_file) as querying_meta_data_file:
            json_data = json.load(querying_meta_data_file)

        self.resource_type = json_data.get("resource_type")
        self.fhir_paths = [
            json_data.get("term_code_defining_id"),
            json_data.get("value_defining_id"),
            json_data.get("time_restriction_defining_id")
        ]
        attribute_paths = list(json_data.get("attribute_defining_id_type_map", {}).keys())
        self.fhir_paths.extend(attribute_paths)


def get_querying_meta_data_by_type(folder_path):
    """
    Finds unique FHIR resources in a folder and combines their FHIR paths.

    Args:
        folder_path (str): The path to the folder containing the JSON files.

    Returns:
        Dictionary with resource type as key and FhirResource object as value.
    """
    json_files = glob.glob(f"{folder_path}/*.json")
    resources = {}
    for json_file in json_files:
        with open(json_file, encoding="utf-8") as f:
            json_data = json.load(f)
        resource_type = json_data.get("resource_type")
        if resource_type not in resources:
            resources[resource_type] = QueryingMetaData(json_file)
        else:
            resources[resource_type].fhir_paths = set(resources[resource_type].fhir_paths).union(
                [json_data.get("term_code_defining_id"),
                 json_data.get("value_defining_id"),
                 json_data.get("time_restriction_defining_id")] +
                list(json_data.get("attribute_defining_id_type_map", {}).keys()))
    return resources