mock_provider "azurerm" {}

variables {
  name                = "log-tp-test"
  resource_group_name = "rg-test"
  location            = "westeurope"
  retention_in_days   = 30
}

run "workspace_uses_pergb_sku_and_retention" {
  command = plan

  assert {
    condition     = azurerm_log_analytics_workspace.this.sku == "PerGB2018"
    error_message = "The workspace must use the PerGB2018 sku."
  }

  assert {
    condition     = azurerm_log_analytics_workspace.this.retention_in_days == 30
    error_message = "Retention must match var.retention_in_days."
  }
}

run "names_the_workspace_from_the_variable" {
  command = plan

  assert {
    condition     = azurerm_log_analytics_workspace.this.name == "log-tp-test"
    error_message = "The workspace name must match var.name."
  }
}
