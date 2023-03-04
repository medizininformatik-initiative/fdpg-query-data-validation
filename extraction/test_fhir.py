import json
import os
import subprocess
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
env_file = os.path.join('.env')


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
    url = "http://localhost:8090/fhir"
    client = FHIRClient(url=url)
    params = {'_count': 10}
    bundle = client.get(resource_type='StructureDefinition', parameters=params, paging=False, get_all=False)
    assert isinstance(bundle, dict), f"Return should be a json string parsed to a dictionary" \
                                     f" but is instead {type(bundle)}"
    resource_type = bundle.get('resourceType', None)
    assert resource_type == 'Bundle', f"Returned dictionary should represent resource instance of type Bundle but" \
                                      f" element 'resourceType' is {resource_type}"
    total = len(bundle.get('entries', []))
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


def page_through_paging_result(paging_result):
    total = 0
    for result_page in paging_result:
        entries = result_page.get('entry', None)
        if entries is not None:
            total += len(entries)
        else:
            print(warn("Paging failed due to missing entry element in bundle:\n" +
                       json.dumps(result_page, indent=4)))
            break
    return total


@pytest.fixture(scope="session")
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


def warn(message):
    return color(message, WARN)


def fail(message):
    return color(message, FAIL)


def color(message, color_code):
    return f"{color_code}{message}{ENDC}"


if __name__ == "__main__":
    setup()
    # teardown()
