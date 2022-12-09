import argparse
import os
import time
import traceback
import requests
import json

from IssueMap import IssueMap
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
    except Exception as error:
        raise Exception("Simple test failed", error)


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
                general, mapped_issues, errors, num_found = run_total_tests(client, resource_type, parameters, total,
                                                                            v_url, "application/json")
                obs_reports[obs_code] = {'count': num_found,
                                         'issues': mapped_issues}
                error_issues['issue'].extend(errors)
                general_issues['issue'].extend(general)
            report[resource_type] = obs_reports
        else:
            parameters = {'_count': count, '_profile': type_profiles[resource_type]}
            general, mapped_issues, errors, num_found = run_total_tests(client, resource_type, parameters, total, v_url,
                                                                        "application/json")
            report[resource_type] = {'count': num_found,
                                     'issues': mapped_issues}
            error_issues['issue'].extend(errors)
            general_issues['issue'].extend(general)
    report['general'] = general_issues
    report['error'] = error_issues
    print("All done")
    return report


# Returns issues grouped by the instance ID
def run_total_tests(client, resource_type, parameters, total, v_url, content_type):
    general_issues = list()
    issues = list()
    error_issues = list()
    paging_result = None
    num_found = 0
    try:
        summary_params = {'_summary': 'count'}
        summary_params.update(parameters)
        result = client.get(resource_type, parameters=summary_params, paging=False)
        print(result['total'])
        num_found = min(result['total'], total)
        paging_result = client.get(resource_type, parameters, max_cnt=total)
    except Exception as error:
        msg = f"Failed to run tests for Observation with parameters {parameters} and excluded result in " \
              f"report "
        print(f"{msg}:\n{traceback.format_exception(error)}")
        error_issues.append(generate_issue('error', 'processing', msg))
    if paging_result is None or paging_result.is_empty():
        param_string = '&'.join([f'{param}={value}' for param, value in parameters.items()])
        print(f"Excluding profile constraint for {resource_type}?{param_string} since no data matches it")
        general_issues.append(
            generate_issue("warning", "processing", f"No data matching {resource_type}?{param_string}"))
        parameters.pop('_profile', None)
        try:
            paging_result = client.get(resource_type, parameters, max_cnt=total)
        except Exception as error:
            msg = f"Failed to run tests for Observation with parameters {parameters} and excluded result in " \
                  f"report "
            print(f"{msg}:\n{traceback.format_exception(error)}")
            error_issues.append(generate_issue('error', 'processing', msg))
    if paging_result is None or paging_result.is_empty():
        param_string = '&'.join([f'{param}={value}' for param, value in parameters.items()])
        msg = f"No matches found for {resource_type}?{param_string}"
        print(msg)
        general_issues.append(generate_issue("warning", "processing", msg))
    else:
        print(f"Found {paging_result.get_total()} for {resource_type}")
        issue_set = IssueSet()
        for idx, bundle in enumerate(paging_result):
            print(f"Status: {idx} of {int(max(total / parameters['_count'], 1))} requests processed")
            try:
                op_outcome = simple_test(json.dumps(bundle), v_url, content_type)
                for issue in op_outcome.get('issue', []):
                    issue_set.add(issue)
            except Exception as error:
                msg = f"Failed to run tests for Observation with parameters {parameters} and excluded result in " \
                      f"report "
                print(f"{msg}:\n{traceback.format_exception(error)}")
                error_issues.append(generate_issue('error', 'processing', msg))
        issues.extend(issue_set.get_issues())
    print(f"All done for initial request @{resource_type} with {str(parameters)}")
    return general_issues, issues, error_issues, num_found


# TODO
def refine_report(report):
    aggregate_map = {'distribution': report['distribution'],
                     'validation': dict()}
    for resource_type, resource_report in report['validation'].items():
        if resource_type == 'Observation':
            obs_map = dict()
            aggregate_map[resource_type] = obs_map
            for obs_code, obs_report in resource_report.items():
                issue_map = IssueMap()
                obs_map[obs_code] = issue_map
                for op_outcome in obs_report:
                    process_op_outcome(op_outcome, issue_map)
        else:
            issue_map = IssueMap()
            aggregate_map[resource_type] = issue_map
            for op_outcome in resource_report:
                process_op_outcome(op_outcome, issue_map)
    return aggregate_map


# TODO
def process_aggregate():
    pass


def process_op_outcome(op_outcome, issue_map):
    for issue in op_outcome['issue']:
        issue_map.put_issue(issue)


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
                    response = client.get(resource_type, parameters=params, paging=False)
                    search_path_results[value] = response.get('total')
                except Exception as error:
                    print(f"Failed distribution analysis for {resource_type}::{search_path}::{value}: "
                          f"Results will be excluded")
                    traceback.print_tb(error.__traceback__)
            results[resource_type][search_path] = search_path_results
    return results


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
    fhir_client = FHIRClient(url, user, pw, fhir_token, fhir_proxy, certificate)
    raw_report = dict()
    try:
        raw_report["distribution"] = analyse_distribution(fhir_client)
    except Exception as e:
        print(f"Distribution analysis failed and will not be included:\n "
              f"{traceback.format_exception(None, e, e.__traceback__)}", flush=True)
    try:
        raw_report["validation"] = run_test(fhir_client, total_sample_size, resource_count_per_page,
                                            validation_endpoint)
    except (ConnectionError, requests.Timeout, requests.HTTPError) as e:
        print("Report generation stopped due to missing connection to FHIR server", flush=True)
        print(str(e), flush=True)
    try:
        raw_report_name = f'raw_report_{round(time.time() * 1000)}.json'
        with open(os.path.join('report', raw_report_name), mode='w+') as raw_report_file:
            raw_report_file.write(json.dumps(raw_report, indent=4))
            print(f"Generated reports: {raw_report_name}")
    except Exception as e:
        print("Could not write report")
        print(str(e))
