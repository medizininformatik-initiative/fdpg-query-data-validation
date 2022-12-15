
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
        url_string = f"{self._url}/{resource_type}"
        request_string = join_url_with_params(url_string, parameters)
        print(f"Requesting: {request_string} with headers {self._headers}")
        response = make_request(request_string, headers=self._headers, proxies=self._proxies, auth=self._auth,
                                cert=self._cert)
        bundle = json.loads(response.text)
        if not paging:
            return bundle
        else:
            paging_result = PagingResult(starting_url=request_string, params=parameters, max_cnt=max_cnt,
                                         headers=self._headers, authorization=self._auth, proxies=self._proxies,
                                         cert=self._cert)
            if get_all:
                bundles = list()
                for result_page in paging_result:
                    bundles.append(result_page)
                return bundles
            else:
                return paging_result


class PagingResult:

    def __init__(self, starting_url, params=None, max_cnt=sys.maxsize, headers=None, authorization=None, proxies=None,
                 cert=None):
        self.__params = params
        self.__current_page = None
        self.total = get_total(starting_url, params=params, headers=headers, auth=authorization, proxies=proxies,
                               cert=cert)
        self.__next_url = join_url_with_params(starting_url, params)
        self.__max_cnt = max_cnt
        self.__current_cnt = 0
        self.__headers = headers
        self.__auth = authorization
        self.__proxies = proxies
        self.__cert = cert

    def __iter__(self):
        return self

    def __next__(self):
        if self.__next_url is None or self.__current_cnt >= self.__max_cnt:
            raise StopIteration
        try:
            response = make_request(self.__next_url, headers=self.__headers, auth=self.__auth, proxies=self.__proxies,
                                    cert=self.__cert)
            self.__current_page = response.json()
            self.__next_url = get_next_url(self.__current_page)
            self.__current_cnt += len(self.__current_page.get('entry', []))
            return self.__current_page
        except HttpError as error:
            raise StopIteration("Paging failed due to request failing") from error
        except KeyError as error:
            raise StopIteration("Paging failed due to missing element in bundle") from error
        except requests.exceptions.JSONDecodeError as error:
            raise StopIteration("Paging failed due to failing to parse content of response body as JSON object") \
                from error

    def is_empty(self):
        return self.total == 0


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
        raise HttpError(response.status_code, f"Paging failed with status code {response.status_code} and "
                        f"headers {response.headers}:\n{response.text}")
    else:
        return response


def get_total(starting_url, params, headers, proxies, cert, auth, verify=True):
    summary_params = params.copy()
    summary_params['_summary'] = 'count'
    request_string = join_url_with_params(starting_url, summary_params)
    response = make_request(request_string, headers=headers, proxies=proxies, cert=cert, auth=auth, verify=verify)
    bundle = response.json()
    total = bundle.get('total', None)
    if total is None:
        print("WARNING: Total element of summary bundle wasn't present! Assumed entry count will be 0!")
        return 0
    return total


def join_url_with_params(url_string, params):
    if params is None:
        return url_string
    param_string = '&'.join([f"{str(key)}={str(value)}" for key, value in params.items()])
    return f"{url_string}?{param_string}"


class HttpError(ConnectionError):

    def __init__(self, status_code, message):
        assert status_code != 200, "Status code must not be 200!"
        self.status_code = status_code
        super().__init__(message)
