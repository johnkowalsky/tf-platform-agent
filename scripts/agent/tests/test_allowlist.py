from allowlist import is_allowed_command, is_allowed_test_path, validate_test_hcl


def test_allows_module_test_path():
    assert is_allowed_test_path("modules/function-app/tests/main.tftest.hcl")


def test_rejects_main_tf():
    assert not is_allowed_test_path("modules/function-app/main.tf")
    assert not is_allowed_test_path("modules/../etc/passwd")


def test_hcl_requires_mock_provider():
    errors = validate_test_hcl('run "x" { command = plan }\n')
    assert any("mock_provider" in e for e in errors)


def test_hcl_rejects_backend():
    content = 'mock_provider "azurerm" {}\nterraform { backend "azurerm" {} }\n'
    errors = validate_test_hcl(content)
    assert errors


def test_commands():
    assert is_allowed_command(["terraform", "init", "-backend=false"])
    assert is_allowed_command(["terraform", "test"])
    assert is_allowed_command(["terraform", "test", "-junit-xml=out.xml"])
    assert not is_allowed_command(["terraform", "apply"])
    assert not is_allowed_command(["bash", "-c", "id"])
