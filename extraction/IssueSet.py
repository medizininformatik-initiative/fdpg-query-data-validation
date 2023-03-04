import re


class IssueSet:

    def __init__(self):
        self.__map = dict()

    def add(self, issue):
        if issue is None:
            return
        if not isinstance(issue, dict):
            raise TypeError("issue argument has to be of type dict")
        severity = issue.get('severity', '')
        code = issue.get('code', '')
        diagnostics = issue.get('diagnostics', '')
        fhirpath = ''
        location = issue.get('location')
        if location is not None:
            fhirpath = get_generic_fhir_path(location[0])
        hash_code = hash(severity + code + diagnostics + fhirpath)
        if hash_code not in self.__map:
            issue['count'] = 1
            self.__map[hash_code] = issue
        else:
            self.__map[hash_code]['count'] += 1

    def get_issues(self):
        return self.__map.values()

    def clear(self):
        self.__map.clear()


# Addresses issue of differences in 'similar' paths occurring due to specific (to the resource instance) deviations not
# necessarily present in other instances (which nonetheless have similar structures). An example of this are indices of
# codings in a CodeableConcept element. These values are not relevant in the context of this analysis as we only care
# about the elements in which issues occur not their absolutely specific locations.
def get_generic_fhir_path(fhir_path):
    return re.sub(r'\[.*]', '[*]', fhir_path)