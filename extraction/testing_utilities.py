import subprocess
import os
import time

import pytest
import requests

WARN = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'


def run_command(command, err_message, exit_on_err=False, env=None, cwd=os.getcwd()):
    process = subprocess.run(command, stdout=subprocess.PIPE, env=env, shell=True, cwd=cwd)
    if process.returncode != 0:
        msg = fail(f"{err_message}: Exit code {process.returncode}")
        if exit_on_err:
            pytest.exit(msg)
        else:
            print(msg)


def health_check(health_check_url, interval=1, attempts=60, start=0, body=None, content_type="application/json"):
    print(f"Checking health for service @ {health_check_url}")
    time.sleep(start)
    current_attempt = 1
    while current_attempt <= attempts:
        print(f"\rChecking health: {current_attempt}/{attempts}", end='')
        try:
            if body is None:
                response = requests.get(url=health_check_url)
            else:
                response = requests.post(url=health_check_url, data=body, headers={"Content-Type": content_type})
            if response.status_code < 400:
                print("\nService is healthy")
                return
        except:
            # SocketTimeoutException while service is still not up
            pass
        current_attempt += 1
        time.sleep(interval)
    raise TimeoutError(f"Service wasn't healthy after {interval * attempts} seconds")


def warn(message):
    return color(message, WARN)


def fail(message):
    return color(message, FAIL)


def color(message, color_code):
    return f"{color_code}{message}{ENDC}"
