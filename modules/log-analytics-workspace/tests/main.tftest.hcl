mock_provider "azurerm" {}

variables {
  name                = "log-tp-test"
  resource_group_name = "rg-test"
  location            = "westeurope"
}

run "workspace_uses_pergb_sku" {
  command = plan

  assert {
    condition     = azurerm_log_analytics_workspace.this.sku == "PerGB2018"
    error_message = "The workspace must use the PerGB2018 sku."
  }
}

run "retention_defaults_to_thirty_days" {
  command = plan

  assert {
    condition     = azurerm_log_analytics_workspace.this.retention_in_days == 30
    error_message = "Default retention must be 30 days."
  }
}

run "retention_follows_override" {
  command = plan

  variables {
    retention_in_days = 90
  }

  assert {
    condition     = azurerm_log_analytics_workspace.this.retention_in_days == 90
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
