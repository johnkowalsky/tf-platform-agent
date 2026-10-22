from pathlib import Path

from allowlist import (
    is_allowed_command,
    is_allowed_test_path,
    module_external_data_names,
    validate_test_hcl,
)


def test_allows_module_test_path():
    assert is_allowed_test_path("modules/function-app/tests/main.tftest.hcl")
    assert is_allowed_test_path(
        "modules/function-app/tests/main.tftest.hcl", module="function-app"
    )


def test_rejects_other_module_path():
    assert not is_allowed_test_path(
        "modules/storage-account/tests/main.tftest.hcl", module="function-app"
    )


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


def test_hcl_rejects_apply_and_external():
    apply = 'mock_provider "azurerm" {}\nrun "x" { command = apply }\n'
    assert any("apply" in e for e in validate_test_hcl(apply))
    external = 'mock_provider "azurerm" {}\ndata "external" "x" { program = ["true"] }\n'
    assert any("external" in e for e in validate_test_hcl(external))
    local = 'mock_provider "azurerm" {}\nresource "null_resource" "x" { provisioner "local-exec" { command = "id" } }\n'
    assert validate_test_hcl(local)


def test_requires_override_data_for_module_external(tmp_path: Path):
    module = tmp_path / "modules" / "function-app"
    module.mkdir(parents=True)
    (module / "main.tf").write_text(
        'data "external" "build_info" { program = ["true"] }\n', encoding="utf-8"
    )
    names = module_external_data_names(module)
    assert names == ["build_info"]
    missing = 'mock_provider "azurerm" {}\nrun "x" { command = plan }\n'
    errors = validate_test_hcl(missing, required_external_overrides=names)
    assert any("override_data" in e for e in errors)
    ok = (
        'mock_provider "azurerm" {}\n'
        "override_data {\n"
        "  target = data.external.build_info\n"
        '  values = { result = { revision = "x" } }\n'
        "}\n"
        'run "x" { command = plan }\n'
    )
    assert validate_test_hcl(ok, required_external_overrides=names) == []


def test_commands():
    assert is_allowed_command(["terraform", "init", "-backend=false"])
    assert is_allowed_command(["terraform", "test"])
    assert is_allowed_command(["terraform", "test", "-junit-xml=out.xml"])
    assert not is_allowed_command(["terraform", "apply"])
    assert not is_allowed_command(["bash", "-c", "id"])
