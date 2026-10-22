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
    result, errors = validate_decision(payload, allowed_modules={"function-app"})
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


def test_rejects_cross_module_path():
    payload = {
        "decision": "update_tests",
        "modules": [
            {
                "name": "function-app",
                "action": "update_tests",
                "path": "modules/network/tests/main.tftest.hcl",
                "content": 'mock_provider "azurerm" {}\nrun "x" { command = plan }\n',
            }
        ],
    }
    result, errors = validate_decision(payload, allowed_modules={"function-app"})
    assert result is None
    assert any("path" in e for e in errors)


def test_rejects_undiscovered_module():
    payload = {
        "decision": "update_tests",
        "modules": [
            {
                "name": "network",
                "action": "update_tests",
                "path": "modules/network/tests/main.tftest.hcl",
                "content": 'mock_provider "azurerm" {}\nrun "x" { command = plan }\n',
            }
        ],
    }
    result, errors = validate_decision(payload, allowed_modules={"function-app"})
    assert result is None
    assert any("discovered" in e for e in errors)


def test_rejects_missing_override_when_module_has_external(tmp_path):
    from pathlib import Path

    module = Path(tmp_path) / "modules" / "function-app"
    module.mkdir(parents=True)
    (module / "main.tf").write_text(
        'data "external" "build_info" { program = ["true"] }\n', encoding="utf-8"
    )
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
    }
    result, errors = validate_decision(
        payload, allowed_modules={"function-app"}, repo=Path(tmp_path)
    )
    assert result is None
    assert any("override_data" in e for e in errors)
