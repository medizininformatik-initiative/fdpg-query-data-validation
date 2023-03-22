import json
import re

from pylatex import Document, Section, Tabularx, Itemize, Command, Subsection, Package, LongTable, Subsubsection, \
    LongTabularx, Tabular
from pylatex.utils import bold, NoEscape, escape_latex

from latex_report.QueryingMetaData import get_querying_meta_data_by_type

AUTHOR = 'Lorenz Rosenau'
SITE = 'Schwarzwaldklinik'

QUERYING_META_DATA = get_querying_meta_data_by_type("QueryingMetaData")


class DataQualityReport:
    def __init__(self, author: str, site: str, report: dict):
        self.site = site
        self.author = author
        self.doc = Document()
        self.report = report

    def generate_resource_count_overview(self):
        if not self.report.get("distribution"):
            return None
        # Define the table format and columns
        table_format = "lccc"
        header_row = [bold("Resource Type"), bold("Total"), bold("Code System"), bold("Count")]

        # Define the table data
        table_data = []
        for resource_type, resource_data in self.report.get("distribution").items():
            total = resource_data.get("total", 0)
            code_systems = resource_data.get("code=?|", {})
            for code_system, count in code_systems.items():
                table_data.append([resource_type, total, code_system, count])
            if not code_systems:
                table_data.append([resource_type, total, "", ""])

        table = Tabular(table_format)
        # Add the table header
        table.add_hline()
        table.add_row(header_row)
        table.add_hline()

        # Add the table rows
        for row in table_data:
            if row[2] == "":
                row[2] = "--"
            if row[3] == "":
                row[3] = "--"
            if row[0] == "Patient" or row[0] == "Organization":
                table.add_row([row[0], row[1], row[2], row[3]])
            else:
                table.add_row([row[0], row[1], row[2], row[3]])

        # Add the table footer
        table.add_hline()
        return table

    @staticmethod
    def generate_document_history_table():
        history_section = Section('Document History')

        with history_section.create(Tabularx('X X X X X')) as table:
            table.add_hline()
            table.add_row(
                (bold('Version'), bold('Date'), bold('Description of Changes'), bold('Author'), bold('Approved By')))
            table.add_hline()
            table.add_row(('1.0', Command('date', NoEscape(r'\today')), 'Initial version', f"{AUTHOR}", ''))
            table.add_hline()

        return history_section

    @staticmethod
    def hyperlink(url, text):
        text = escape_latex(text)
        url = escape_latex(url)
        return NoEscape(r'\href{' + url + '}{' + text + '}')

    @staticmethod
    def generate_intro_section():
        intro_section = Section('Introduction')
        khan_ref = Command("cite", NoEscape(r"kahn_harmonized_2016"))
        intro_section.append(
            f'This data quality report analyzes the compatibility of FHIR data with the "Forschungs Daten Portal '
            f'Gesundheit" (FDPG) and is based on the MII Core Data Set (KDS) with further restrictions. '
            f'The focus of this analysis is on completeness and correctness, as defined by Khan et al.')
        intro_section.append(khan_ref)
        return intro_section

    @staticmethod
    def generate_validation_section():
        validation_section = Section('ValidationValidation Process')

        validation_section.append('To ensure the quality of the FHIR data, a validation process was used. '
                                  'The process involved the following steps:')

        with validation_section.create(Itemize()) as itemize:
            itemize.add_item('Development of FHIR profiles based on the core data set.')
            itemize.add_item('Application of the same restrictions as in the search ontology to validate the instance '
                             'data at the clinical sites.')
            itemize.add_item('Identification of discrepancies between the available concepts in the search ontology '
                             'and the instance data at the clinical sites.')
            itemize.add_item('Identification of discrepancies among the instance data at different clinical sites.')
            itemize.add_item('Validation of data completeness and correctness towards the core data set.')

        validation_section.append('This validation process allowed us to gain valuable insight into the quality of the '
                                  'FHIR data and identify areas for improvement. The process also helped ensure that '
                                  'the FHIR data adhered to the established standards and restrictions defined by the '
                                  'search ontology and core data set.')

        return validation_section

    @staticmethod
    def generate_disclaimer_section():
        disclaimer_text = NoEscape("This report has been automatically generated and is intended to provide a "
                                   "snapshot of the data quality at the time of generation. "
                                   r"It is a work in progress and may contain errors or inaccuracies. \newline "
                                   "While we have made every effort to ensure that no re-identifying data is present in the "
                                   "report, we cannot guarantee that this is the case. Therefore, we accept no liability or "
                                   r"responsibility for any damages or \newline "
                                   r"consequences arising from the use of this report. \newline "
                                   "Before sharing this report with individuals outside of your institution, we strongly "
                                   "recommend that you conduct a diligent review of its contents to ensure that it is suitable "
                                   r"for your purposes. \newline \newline "
                                   "Thank you for your understanding and cooperation in this matter.")

        disclaimer_section = Section('Disclaimer')
        disclaimer_section.append(disclaimer_text)
        return disclaimer_section

    def generate_metrics_section(self):
        metrics_section = Section('Resource Overview')
        metrics_section.append('This section provides an overview of the resources available at the clinical site.')
        metrics_section.append(Command('newline'))
        metrics_section.append(Command('newline'))
        resource_overview_table = self.generate_resource_count_overview()
        if resource_overview_table:
            metrics_section.append(resource_overview_table)
        else:
            metrics_section.append('No resources available')
        return metrics_section

    def generate_issues_section(self):
        issues_section = Section('Data Quality Issues')
        issues_section.append('This is the data quality issues section.')
        data_types = ['Consent', 'Condition', 'Medication', 'MedicationAdministration', 'MedicationStatement',
                      'Procedure', 'Specimen']
        for data_type in data_types:
            sub_section = self.generate_issue_sub_section(data_type)
            if sub_section:
                issues_section.append(sub_section)
        issues_section.append(self.generate_observation_sub_section())
        return issues_section

    def generate_observation_sub_section(self):
        observation_section = Subsection('Observation')
        observation_section.append('This is the data quality issues section for Observation.')
        validation_result = self.get_validation_result_by_data_type('Observation')
        observation_section.append('The number of validated resources is ' + str(validation_result.get("count")) + '.')
        observation_section.append(Command('newline'))
        observation_section.append(Command('newline'))
        observation_section.append(self.generate_observation_unit_sub_sub_section())

        return observation_section

    def generate_observation_unit_sub_sub_section(self):
        sub_sub_section = Subsubsection('Observation Units')
        sub_sub_section.append('A predictable issue is the use of different units for the same observation. The '
                               'search ontology uses the Miracum MDR LOINC Top300 codes ')
        sub_sub_section.append(
            self.hyperlink(
                """https://mdr.miracum.org/detail.xhtml?urn=urn%3Amiracum1%3Adataelementgroup%3A10%3A6""",
                '[MDR]'))
        sub_sub_section.append('. ')
        sub_sub_section.append('However it is to be expected that non Miracum sites use different units.'
                               'The following table shows the differences between the units used in the FHIR data and '
                               'the units used in the search ontology.')
        sub_sub_section.append(Command('newline'))
        sub_sub_section.append(Command('newline'))
        sub_sub_section.append(self.generate_observation_unit_table())
        return sub_sub_section

    def generate_observation_unit_table(self):
        table = LongTabularx('|X|X|X|')
        table.add_hline()
        table.add_row((bold('Loinc Code'), bold('Expected Unit'), bold('Actual Unit')))
        table.add_hline()
        validation_result = self.get_validation_result_by_data_type('Observation')
        for loinc_code, result in validation_result.items():
            issues = result.get("issues", [])
            unit_issues = self.filter_issues_by_location(issues, "value.ofType(Quantity).code")
            for unit_issue in unit_issues:
                # extract actual and expected unit from "Value is 'actual' but must be 'expected'" string
                expected = unit_issue.get("diagnostics").split("'")[3]
                actual = unit_issue.get("diagnostics").split("'")[1]
                table.add_row((loinc_code, expected, actual))
                table.add_hline()
        return table

    @staticmethod
    def filter_issues_by_location(issues, location):
        """
        Filters the issues by location.
        :param issues: The issues to filter.
        :param location: The location to filter for.
        :return: The filtered issues.
        """
        return [issue for issue in issues if location in issue.get("location")[0]]

    def generate_issue_sub_section(self, data_type):
        sub_section = Subsection(data_type)
        sub_section.append('This is the data quality issues section for ' + data_type + r'.')
        validation_result = self.get_validation_result_by_data_type(data_type)
        if not validation_result:
            return None
        validated_resources = validation_result.get("count")
        sub_section.append('The number of validated resources is ' + str(validated_resources) + '.')
        sub_section.append(Command('newline'))
        sub_section.append(Command('newline'))
        issues = validation_result.get("issues")
        self.set_issue_location_resource_type(issues, data_type)
        fdpg_issues = self.filter_issues_by_fdpg_query_paths(issues, data_type)
        if fdpg_issues:
            sub_section.append(self.generate_fdpg_issue_section(data_type, fdpg_issues))
        sub_section.append(Command('newline'))
        [issues.remove(issue) for issue in fdpg_issues]
        general_issues = issues
        if general_issues:
            sub_section.append(self.generate_general_issue_section(data_type, general_issues))
        return sub_section

    def generate_fdpg_issue_section(self, data_type, fdpg_issues):
        fdpg_issues_section = Subsubsection(f'{data_type} FDPG Issues')
        fdpg_issues_section.append('This section provides an overview of the issues direclty related to the search '
                                   'ontology.')
        fdpg_issues_section.append(Command('newline'))
        fdpg_issues_section.append(Command('newline'))
        if issue_table := self.generate_issue_table(fdpg_issues):
            fdpg_issues_section.append(issue_table)
        return fdpg_issues_section

    def generate_general_issue_section(self, data_type, issues):
        general_issues_section = Subsubsection(f'{data_type} General Issues')
        general_issues_section.append(
            'The following issues are not directly related to the search ontology. And should not '
            'effect the search results. You want to investigate these issues regardless. As they '
            'indicate incompatibility with the FHIR standard or core data set.')
        general_issues_section.append(Command('newline'))
        general_issues_section.append(Command('newline'))
        if issue_table := self.generate_issue_table(issues):
            general_issues_section.append(issue_table)
        return general_issues_section

    def get_validation_result_by_data_type(self, data_type):
        return self.report.get("validation").get(data_type, {})

    @staticmethod
    def set_issue_location_resource_type(issues, resource_type):
        """
        The location of the issue has a path based on the bundle structure.
        I.e. Bundle.entry[0].resource.ofType(Condition).code
        This method replaces the resource type with the actual resource type -> Condition.code
        using a regex.
        """
        for issue in issues:
            issue["location"][0] = re.sub(r"Bundle.entry\[\d+].resource.ofType\(" + resource_type + r"\)",
                                          resource_type,
                                          issue["location"][0])

    @staticmethod
    def get_issues_by_severity(issues, severity: str):
        return [issue for issue in issues if issue.get("severity") == severity]

    @staticmethod
    def generate_summary_section():
        summary_section = Section('Data Quality Summary')
        summary_section.append('This is the data quality summary section.')
        return summary_section

    @staticmethod
    def generate_conclusion_section():
        conclusion_section = Section('Conclusion')
        conclusion_section.append('This is the conclusion section.')
        return conclusion_section

    def add_title(self):
        self.doc.preamble.append(Command('title', 'Data Quality Report'))
        self.doc.preamble.append(Command('author', f'{self.site}'))
        self.doc.preamble.append(Command('date', NoEscape(r'\today')))
        self.doc.append(NoEscape(r'\maketitle'))

    @staticmethod
    def filter_issues_by_fdpg_query_paths(issues, resource_type):
        """
        Filters the issues by the FDPG query paths.
        :param issues: The issues to filter.
        :param resource_type: The resource type to get the querying metadata for.
        :return: The filtered issues.
        """
        querying_meta_data = QUERYING_META_DATA.get(resource_type)
        if not querying_meta_data:
            return []
        result = []
        for issue in issues:
            location = issue.get("location")[0]
            # remove index from location
            location = re.sub(r"\[\d+]", "", location)
            for relevant_path in querying_meta_data.fhir_paths:
                if not relevant_path:
                    continue
                # Remove [x] from relevant path
                relevant_path = re.sub(r"\[x]", "", relevant_path)
                # Remove slice name from relevant path (e.g. Observation.code.coding:loinc.system ->
                # Observation.code.coding.system)
                relevant_path = re.sub(r":\w+", "", relevant_path)
                # Remove parentheses from relevant path
                relevant_path = relevant_path.replace("(", "").replace(")", "")
                if location in relevant_path or relevant_path in location:
                    result.append(issue)
                    break
        return result

    def generate_report(self):
        self.doc = Document('data_quality_report')

        self.doc.preamble.append(Package('biblatex', options=['sorting=none']))
        self.doc.preamble.append(Package('hyperref'))
        self.doc.preamble.append(Command('addbibresource', "references.bib"))

        self.add_title()
        self.doc.append(NoEscape(r'\newpage'))

        self.doc.append(NoEscape(r'\tableofcontents'))

        self.doc.append(NoEscape(r'\newpage'))

        disclaimer_section = self.generate_disclaimer_section()
        self.doc.append(disclaimer_section)

        self.doc.append(NoEscape(r'\newpage'))

        history_section = self.generate_document_history_table()
        self.doc.append(history_section)

        self.doc.append(NoEscape(r'\newpage'))

        intro_section = self.generate_intro_section()
        self.doc.append(intro_section)

        validation_section = self.generate_validation_section()
        self.doc.append(validation_section)

        self.doc.append(NoEscape(r'\newpage'))

        metrics_section = self.generate_metrics_section()
        self.doc.append(metrics_section)

        self.doc.append(NoEscape(r'\newpage'))

        issues_section = self.generate_issues_section()
        self.doc.append(issues_section)

        # summary_section = self.generate_summary_section()
        # self.doc.append(summary_section)
        #
        # conclusion_section = self.generate_conclusion_section()
        # self.doc.append(conclusion_section)

        bib_cmd = Command('printbibliography')
        self.doc.append(bib_cmd)

        self.doc.generate_pdf(clean_tex=True)

    def generate_issue_table(self, issues):
        table = LongTable('p{0.05\\textwidth}p{0.3\\textwidth}p{0.65\\textwidth}')
        table.add_hline()
        table.add_row((bold("N"), bold("Location"), bold("Description")))
        table.add_hline()
        if not issues:
            return None
        for issue in self.sorted_by_severity(issues):
            # set the color of the row based on the severity of the issue
            # force line break in issue diagnostic if it is too long
            location = issue.get("location")[0]
            # add new line after each dot
            location = location.replace(".", r"\newline .")
            table.add_row(issue.get("count"), location, escape_latex(issue.get("diagnostics")),
                          escape=False,
                          color=self.get_severity_color(issue.get("severity")))
            table.add_hline()
        table.add_hline()
        return table

    def sorted_by_severity(self, issues):
        """
        Sorts the issues by severity. The order is: fatal, error, warning, information.
        :param issues: The issues to sort.
        :return: The sorted issues.
        """
        if not issues:
            return []
        return sorted(issues, key=lambda issue: self.get_severity_order(issue.get("severity")))

    @staticmethod
    def get_severity_order(param):
        if param == "fatal":
            return 0
        elif param == "error":
            return 1
        elif param == "warning":
            return 2
        else:
            return 3

    @staticmethod
    def get_severity_color(severity):
        if severity == "fatal":
            return "red"
        elif severity == "error":
            return "orange"
        elif severity == "warning":
            return "yellow"
        elif severity == "information":
            return "white"


if __name__ == '__main__':
    with open('../report/raw_report_test.json') as f:
        report_data = json.load(f)
        quality_report = DataQualityReport(AUTHOR, SITE, report_data)
        quality_report.generate_report()
