import glob
import json
import os
import subprocess
import time
import traceback

import dotenv
import pytest
import requests

from fhir import FHIRClient
from fhir import PagingResult

WARN = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

docker_compose_validation = os.path.join('.', 'validation_service', 'docker-compose-validation.yml')
docker_compose_vms = os.path.join('.', 'validation_mapper_service', 'docker-compose-vms.yml')
project_context = 'feasibility-deploy'
env_file = '.env'
fhir_server_volume_name = 'test-blaze-data'
fhir_server_name = 'test-fhir-server'
fhir_server_ports = [9000, 8080]  # host port, container port
blaze_image = 'samply/blaze:0.18'
data_dir = 'fhir_profiles'


def test_fhirclient():
    # Test Basic Auth
    print("Testing BasicAuth init")
    url = "https://www.example.org"
    user = "user"
    password = "password"
    client = FHIRClient(url=url, user=user, pw=password)
    assert client._auth is not None, "HTTPBasicAuth object is None but should not be"
    assert client._auth.username == user, f"username attribute of HTTPBasicAuth object is {client._auth.username}" \
                                          f" but should be {user}"
    assert client._auth.password == password, f"password attribute of HTTPBasicAuth object is {client._auth.password}" \
                                              f" but should be {password}"
    assert 'Authorization' not in client._headers.keys(), f"Header with key 'Authorization' should not be in clients" \
                                                          f" headers attribute if Basic Auth is used:" \
                                                          f" associated value: {client._headers['Authorization']}"

    # Test TokenAuth
    print("Testing TokenAuth init")
    token = "adsfmaf32fjfjfp2aqfpek67vfda02"
    client = FHIRClient(url=url, user=user, pw=password, token=token)
    assert client._auth is None, f"HTTPBasicAuth object is not None but should be: {str(client._auth)}"
    assert 'Authorization' in client._headers.keys(), f"headers attribute of client should contain key 'Authorization'"
    assert client._headers['Authorization'] == f"Bearer: {token}", f"Key 'Authorization' in clients headers attribute" \
                                                                   f" should be paired with value 'Bearer: {token}'"


def test_get():
    print("Testing get method with paging=False, get_all=False")
    url = f"http://localhost:{fhir_server_ports[0]}/fhir"
    client = FHIRClient(url=url)
    params = {'_count': 10}
    bundle = client.get(resource_type='StructureDefinition', parameters=params, paging=False, get_all=False)
    assert isinstance(bundle, dict), f"Return should be a json string parsed to a dictionary" \
                                     f" but is instead {type(bundle)}"
    resource_type = bundle.get('resourceType', None)
    assert resource_type == 'Bundle', f"Returned dictionary should represent resource instance of type Bundle but" \
                                      f" element 'resourceType' is {resource_type}"
    total = len(bundle.get('entry', []))
    assert total == 10, f"Returned bundle should contain 10 entries but contains {total}"

    print("Testing get method with paging=True, get_all=False")
    client = FHIRClient(url=url)
    paging_result = client.get(resource_type='StructureDefinition', parameters=params, paging=True, get_all=False)
    assert isinstance(paging_result, PagingResult), f"Return is not of type PagingResult" \
                                                    f" but is instead {type(paging_result)}"
    response = requests.get(url=f'{url}/StructureDefinition?_summary=count')
    expected_total = response.json().get('total', None)
    if expected_total is not None:
        total = page_through_paging_result(paging_result)
        assert total == expected_total, f"Paging returned unexpected number of resource instances:" \
                                        f" {total} (actual) vs {expected_total} (expected)"
    else:
        print(warn("Paging skipped due to missing total element in summary bundle:\n" + response.text))

    print("Testing get method with paging=True, get_all=False, max_cnt=30")
    client = FHIRClient(url=url)
    max_cnt = 30
    paging_result = client.get(resource_type='StructureDefinition', parameters=params, paging=True, get_all=False,
                               max_cnt=max_cnt)
    assert isinstance(paging_result, PagingResult), f"Return is not of type PagingResult" \
                                                    f" but is instead {type(paging_result)}"
    if expected_total < max_cnt:
        print(warn(f"Paging skipped due to smaller resource instance count present than max_cnt:" +
                   f" {expected_total} (present) vs {max_cnt} (max_cnt)"))
    else:
        total = page_through_paging_result(paging_result)
        assert total == max_cnt, f"Paging returned unexpected number of resource instances:" \
                                 f" {total} (returned) vs {max_cnt} (max_cnt)"

    print("Testing get method with paging=True, get_all=True")
    client = FHIRClient(url=url)
    result_bundles = client.get(resource_type='StructureDefinition', parameters=params, paging=True, get_all=True)
    assert isinstance(result_bundles, list), f"Return is not a list but is instead {type(result_bundles)}"
    try:
        total = page_through_paging_result(result_bundles)
        assert total == expected_total, f"Wrong number of entries were returned:" \
                                        f" {total} returned vs {expected_total} expected"
    except AssertionError as e:
        # Pass on AssertionError instance
        raise e
    except Exception as e:
        print(warn("Could not process list of returned bundles. Partially kipping test"))
        print(warn(traceback.format_exception(e)))

    print("Testing get method with paging=True, get_all=True, max_cnt=30")
    client = FHIRClient(url=url)
    result_bundles = client.get(resource_type='StructureDefinition', parameters=params, paging=True, get_all=True,
                                max_cnt=30)
    assert isinstance(result_bundles, list), f"Return is not a list but is instead {type(result_bundles)}"
    total = page_through_paging_result(result_bundles)
    assert total == 30, f"Wrong number of entries were returned: {total} returned vs {expected_total} expected"


'''
Works for paging through list of bundles as well as PagingResult instance as both enable iteration through their content
as well as return a dictionary representation of a bundle in each iteration
'''
def page_through_paging_result(paging_result):
    total = 0
    for result_page in paging_result:
        assert isinstance(result_page, dict), f"Element in return has to be a dictionary" \
                                              f" but is instead {type(result_page)}"
        entries = result_page.get('entry', None)
        if entries is not None:
            total += len(entries)
        else:
            print(warn("Paging failed due to missing entry element in bundle:\n" +
                       json.dumps(result_page, indent=4)))
            break
    return total


@pytest.fixture(scope="session", autouse=True)
def prepare_fhir_server(request):
    setup_fhir_server()
    request.addfinalizer(teardown_fhir_server)


def setup_fhir_server():
    print("Starting setup of FHIR server")
    os.chdir(os.path.join('.', '..'))
    print(f"Loading environment variables from {env_file}")
    env_dict = dotenv.dotenv_values(env_file)
    print("Setting up FHIR server")
    print("Creating volume")
    volume_create_command = f"docker volume create {fhir_server_volume_name}"
    run_command(volume_create_command, "Failed to create volume", exit_on_err=True, env=env_dict, cwd=os.getcwd())
    print("Starting container")
    base_url = f'http://localhost:{fhir_server_ports[0]}'
    docker_run_command = f"docker run --name {fhir_server_name}" \
                         f" -p {fhir_server_ports[0]}:{fhir_server_ports[1]}" \
                         f" -v {fhir_server_volume_name}:/app/data" \
                         f" -e BASE_URL={base_url} -d {blaze_image}"
    run_command(docker_run_command, "Failed to start FHIR server", exit_on_err=True, env=env_dict, cwd=os.getcwd())
    try:
        wait_until_healthy(blaze_base_url=base_url, interval=1, attempts=60)
    except TimeoutError as e:
        print("Health check failed. Stopping tests")
        print(traceback.format_exception(e))
        exit(-1)
    print("Uploading data for testing")
    fhir_server_url = f"{base_url}/fhir"
    try:
        upload_structure_definitions(fhir_server_url=fhir_server_url, file_dir=data_dir)
    except Exception as e:
        print("Upload failed. Stopping tests")
        print(traceback.format_exception(e))
        exit(-1)
    print("Starting setup done")


def teardown_fhir_server():
    print("Shutting down FHIR server")
    docker_container_rm_command = f"docker container rm {fhir_server_name} --force"
    run_command(docker_container_rm_command, "Failed to shut down FHIR server", cwd=os.getcwd())
    print("Removing volume")
    docker_volume_rm_command = f"docker volume rm {fhir_server_volume_name}"
    run_command(docker_volume_rm_command, "Failed to remove volume", cwd=os.getcwd())


def upload_structure_definitions(fhir_server_url, file_dir):
    for path in glob.glob(pathname=os.path.join(file_dir, '**', '*.json'), recursive=True):
        print(f"Uploading file @ {path} to server @ {fhir_server_url}")
        file_content = open(path).read()
        response = requests.post(url=f"{fhir_server_url}/StructureDefinition", data=file_content,
                                 headers={'Content-Type': 'application/json'})
        if response.status_code != 200 and response.status_code != 201:
            raise Exception(f"Upload failed with status code {response.status_code}:\n{response.text}")


def run_command(command, err_message, exit_on_err=False, env=None, cwd=os.getcwd()):
    process = subprocess.run(command, stdout=subprocess.PIPE, env=env, shell=True, cwd=cwd)
    if process.returncode != 0:
        print(fail(f"{err_message}: Exit code {process.returncode}"))
        if exit_on_err:
            exit(-1)


def wait_until_healthy(blaze_base_url, interval=1, attempts=60):
    print(f"Checking health for FHIR server @{blaze_base_url}/health")
    current_attempt = 1
    while current_attempt <= attempts:
        print(f"Checking health of FHIR server: {current_attempt}/{attempts}")
        try:
            response = requests.get(url=f"{blaze_base_url}/health")
            if response.status_code == 200:
                print("FHIR server is healthy")
                return
        except:
            # SocketTimeoutException while service is still not up
            pass
        current_attempt += 1
        time.sleep(interval)
    raise TimeoutError(f"FHIR service wasn't healthy after {interval * attempts} seconds")


def warn(message):
    return color(message, WARN)


def fail(message):
    return color(message, FAIL)


def color(message, color_code):
    return f"{color_code}{message}{ENDC}"


if __name__ == "__main__":
    setup_fhir_server()
    teardown_fhir_server()

'''
def prepare_setup(request):
    setup()
    request.addfinalizer(teardown)


def setup():
    print("Starting setup")
    os.chdir(os.path.join('.', '..'))
    print(f"Loading environment variables from {env_file}")
    env_dict = dotenv.dotenv_values(env_file)
    print("Starting containers")
    docker_compose_template = "docker compose -p {} -f {} --env-file {} up -d"

    print("Starting validation containers")
    command = docker_compose_template.format(project_context, os.path.join(os.getcwd(), docker_compose_validation),
                                             os.path.join(os.getcwd(), env_file))
    process = subprocess.run(command, stdout=subprocess.PIPE, env=env_dict, shell=True, cwd=os.getcwd())
    if process.returncode != 0:
        print(fail(f"Failed to start validation containers: Exit code {process.returncode}"))
        exit(-1)

    print("Starting validation mapping service container")
    command = docker_compose_template.format(project_context, os.path.join(os.getcwd(), docker_compose_vms),
                                             os.path.join(os.getcwd(), env_file))
    process = subprocess.run(command, stdout=subprocess.PIPE, env=env_dict, shell=True, cwd=os.getcwd())
    if process.returncode != 0:
        print(fail(f"Failed to start validation mapping service container: Exit code {process.returncode}"))
        exit(-1)


def teardown():
    print("Starting teardown")
    print("Removing containers and volumes")
    docker_compose_down_template = "docker compose -p {} -f {} down"

    print("Removing validation mapping service container")
    command = docker_compose_down_template.format(project_context, docker_compose_vms)
    process = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
    if process.returncode != 0:
        print(fail(f"Failed to remove validation mapping service container: Exit code {process.returncode}"))

    print("Removing validation containers")
    command = docker_compose_down_template.format(project_context, docker_compose_validation)
    process = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
    if process.returncode != 0:
        print(fail(f"Failed to remove validation containers: Exit code {process.returncode}"))

    print("Removing volumes")
    command = "docker volume rm validation-structure-definition-server-data"
    process = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
    if process.returncode != 0:
        print(f"Failed to remove volumes: Exit code {process.returncode}")
'''
