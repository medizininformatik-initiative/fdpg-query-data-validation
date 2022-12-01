import os
import subprocess

import pytest

from fhir import FHIRClient


FAIL = '\033[91m'
ENDC = '\033[0m'

docker_compose_validation = os.path.join('.', 'validation_service', 'docker-compose-validation.yml')
docker_compose_vms = os.path.join('.', 'validation_mapper_service', 'docker-compose-vms.yml')
project_context = 'feasibility-deploy'
env_file = '.env'


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
    pass


@pytest.fixture(scope="session", autouse=True)
def prepare_setup(request):
    setup()
    request.addfinalizer(teardown)


def setup():
    print("Starting setup")
    print("Starting containers")
    # Change CWD to base project directory
    os.chdir(os.path.join('.', '..'))
    print(os.getcwd())
    docker_compose_template = "dockercompose -p {} -f {} --env-file {} up -d"

    print("Starting validation containers")
    command = docker_compose_template.format(project_context, docker_compose_validation, env_file).split()
    print(command)
    process = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
    if process.returncode != 0:
        print(fail(f"Failed to start validation containers: Exit code {process.returncode}"))
        print(fail(process.stderr))
        exit(-1)
    print(process.stdout)

    print("Starting validation mapping service container")
    command = docker_compose_template.format(project_context, docker_compose_vms, env_file).split()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, cwd=os.getcwd())
    output, error = process.communicate()
    if process.returncode != 0:
        print(fail(f"Failed to start validation mapping service container: Exit code {process.returncode}"))
        print(fail(error))
        exit(-1)
    print(output)


def teardown():
    print("Starting teardown")
    print("Removing containers and volumes")
    docker_compose_down_template = "docker compose -p {} -f {} down --volumes"

    print("Removing validation mapping service container and volumes")
    command = docker_compose_down_template.format(project_context, docker_compose_vms).split()
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    output, error = process.communicate()
    if process.returncode != 0:
        print(fail(f"Failed to remove validation mapping service container and volumes: Exit code {process.returncode}"))
        print(fail(error))
    print(output)

    print("Removing validation containers and volumes")
    command = docker_compose_down_template.format(project_context, docker_compose_validation).split()
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    output, error = process.communicate()
    if process.returncode != 0:
        print(fail(f"Failed to remove validation containers and volumes: Exit code {process.returncode}"))
        print(fail(error))
    print(output)


def fail(message):
    return f"{FAIL}{message}{ENDC}"
