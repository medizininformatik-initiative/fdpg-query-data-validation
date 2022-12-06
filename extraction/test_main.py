import glob
import json
import os
import traceback
import dotenv
import pytest

from requests import JSONDecodeError
from testing_utilities import run_command, health_check
from main import simple_test, generate_issue


docker_compose_validation = os.path.join('.', 'validation_service', 'docker-compose-validation.yml')
docker_compose_vms = os.path.join('.', 'validation_mapper_service', 'docker-compose-vms.yml')
project_context = 'testing'
env_file = '.env'
fhir_profile_dir = os.path.join('..', 'fhir_profiles')
value_set_dir = os.path.join('..', 'value_sets')
validation_mapping_dir = os.path.join('..', 'maps')
test_data = os.path.join('test', 'data')
valid_data = glob.glob(pathname=os.path.join('*', '*_pass.json'), root_dir=test_data)
invalid_data = glob.glob(pathname=os.path.join('*', '*_fail.json'), root_dir=test_data)
validation_url = 'http://localhost:8092/validate'
validator_url = 'http://localhost:8091/validate'
health_check_bundle = {"resourceType": "Bundle",
                       "type": "transaction",
                       "entry": []}


def test_simple_test():
    print("Testing simple_test method")
    valid_condition_bundle_file = open(os.path.join(test_data, 'condition', 'condition_pass.json'), encoding='utf_8')
    valid_condition_bundle = valid_condition_bundle_file.read()
    invalid_condition_bundle_file = open(os.path.join(test_data, 'condition', 'condition_fail.json'), encoding='utf_8')
    invalid_condition_bundle = invalid_condition_bundle_file.read()

    print("Testing with valid data")
    headers = {'Content-Type': 'application/json'}
    try:
        operation_outcome = simple_test(data=valid_condition_bundle, v_url=validation_url,
                                        content_type='application/json')
        resource_type_test(operation_outcome, 'OperationOutcome')
        issues = operation_outcome.get('issues', [])
        if len(issues) == 1:
            assert issues.get(0).get('diagnostics') == 'No issues detected during validation', \
                f"No issues should've been detected. Issues were: {issues}"
    except JSONDecodeError as error:
        print("Response body could not be parsed as JSON object. Partially skipping tests.")
        print(traceback.format_exception(error))

    print("Testing with invalid data")
    try:
        operation_outcome = simple_test(data=valid_condition_bundle, v_url=validation_url,
                                        content_type='application/json')
        resource_type_test(operation_outcome, 'OperationOutcome')
        issues = operation_outcome.get('issue', [])
        has_severe_issues = False
        for issue in issues:
            severity = issue.get('severity')
            if severity == 'warning' or severity == 'error' or severity == 'fatal':
                has_severe_issues = True
                break
        assert has_severe_issues, f"Issues of severity higher than 'information' should've been found:" \
                                  f"\n{operation_outcome}"
    except JSONDecodeError as error:
        print("Response body could not be parsed as JSON object. Partially skipping tests.")
        print(traceback.format_exception(error))


def test_observation_test():
    pass


def test_generate_issue():
    print("Testing generate_issue method")
    issue_severity = "error"
    issue_type = "processing"
    diagnostics = "Something failed"
    issue = generate_issue(severity=issue_severity, issue_type=issue_type, diagnostics=diagnostics)
    assert issue['severity'] == issue_severity, f"Issue severities don't match: {issue['severity']} (present) vs" \
                                                f" {issue_severity} (expected)"
    assert issue['type'] == issue_type, f"Issue types don't match: {issue['type']} (present) vs {issue_type} (expected)"
    assert issue['diagnostics'] == diagnostics, f"Diagnostics don't match: {issue['diagnostics']} (present) vs" \
                                                f" {diagnostics} (expected)"


def test_run_total_tests():
    print("Testing run_total_tests method")


def parse_json(data):
    try:
        return json.loads(data)
    except JSONDecodeError as exception:
        raise AssertionError(f"Could not parse response as JSON dict:\n{data}", exception)


def resource_type_test(resource_instance, expected_resource_type):
    resource_type = resource_instance.get('resourceType', None)
    assert resource_type == expected_resource_type, f"Returned resource instance was not of type" \
                                                    f" '{expected_resource_type}'" \
                                                    f" but was instead of type {resource_type}"


@pytest.fixture(scope="session")
def prepare_setup(request):
    setup()
    request.addfinalizer(teardown)


def setup():
    print("Starting setup")
    os.chdir(os.path.join('.', '..'))
    print(f"Loading environment variables from {env_file}")
    env_dict = dotenv.dotenv_values(env_file)
    env_dict['PROJECT_CONTEXT'] = project_context
    env_dict['FHIR_PROFILE_DIRECTORY'] = fhir_profile_dir
    env_dict['VALUE_SET_DIRECTORY'] = value_set_dir
    env_dict['VALIDATION_MAPPING_DIRECTORY'] = validation_mapping_dir
    print("Starting containers")
    docker_compose_template = "docker compose -p {} -f {} --env-file {} up -d"

    print("Starting validation containers")
    command = docker_compose_template.format(project_context, os.path.join(os.getcwd(), docker_compose_validation),
                                             os.path.join(os.getcwd(), env_file))
    run_command(command, f"Failed to start validation containers", exit_on_err=True, env=env_dict, cwd=os.getcwd())
    print("Waiting until validation services are ready")
    health_check_body = json.dumps(health_check_bundle)
    try:
        health_check(health_check_url=validator_url, interval=1, attempts=60, start=0, body=health_check_body)
    except TimeoutError as error:
        msg = f"Validation services were not ready in time\n{traceback.format_exception(error)}"
        pytest.exit(msg)

    print("Starting validation mapping service container")
    command = docker_compose_template.format(project_context, os.path.join(os.getcwd(), docker_compose_vms),
                                             os.path.join(os.getcwd(), env_file))
    run_command(command, f"Failed to start validation mapping service container", exit_on_err=True, env=env_dict,
                cwd=os.getcwd())
    print("Waiting until validation mapping service is ready")
    try:
        health_check(health_check_url=validation_url, interval=1, attempts=60, start=0)
    except TimeoutError as error:
        msg = f"Validation mapping service was not ready in time\n{traceback.format_exception(error)}"
        pytest.exit(msg)


def teardown():
    print("Starting teardown")
    print("Removing containers and volumes")
    docker_compose_down_template = "docker compose -p {} -f {} down"

    print("Removing validation mapping service container")
    command = docker_compose_down_template.format(project_context, docker_compose_vms)
    run_command(command, f"Failed to remove validation mapping service container", exit_on_err=False, cwd=os.getcwd())

    print("Removing validation containers")
    command = docker_compose_down_template.format(project_context, docker_compose_validation)
    run_command(command, f"Failed to remove validation containers", exit_on_err=False, cwd=os.getcwd())

    print("Removing volumes")
    command = "docker volume rm validation-structure-definition-server-data"
    run_command(command, f"Failed to remove volumes", exit_on_err=False, cwd=os.getcwd())


if __name__ == "__main__":
    setup()
    input("Press Enter key to initialize shutdown ...")
    teardown()
