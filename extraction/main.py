import argparse
import os
import time
import traceback
import requests
import json

from IssueSet import IssueSet
from fhir import FHIRClient, HttpError

cert_dir = 'certificates'
distribution_tests_file = os.path.join('distribution_tests', 'distribution_tests.json')


def configure_argparser():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('url', action='store', help="URL of the FHIR server from which to pull the data")
    arg_parser.add_argument('-u', '--user', help='basic auth user fhir server', nargs="?", default="")
    arg_parser.add_argument('-p', '--password', help='basic auth pw fhir server', nargs="?", default="")
    arg_parser.add_argument('-ft', '--fhir-token', help='token auth fhir server', nargs="?", default=None)
    arg_parser.add_argument('--http-proxy', help='http proxy url for your fhir server - None if not set here',
                            nargs="?", default=None)
    arg_parser.add_argument('--https-proxy', help='https proxy url for your fhir server - None if not set here',
                            nargs="?",
                            default=None)
    arg_parser.add_argument('--cert', help='path to certificate file used to verify requests', nargs="?", default=None)
    arg_parser.add_argument('-t', '--total', action='store', default=500, type=int,
                            help="Total amount of resource instances"
                                 " to pull for testing")
    arg_parser.add_argument('-c', '--count', action='store', default=100, type=int,
                            help="Amount of resource instances to "
                                 "pull each request regarding page size")
    arg_parser.add_argument('-v', '--validation-endpoint', action='store', default='http://localhost:8082/validate',
                            help='URL of the validation endpoint used for validating the data')
    arg_parser.add_argument('--verify', action='store', type=str, choices=['true', 'false'], default='true',
                            help='Indicates whether SSL certificates will be validated')
    return arg_parser


def make_bundle(bundles):
    collective_bundle = {"resourceType": "Bundle",
                         "type": "transaction",
                         "entry": list()}
    for bundle in bundles:
        entry = bundle.get('entry')
        if isinstance(entry, list):
            collective_bundle['entry'].extend(bundle.get('entry'))
    return collective_bundle


def simple_test(data, v_url, content_type):
    try:
        response = requests.post(url=v_url, data=data, headers={"Content-Type": content_type})
        return json.loads(response.text)
    except Exception as simple_test_error:
        raise Exception("Simple test failed", simple_test_error)


def observation_test(data, v_url, content_type):
    results = dict()
    for k, v in data.items():
        try:
            response = simple_test(v, v_url, content_type)
        except Exception as exception:
            response = str(exception)
        results[k] = response
    return results


def map_bundle_id_to_entry_idx(bundle):
    return [entry['resource']['id'] for entry in bundle.get('entry', [])]


def map_issues_to_entry(bundle, op_outcome):
    id_index = map_bundle_id_to_entry_idx(bundle)
    id_issue_map = dict()
    for issue in op_outcome.get('issue', []):
        if 'location' in issue:
            fhir_path = issue.get('location', [])[0]
            # Due to using the HAPI Validator and Bundle instances the index of the resource instance in the entry
            # list is assumed to be contained in the second component of the FHIR path expression Form:
            # Bundle.entry[x]... where x is some number
            entry_idx = int(fhir_path.split('.')[1][6:-1])
            resource_id = id_index[entry_idx]
            issue_entry = {'issue': issue, 'element': get_issue_element(bundle, fhir_path)}
            if resource_id in id_issue_map:
                id_issue_map[resource_id].append(issue_entry)
            else:
                id_issue_map[resource_id] = [issue_entry]
        else:
            if 'not-assignable' in id_issue_map:
                id_issue_map['not-assignable'].append(issue)
            else:
                id_issue_map['not-assignable'] = [issue]
    return id_issue_map


def get_issue_element(_bundle, _fhir_path_expr):
    return ""


def generate_issue(severity, issue_type, diagnostics):
    return {"severity": severity,
            "type": issue_type,
            "diagnostics": diagnostics}


test_type = {"Condition": simple_test,
             "Observation": observation_test,
             "Medication": simple_test,
             "MedicationAdministration": simple_test,
             "MedicationStatement": simple_test,
             "Procedure": simple_test,
             "Specimen": simple_test,
             "Consent": simple_test}

type_profiles = {
    "Condition": "https://www.medizininformatik-initiative.de/fhir/core/modul-diagnose/StructureDefinition/Diagnose",
    "Observation": "https://www.medizininformatik-initiative.de/fhir/core/modul-labor/StructureDefinition"
                   "/ObservationLab",
    "Medication": "https://www.medizininformatik-initiative.de/fhir/core/modul-medikation/StructureDefinition"
                  "/Medication",
    "MedicationAdministration": "https://www.medizininformatik-initiative.de/fhir/core/modul-medikation"
                                "/StructureDefinition/MedicationAdministration",
    "MedicationStatement": "https://www.medizininformatik-initiative.de/fhir/core/modul-medikation"
                           "/StructureDefinition/MedicationStatement",
    "Procedure": "https://www.medizininformatik-initiative.de/fhir/core/modul-prozedur/StructureDefinition/Procedure",
    "Specimen": "https://www.medizininformatik-initiative.de/fhir/ext/modul-biobank/StructureDefinition/SpecimenCore",
    "Consent": "https://www.medizininformatik-initiative.de/fhir/modul-consent/StructureDefinition/mii-pr-consent"
               "-einwilligung"}


def run_test(client, total, count, v_url):
    print(f"Running tests for the following resources : {', '.join(type_profiles.keys())}")
    report = dict()
    error_issues = {"issue": []}
    general_issues = {"issue": []}
    # aggregated_report = dict()
    for resource_type, test in test_type.items():
        print(f"Running tests for {resource_type}")
        # Fetch data from FHIR server
        if resource_type == 'Observation':
            val_mapping = json.load(open('./maps/validation_mapping.json'))
            obs_reports = dict()
            for obs_code, _ in val_mapping['Observation'].items():
                search_string = f"http://loinc.org|{obs_code}"
                parameters = {'code': search_string, '_profile': type_profiles['Observation'], '_count': count}
                get_and_append_issues(client, resource_type, parameters, total, v_url, key=obs_code, report=obs_reports,
                                      error_issues=error_issues, general_issues=general_issues)
            report[resource_type] = obs_reports
        else:
            parameters = {'_count': count, '_profile': type_profiles[resource_type]}
            get_and_append_issues(client, resource_type, parameters, total, v_url, key=resource_type, report=report,
                                  error_issues=error_issues, general_issues=general_issues)
    report['general'] = general_issues
    report['error'] = error_issues
    print("All done")
    return report


def get_and_append_issues(client, resource_type, parameters, total, v_url, key, report, error_issues, general_issues):
    general, mapped_issues, errors, num_found = run_total_tests(client, resource_type, parameters, total, v_url,
                                                                "application/json")
    if len(mapped_issues) > 1 or (len(mapped_issues) == 1 and mapped_issues[0].get(
            'diagnostics') != 'No issues detected during validation'):
        report[key] = {'count': num_found,
                       'issues': mapped_issues}
    error_issues['issue'].extend(errors)
    general_issues['issue'].extend(general)


# Returns issues grouped by the instance ID
def run_total_tests(client, resource_type, parameters, total, validation_url, content_type):
    general_issues = list()
    issues = list()
    error_issues = list()
    paging_result, num_of_instances_to_process, request_error = try_request_with_profile(resource_type, parameters,
                                                                                         total, client)
    if request_error is not None:
        error_issues.append(request_error)
    if paging_result is None or paging_result.is_empty():
        param_string = '&'.join([f'{param}={value}' for param, value in parameters.items()])
        print(f"Excluding profile constraint for {resource_type}?{param_string} since no data matches it")
        general_issues.append(
            generate_issue("warning", "processing", f"No data matching {resource_type}?{param_string}"))
        paging_result, num_of_instances_to_process, request_error = try_request_with_profile(resource_type, parameters,
                                                                                             total, client)
    if paging_result is None or paging_result.is_empty():
        param_string = '&'.join([f'{param}={value}' for param, value in parameters.items()])
        msg = f"No matches found for {resource_type}?{param_string}"
        print(msg)
        general_issues.append(generate_issue("warning", "processing", msg))
    else:
        print(f"Found {paging_result.total} for {resource_type}")
        validation_issues, validation_error_issues = validate_data_in_paging_result(paging_result, validation_url,
                                                                                    parameters, content_type)
        issues.extend(validation_issues)
        error_issues.extend(validation_error_issues)
    print(f"All done for initial request @{resource_type} with {str(parameters)}")
    return general_issues, issues, error_issues, num_of_instances_to_process


def try_request_with_profile(resource_type, parameters, total, client):
    paging_result = None
    num_of_instances_to_process = 0
    request_error = None
    try:
        num_of_instances_found = client.count_resources(resource_type=resource_type, params=parameters)
        num_of_instances_to_process = min(num_of_instances_found, total)
        paging_result = client.get(resource_type, parameters, max_cnt=total)
    except HttpError as http_error:
        msg = f"Failed to run tests for Observation with parameters {parameters} and excluded result in report "
        print(f"{msg}:\n{traceback.format_exception(http_error)}")
        request_error = generate_issue('error', 'processing', msg)
    return paging_result, num_of_instances_to_process, request_error


def try_request_without_profile(resource_type, parameters, total, client):
    paging_result = None
    num_of_instances_to_process = 0
    request_error = None
    parameters.pop('_profile', None)
    try:
        paging_result = client.get(resource_type, parameters, max_cnt=total)
        num_of_instances_to_process = min(paging_result.total, total)
    except HttpError as http_error:
        msg = f"Failed to run tests for Observation with parameters {parameters} and excluded result in " \
              f"report "
        print(f"{msg}:\n{traceback.format_exception(http_error)}")
        request_error = generate_issue('error', 'processing', msg)
    return paging_result, num_of_instances_to_process, request_error


def validate_data_in_paging_result(paging_result, validation_url, parameters, content_type, ):
    issue_set = IssueSet()
    error_issues = []
    for idx, bundle in enumerate(paging_result):
        try:
            op_outcome = simple_test(json.dumps(bundle), validation_url, content_type)
            for issue in op_outcome.get('issue', []):
                issue_set.add(issue)
        except Exception as test_error:
            msg = f"Failed to run tests for Observation with parameters {parameters} and excluded result in " \
                  f"report "
            print(f"{msg}:\n{traceback.format_exception(test_error)}")
            error_issues.append(generate_issue('error', 'processing', msg))
        print(
            f"Status: {idx + 1} of {max(int(paging_result.total / parameters['_count']), 1)} requests processed")
    issues = issue_set.get_issues()
    return issues, error_issues


def analyse_distribution(client):
    print("Running distribution analysis")
    count_searches = json.loads(open(distribution_tests_file).read())
    results = dict()
    for resource_type, searches in count_searches.items():
        print(f"Distribution test for {resource_type}")
        response = client.get(resource_type, parameters={'_summary': 'count'}, paging=False)
        type_total = response['total']
        results[resource_type] = {'total': type_total}
        for search_path, values in searches.items():
            search_path_results = dict()
            for value in values:
                try:
                    # Insert value into search path and split for insertion as param into FHIR client's get function
                    search_path_param = search_path.replace('?', value).split('=')
                    params = {search_path_param[0]: search_path_param[1],
                              '_summary': 'count'}
                    search_path_results[value] = client.count_resources(resource_type, params=params)
                except Exception as analysis_error:
                    print(f"Failed distribution analysis for {resource_type}::{search_path}::{value}: "
                          f"Results will be excluded")
                    traceback.print_tb(analysis_error.__traceback__)
            results[resource_type][search_path] = search_path_results
    return results


def write_raw_report(raw_report):
    try:
        raw_report_name = f'raw_report_{round(time.time() * 1000)}.json'
        with open(os.path.join('report', raw_report_name), mode='w+') as raw_report_file:
            raw_report_file.write(json.dumps(raw_report, indent=4))
            print(f"Generated reports: {raw_report_name}")
    except Exception as writing_error:
        print("Could not write report")
        print(traceback.format_exception(writing_error))


if __name__ == '__main__':
    parser = configure_argparser()
    args = parser.parse_args()
    url = args.url
    user = args.user
    pw = args.password
    fhir_token = args.fhir_token
    fhir_proxy = {'http': args.http_proxy,
                  'https': args.https_proxy}
    certificate = None
    if args.cert is not None:
        certificate = args.cert
    total_sample_size = args.total
    resource_count_per_page = args.count
    validation_endpoint = args.validation_endpoint
    if args.verify == 'false':
        verify_ssl_cert = False
    else:
        verify_ssl_cert = True
    fhir_client = FHIRClient(url, user, pw, fhir_token, fhir_proxy, certificate, verify=verify_ssl_cert)
    raw_report = dict()
    try:
        raw_report["distribution"] = analyse_distribution(fhir_client)
    except Exception as error:
        print(f"Distribution analysis failed and will not be included:\n "
              f"{traceback.format_exception(error)}", flush=True)
    try:
        raw_report["validation"] = run_test(fhir_client, total_sample_size, resource_count_per_page,
                                            validation_endpoint)
    except (ConnectionError, requests.Timeout, requests.HTTPError) as error:
        print("Report generation stopped due to missing connection to FHIR server", flush=True)
        print(traceback.format_exception(error), flush=True)
    write_raw_report(raw_report)
