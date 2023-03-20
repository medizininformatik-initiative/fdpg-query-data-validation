import json

from main import simple_test


def test_positive_observation():
    with open("quantity_observation_bundle_no_error.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8091/validate", "application/json")
        print(json.dumps(result, indent=4))


def test_wrong_unit_code_observation():
    with open("test/quantity_observation_bundle_wrong_unit.json", encoding="utf-8") as f:
        bundle = json.load(f)
        result = simple_test(json.dumps(bundle), "http://localhost:8091/validate", "application/json")
        for issue in result.get("issue", []):
            if issue.get("severity", "") == "error" and issue.get("location", "")[0] == \
                    "Bundle.entry[0].resource.ofType(Observation).value.ofType(Quantity).code":
                assert "Value is '10*3/mL' but must be '10*3/uL'" == (issue.get("diagnostics", ""))
                return
        assert False

