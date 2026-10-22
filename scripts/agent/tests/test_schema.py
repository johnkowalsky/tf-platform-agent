from schema import validate_decision


def test_update_tests_ok():
    payload = {
        "decision": "update_tests",
        "modules": [
            {
                "name": "function-app",
                "action": "update_tests",
                "path": "modules/function-app/tests/main.tftest.hcl",
                "content": 'mock_provider "azurerm" {}\nrun "x" { command = plan }\n',
            }
        ],
        "findings": ["note"],
        "summary": "ok",
    }
    result, errors = validate_decision(payload)
    assert errors == []
    assert result["decision"] == "update_tests"


def test_rejects_main_tf_path():
    payload = {
        "decision": "update_tests",
        "modules": [
            {
                "name": "function-app",
                "action": "update_tests",
                "path": "modules/function-app/main.tf",
                "content": 'mock_provider "azurerm" {}\n',
            }
        ],
    }
    result, errors = validate_decision(payload)
    assert result is None
    assert errors
