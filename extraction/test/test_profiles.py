import json
import unittest

from extraction.main import simple_test


def test_positive_condition():
    with open("resources/condition_bundle_no_error.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            assert "No issues detected during validation" == (issue.get("diagnostics", ""))
            return
        assert False


def test_wrong_code_condition():
    with open("resources/condition_bundle_code_error.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            if issue.get("severity", "") == "error" and issue.get("location", [])[0] == \
                    "Bundle.entry[0].resource.ofType(Condition).code.coding[0]":
                return
        assert False


def test_no_icd10_condition():
    with open("resources/condition_bundle_no_icd10_coding.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            if issue.get("severity", "") == "error" and issue.get("location", "")[0] == \
                    "Bundle.entry[0].resource.ofType(Condition).code":
                assert issue.get("diagnostics", "") == "Condition.code.coding:icd10-gm: minimum required = 1, but " \
                                                       "only found 0 (from https://www.medizininformatik-initiative.de" \
                                                       "/fhir/fdpg/StructureDefinition/Diagnose)"
                return
        assert False


def test_no_reference_conditon():
    with open("resources/condition_bundle_no_reference.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            if issue.get("severity", "") == "error" and issue.get("location", "")[0] == \
                    "Bundle.entry[0].resource.ofType(Condition)":
                assert "Condition.subject: minimum required = 1, but only found 0 " in issue.get("diagnostics", "")
                return
        assert False


@unittest.skip("Not implemented yet")
def test_positive_consent():
    with open("resources/consent_bundle_no_error.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            assert "No issues detected during validation" == (issue.get("diagnostics", ""))
            return
        assert False


def test_positive_medication():
    with open("resources/medication_bundle_no_error.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            assert "No issues detected during validation" == (issue.get("diagnostics", ""))
            return
        assert False


@unittest.skip("Not implemented yet")
def test_wrong_code_medication():
    with open("resources/medication_bundle_wrong_code.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            if issue.get("severity", "") == "error" and issue.get("location", "")[0] == \
                    "Bundle.entry[0].resource.ofType(Medication).code":
                pass


def test_positive_medication_administration():
    with open("resources/medication_administration_bundle_no_error.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            assert "No issues detected during validation" == (issue.get("diagnostics", ""))
            return
        assert False


def test_no_reference_medication_administration():
    with open("resources/medication_administration_bundle_no_reference.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            if issue.get("severity", "") == "error" and issue.get("location", "")[0] == \
                    "Bundle.entry[0].resource.ofType(MedicationAdministration)":
                if "MedicationAdministration.medication[x]:medicationReference: minimum required = 1, but only " \
                   "found 0" in (issue.get("diagnostics", "")):
                    return
        assert False


def test_positive_specimen():
    with open("resources/specimen_bundle_no_error.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            assert "No issues detected during validation" == (issue.get("diagnostics", ""))
            return
        assert False


def test_wrong_code_specimen():
    with open("resources/specimen_bundle_wrong_code.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            if issue.get("severity", "") == "error" and issue.get("location", "")[0] == \
                    "Bundle.entry[0].resource.ofType(Specimen).type.coding[0]":
                return
        assert False


@unittest.skip("Not working due to a bug in the validator")
def test_wrong_body_site_code_specimen():
    with open("resources/specimen_bundle_wrong_body_site_code.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            if issue.get("severity", "") == "error" and issue.get("location", "")[0] == \
                    "Bundle.entry[0].resource.ofType(Specimen).bodySite.ofType(CodeableConcept).coding[0].code":
                return
        assert False


@unittest.skip("Not working due to a bug in the validator")
def test_positive_procedure():
    with open("resources/procedure_bundle_no_error.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            assert "No issues detected during validation" == (issue.get("diagnostics", ""))
            return
        assert False


@unittest.skip("Not working due to a bug in the validator")
def test_wrong_code_procedure():
    with open("resources/procedure_bundle_wrong_code.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            if issue.get("severity", "") == "error" and issue.get("location", "")[0] == \
                    "Bundle.entry[0].resource.ofType(Procedure).code.ofType(CodeableConcept).coding[0].code":
                return
        assert False


def test_positive_concept_observation():
    known_issues = [
        "Code [system = http://loinc.org and code = 26436-6] wasn't in value set [url = "
        "http://hl7.org/fhir/ValueSet/observation-category and version = null]",
        "None of the codings provided are in the value set 'IdentifierType' "
        "(http://hl7.org/fhir/ValueSet/identifier-type|4.0.1), and a coding should come from this value set unless it "
        "has no suitable code (note that the validator cannot judge what is suitable) "
        "(codes = http://terminology.hl7.org/CodeSystem/v2-0203#OBI)"
    ]

    with open("resources/concept_observation_bundle_no_error.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        unknown_issues = [issue for issue in result.get("issue", []) if
                          issue.get("diagnostics", "") not in known_issues]
        assert unknown_issues == []


def test_wrong_code_concept_observation():
    with open("resources/concept_observation_bundle_wrong_code.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            if issue.get("severity", "") == "error" and issue.get("location", "")[0] == \
                    "Bundle.entry[0].resource.ofType(Observation).value.ofType(CodeableConcept)":
                assert "None of the codings provided are in the value set " in issue.get("diagnostics", "")
                return
        assert False


@unittest.skip("Not implemented yet")
def test_positive_quantity_observation():
    with open("resources/quantity_observation_bundle_no_error.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            assert "No issues detected during validation" == (issue.get("diagnostics", ""))
            return
        assert False


def test_wrong_unit_code_observation():
    with open("resources/quantity_observation_bundle_wrong_unit.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8092/validate", "application/json")
        for issue in result.get("issue", []):
            if issue.get("severity", "") == "error" and issue.get("location", "")[0] == \
                    "Bundle.entry[0].resource.ofType(Observation).value.ofType(Quantity).code":
                assert "Value is '10*3/mL' but must be '10*3/uL'" == (issue.get("diagnostics", ""))
                return
        assert False
