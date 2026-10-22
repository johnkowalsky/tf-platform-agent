mock_provider "azurerm" {}

# data.external runs the real build-info.sh during plan; mocked apply is not used
# because that script is untrusted input from the module tree. Plan-time asserts
# still cover the security-relevant configuration without Azure credentials.

variables {
  name                          = "func-tp-test"
  resource_group_name           = "rg-test"
  location                      = "westeurope"
  storage_account_name          = "sttptest001"
  storage_account_id            = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.Storage/storageAccounts/sttptest001"
  public_network_access_enabled = true
}

run "app_requires_https_and_tls12" {
  command = plan

  assert {
    condition     = azurerm_linux_function_app.this.https_only == true
    error_message = "HTTPS must be required."
  }

  assert {
    condition     = azurerm_linux_function_app.this.site_config[0].minimum_tls_version == "1.2"
    error_message = "TLS 1.2 must be the minimum."
  }
}

run "ftps_state_is_all_allowed" {
  command = plan

  assert {
    condition     = azurerm_linux_function_app.this.site_config[0].ftps_state == "AllAllowed"
    error_message = "FTPS state must match the module default of AllAllowed."
  }
}

run "uses_managed_identity_for_runtime_storage" {
  command = plan

  assert {
    condition     = azurerm_linux_function_app.this.storage_uses_managed_identity == true
    error_message = "The function app must use a managed identity for storage."
  }

  assert {
    condition     = azurerm_role_assignment.runtime_storage.role_definition_name == "Storage Blob Data Owner"
    error_message = "Runtime storage role must be Storage Blob Data Owner."
  }
}

run "service_plan_name_follows_convention" {
  command = plan

  assert {
    condition     = azurerm_service_plan.this.name == "asp-func-tp-test"
    error_message = "The service plan name must start with asp-."
  }
}
