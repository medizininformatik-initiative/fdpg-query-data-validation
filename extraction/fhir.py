import sys

import requests
from requests import auth
import json

resource_types = ["Condition", "Observation", "Procedure", "Medication", "MedicationAdministration",
                  "MedicationStatement", "Specimen", "Consent"]


class FHIRClient:

    def __init__(self, url, user=None, pw=None, token=None, proxies=None, cert=None):
        self.__url = url
        # Removed ['Prefer': 'handling=strict'] from headers due to issues with FHIR search requests
        self.__headers = {'Content-Type': 'application/json'}
        self.__auth = None
        if token is not None:
            self.__headers['Authorization'] = f"Bearer: {token}"
        else:
            self.__auth = auth.HTTPBasicAuth(user, pw)
        self.__proxies = proxies
        self.__cert = None
        if cert is not None and len(cert) > 0:
            self.__cert = cert

    def get(self, resource_type, parameters=None, paging=True, get_all=False, max_cnt=sys.maxsize):
        current_cnt = 0
        assert resource_type in resource_types, f"The provided resource type '{resource_type}' has to be one of " \
                                                f"{', '.join(resource_types)} "
        request_string = f"{self.__url}/{resource_type}"
        if parameters is not None:
            param_string = "&".join([f"{k}={str(v)}" for k, v in parameters.items()])
            request_string = f"{request_string}?{param_string}"
        print(f"Requesting: {request_string} with headers {self.__headers}")
        bundle = json.loads(requests.get(url=request_string, headers=self.__headers,
                                         proxies=self.__proxies, verify=self.__cert).text)
        if not paging:
            return bundle
        else:
            if get_all:
                bundles = list()
                while current_cnt < max_cnt:
                    bundles.append(bundle)
                    next_url = get_next_url(bundle)
                    if next_url is None:
                        break
                    print(f"Requesting: {next_url}")
                    bundle = json.loads(requests.get(url=next_url, headers=self.__headers, proxies=self.__proxies,
                                                     verify=self.__cert).text)
                    current_cnt += len(bundle.get('entry', []))
                return bundles
            else:
                return PagingResult(bundle, max_cnt=max_cnt, headers=self.__headers, authorization=self.__auth)


class PagingResult:

    def __init__(self, bundle, max_cnt=sys.maxsize, headers=None, authorization=None, cert=None):
        self.__current_page = bundle
        self.__total = bundle.get('total', len(bundle.get('entry', [])))
        self.__next_url = get_next_url(bundle)
        self.__max_cnt = max_cnt
        self.__current_cnt = 0
        self.__headers = headers
        self.__auth = authorization
        self.__cert = cert
        self.__stop = False

    def __iter__(self):
        return self

    def __next__(self):
        # TODO: Implement better version of PagingResult which takes to initial request instead of the first bundle to
        # TODO: avoid convoluted condition checking
        if self.__stop:
            raise StopIteration
        self.__next_url = get_next_url(self.__current_page)
        bundle = self.__current_page
        self.__current_cnt += len(bundle.get('entry', []))
        if self.__next_url is not None and self.__current_cnt < self.__max_cnt:
            print(f"Requesting: {self.__next_url}")
            self.__current_page = json.loads(requests.get(self.__next_url, headers=self.__headers, auth=self.__auth,
                                                          verify=self.__cert).text)
        else:
            self.__stop = True
        return bundle

    def is_empty(self):
        return self.__total == 0

    # Might not be reliable depending on whether the server FHIR server returns a value for the total element
    def get_total(self):
        return self.__total


def get_next_url(bundle):
    next_url = None
    if links := bundle.get('link'):
        for link in links:
            if link['relation'] == 'next':
                next_url = link['url']
                break
    else:
        # print(f"Failed to retrieve bundle link")
        return None
    return next_url
