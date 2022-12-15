

import sys
import requests
from requests import auth
import json

resource_types = ["Condition", "Observation", "Procedure", "Medication", "MedicationAdministration",
                  "MedicationStatement", "Specimen", "Consent", "StructureDefinition"]


class FHIRClient:

    def __init__(self, url, user=None, pw=None, token=None, proxies=None, cert=None):
        self._url = url
        self._headers = {'Content-Type': 'application/json'}
        self._auth = None
        if token is not None and len(token) > 0:
            self._headers['Authorization'] = f"Bearer: {token}"
        else:
            self._auth = auth.HTTPBasicAuth(user, pw)
        self._proxies = proxies
        self._cert = None
        if cert is not None and len(cert) > 0:
            self._cert = cert

    def get(self, resource_type, parameters=None, paging=True, get_all=False, max_cnt=sys.maxsize):
        assert resource_type in resource_types, f"The provided resource type '{resource_type}' has to be one of " \
                                                f"{', '.join(resource_types)} "
        request_string = f"{self._url}/{resource_type}"
        if parameters is not None:
            param_string = "&".join([f"{k}={str(v)}" for k, v in parameters.items()])
            request_string = f"{request_string}?{param_string}"
        print(f"Requesting: {request_string} with headers {self._headers}")
        response = make_request(request_string, headers=self._headers, proxies=self._proxies, auth=self._auth,
                                cert=self._cert)
        bundle = json.loads(response.text)
        if not paging:
            return bundle
        else:
            paging_result = PagingResult(bundle, max_cnt=max_cnt, headers=self._headers, authorization=self._auth,
                                         proxies=self._proxies, cert=self._cert)
            if get_all:
                bundles = list()
                for result_page in paging_result:
                    bundles.append(result_page)
                return bundles
            else:
                return paging_result


class PagingResult:

    def __init__(self, starting_url, max_cnt=sys.maxsize, headers=None, authorization=None, proxies=None, cert=None):
        self.__current_page = None
        self.__total = None  # bundle.get('total', len(bundle.get('entry', [])))
        self.__next_url = starting_url  # get_next_url(bundle)
        self.__max_cnt = max_cnt
        self.__current_cnt = 0
        self.__headers = headers
        self.__auth = authorization
        self.__proxies = proxies
        self.__cert = cert
        self.__stop = False

    def __iter__(self):
        return self

    def __next__(self):
        # TODO: Implement better version of PagingResult which takes to initial request instead of the first bundle to
        # TODO: avoid convoluted condition checking
        try:
            self.__current_page = make_request(self.__next_url, headers=self.__headers, auth=self.__auth,
                                               proxies=self.__proxies, cert=self.__cert)
            self.__next_url = get_next_url(self.__current_page)
            self.__current_cnt += len(self.__current_page.get('entry', []))
            if self.__next_url is not None and self.__current_cnt < self.__max_cnt:
        except HttpError as error:
            raise StopIteration(f"Paging failed due to request failing") from error
        except KeyError as error:
            raise StopIteration(f"Paging failed due to missing element in bundle") from error

        if self.__stop:
            raise StopIteration
        self.__next_url = get_next_url(self.__current_page)
        bundle = self.__current_page
        self.__current_cnt += len(bundle.get('entry', []))
        if self.__next_url is not None and self.__current_cnt < self.__max_cnt:
            print(f"Requesting: {self.__next_url}")
            response = requests.get(self.__next_url, headers=self.__headers, auth=self.__auth, verify=self.__cert,
                                    proxies=self.__proxies)
            if response.status_code != 200:
                raise StopIteration(f"Paging failed with status code {response.status_code} and "
                                    f"headers {response.headers}:\n{response.text}")
            self.__current_page = json.loads(response.text)
        else:
            self.__stop = True
        return bundle

    def is_empty(self):
        if self.__total is None:
            # Ensure some statement can be made about the whether the bundle is empty
            self.__next__()
        return self.__total == 0


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


def make_request(url_string, headers, proxies, cert, auth, verify=True):
    print(f"Requesting: {url_string}")
    response = requests.get(url=url_string, headers=headers, proxies=proxies,
                            cert=cert, auth=auth, verify=verify)
    if response.status_code != 200:
        raise HttpError(response.status_code, f"Request failed with status code {response.status_code} and "
                        f"headers {response.headers}:\n{response.text}")
    else:
        return response


class HttpError(ConnectionError):

    def __init__(self, status_code, message):
        assert status_code != 200, "Status code must not be 200!"
        self.status_code = status_code
        super().__init__(message)
