mock_provider "azurerm" {}

variables {
  name                = "dbw-tp-test"
  resource_group_name = "rg-test"
  location            = "westeurope"
}

run "workspace_disables_public_ip_on_clusters" {
  command = plan

  assert {
    condition     = azurerm_databricks_workspace.this.custom_parameters[0].no_public_ip == true
    error_message = "Clusters must not get a public IP."
  }
}

run "sku_defaults_to_premium" {
  command = plan

  assert {
    condition     = azurerm_databricks_workspace.this.sku == "premium"
    error_message = "Default sku must be premium."
  }
}

run "public_network_defaults_to_true" {
  command = plan

  assert {
    condition     = azurerm_databricks_workspace.this.public_network_access_enabled == true
    error_message = "Default public_network_access_enabled must be true."
  }
}

run "public_network_can_be_disabled" {
  command = plan

  variables {
    public_network_access_enabled = false
  }

  assert {
    condition     = azurerm_databricks_workspace.this.public_network_access_enabled == false
    error_message = "public_network_access_enabled must follow the variable."
  }
}

run "managed_resource_group_name_follows_convention" {
  command = plan

  assert {
    condition     = azurerm_databricks_workspace.this.managed_resource_group_name == "rg-test-dbw-tp-test-managed"
    error_message = "Managed resource group must be <rg>-<name>-managed."
  }
}

run "rejects_invalid_sku" {
  command = plan

  variables {
    sku = "trial"
  }

  expect_failures = [var.sku]
}
