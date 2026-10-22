mock_provider "azurerm" {
  mock_data "azurerm_role_definition" {
    defaults = {
      id = "/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Authorization/roleDefinitions/4633458b-17de-408a-b874-0445c86b69e6"
    }
  }
}

variables {
  name                = "kv-tp-test"
  resource_group_name = "rg-test"
  location            = "westeurope"
  tenant_id           = "00000000-0000-0000-0000-000000000000"
  allowed_subnet_ids = [
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.Network/virtualNetworks/vnet-test/subnets/snet-apps"
  ]
  secret_readers = {
    adf  = "11111111-1111-1111-1111-111111111111"
    func = "22222222-2222-2222-2222-222222222222"
  }
}

run "vault_uses_rbac_and_purge_protection" {
  command = plan

  assert {
    condition     = azurerm_key_vault.this.rbac_authorization_enabled == true
    error_message = "The vault must use role-based access, not access policies."
  }

  assert {
    condition     = azurerm_key_vault.this.purge_protection_enabled == true
    error_message = "Purge protection must be on."
  }
}

run "network_acls_deny_by_default" {
  command = plan

  assert {
    condition     = azurerm_key_vault.this.network_acls[0].default_action == "Deny"
    error_message = "Network ACLs must deny by default."
  }

  assert {
    condition     = length(azurerm_key_vault.this.network_acls[0].virtual_network_subnet_ids) == 1
    error_message = "Allowed subnets must be passed through to the vault."
  }
}

run "creates_one_role_assignment_per_reader" {
  command = plan

  assert {
    condition     = length(azurerm_role_assignment.secret_reader) == 2
    error_message = "Expected one role assignment for each secret reader."
  }
}
