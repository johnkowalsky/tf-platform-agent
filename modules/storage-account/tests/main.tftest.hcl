mock_provider "azurerm" {}

variables {
  name                = "sttptest001"
  resource_group_name = "rg-test"
  location            = "westeurope"
  is_data_lake        = true
  containers          = ["raw", "curated"]
  allowed_subnet_ids = [
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.Network/virtualNetworks/vnet-test/subnets/snet-apps"
  ]
}

run "account_is_locked_down_by_default" {
  command = plan

  assert {
    condition     = azurerm_storage_account.this.min_tls_version == "TLS1_2"
    error_message = "The account must require TLS 1.2."
  }

  assert {
    condition     = azurerm_storage_account.this.allow_nested_items_to_be_public == false
    error_message = "Public blob access must be off."
  }

  assert {
    condition     = azurerm_storage_account_network_rules.this.default_action == "Deny"
    error_message = "Network access must be denied by default."
  }
}

run "hierarchical_namespace_follows_is_data_lake" {
  command = plan

  assert {
    condition     = azurerm_storage_account.this.is_hns_enabled == true
    error_message = "is_hns_enabled must match var.is_data_lake."
  }
}

run "network_rules_keep_allowed_subnets" {
  command = plan

  assert {
    condition     = length(azurerm_storage_account_network_rules.this.virtual_network_subnet_ids) == 1
    error_message = "Allowed subnet IDs must be passed to the network rules."
  }
}

run "creates_one_container_per_name" {
  command = plan

  assert {
    condition     = length(azurerm_storage_container.this) == 2
    error_message = "Expected one container for each name."
  }
}

run "rejects_invalid_name" {
  command = plan

  variables {
    name = "Invalid-Name"
  }

  expect_failures = [var.name]
}
