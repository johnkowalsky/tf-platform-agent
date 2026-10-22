mock_provider "azurerm" {}

variables {
  name                       = "adf-tp-test"
  resource_group_name        = "rg-test"
  location                   = "westeurope"
  log_analytics_workspace_id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.OperationalInsights/workspaces/log-test"
  linked_storage_accounts = {
    raw = "https://sttptest001.dfs.core.windows.net/"
  }
}

run "factory_uses_system_assigned_identity" {
  command = plan

  assert {
    condition     = length(azurerm_data_factory.this.identity) == 1
    error_message = "The factory must have a system-assigned identity."
  }

  assert {
    condition     = azurerm_data_factory.this.identity[0].type == "SystemAssigned"
    error_message = "The identity type must be SystemAssigned."
  }
}

run "creates_one_linked_service_per_lake" {
  command = plan

  assert {
    condition     = length(azurerm_data_factory_linked_service_data_lake_storage_gen2.this) == 1
    error_message = "Expected one linked service for each linked storage account."
  }

  assert {
    condition     = azurerm_data_factory_linked_service_data_lake_storage_gen2.this["raw"].use_managed_identity == true
    error_message = "Linked services must use the managed identity."
  }
}

run "diagnostic_setting_targets_pipeline_and_activity_runs" {
  command = plan

  assert {
    condition     = azurerm_monitor_diagnostic_setting.this.name == "diag-adf-tp-test"
    error_message = "Diagnostic setting name must follow diag-<factory-name>."
  }

  assert {
    condition = length([
      for log in azurerm_monitor_diagnostic_setting.this.enabled_log : log
      if log.category == "PipelineRuns" || log.category == "ActivityRuns"
    ]) == 2
    error_message = "Diagnostics must enable PipelineRuns and ActivityRuns."
  }
}

run "public_network_defaults_to_true" {
  command = plan

  assert {
    condition     = azurerm_data_factory.this.public_network_enabled == true
    error_message = "Default public_network_enabled must be true."
  }
}

run "public_network_can_be_disabled" {
  command = plan

  variables {
    public_network_enabled = false
  }

  assert {
    condition     = azurerm_data_factory.this.public_network_enabled == false
    error_message = "public_network_enabled must follow the variable."
  }
}
