import re


class IssueMap:

    def __init__(self):
        self.__map = dict()

    def put_issue(self, issue):
        # Assumed to be the FHIR path describing the error location not the row/column position
        fhir_path = issue['location'][0]
        key = hash(get_generic_fhir_path(fhir_path))
        diagnostics = issue['diagnostics']
        if key in self.__map:
            occurrences = self.__map[key]
            if diagnostics in occurrences:
                occurrences[diagnostics] = (occurrences[diagnostics][0] + 1, occurrences[diagnostics][1].append(fhir_path))
            else:
                occurrences[diagnostics] = 1, list(fhir_path)
        else:
            self.__map[fhir_path][diagnostics] = 1, list(fhir_path)

    def get_problems_for_element(self, fhir_path):
        return self.__map.get(get_generic_fhir_path(fhir_path))

    def get_problem_count(self, fhir_path, diagnostics):
        problems = self.get_problems_for_element(fhir_path)
        if problems is not None:
            return problems.get(diagnostics)
        else:
            return 0, list()

    def get_map(self):
        return self.__map


# Addresses issue of differences in 'similar' paths occuring due to specific (to the resource instance) deviations not
# necessarily present in other instances (which nonetheless have similar structures). An example of this are indices of
# codings in a CodeableConcept element. These values are not relevant in the context of this analysis as we only care
# about the elements in which issues occur not their absolutely specific locations.
def get_generic_fhir_path(fhir_path):
    return re.sub(r'\[*\]', '[*]', fhir_path)
