mock_provider "azurerm" {}

variables {
  name                = "lake-blob"
  resource_group_name = "rg-test"
  location            = "westeurope"
  subnet_id           = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.Network/virtualNetworks/vnet-test/subnets/snet-endpoints"
  target_resource_id  = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.Storage/storageAccounts/sttptest001"
  subresource_name    = "blob"
  private_dns_zone_id = null
}

run "names_follow_the_convention" {
  command = plan

  assert {
    condition     = azurerm_private_endpoint.this.name == "pe-lake-blob"
    error_message = "The private endpoint name must start with pe-."
  }

  assert {
    condition     = azurerm_private_endpoint.this.private_service_connection[0].name == "psc-lake-blob"
    error_message = "The private service connection name must start with psc-."
  }
}

run "connection_is_automatic" {
  command = plan

  assert {
    condition     = azurerm_private_endpoint.this.private_service_connection[0].is_manual_connection == false
    error_message = "The connection must be automatic, not manual."
  }

  assert {
    condition     = azurerm_private_endpoint.this.private_service_connection[0].subresource_names[0] == "blob"
    error_message = "The subresource must match var.subresource_name."
  }
}

run "omits_dns_zone_group_when_zone_is_null" {
  command = plan

  assert {
    condition     = length(azurerm_private_endpoint.this.private_dns_zone_group) == 0
    error_message = "No DNS zone group should be created when private_dns_zone_id is null."
  }
}

run "attaches_dns_zone_group_when_zone_is_set" {
  command = plan

  variables {
    private_dns_zone_id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.Network/privateDnsZones/privatelink.blob.core.windows.net"
  }

  assert {
    condition     = length(azurerm_private_endpoint.this.private_dns_zone_group) == 1
    error_message = "A DNS zone group must be created when private_dns_zone_id is set."
  }

  assert {
    condition     = azurerm_private_endpoint.this.private_dns_zone_group[0].private_dns_zone_ids[0] == "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-test/providers/Microsoft.Network/privateDnsZones/privatelink.blob.core.windows.net"
    error_message = "The DNS zone group must reference the provided zone id."
  }
}
