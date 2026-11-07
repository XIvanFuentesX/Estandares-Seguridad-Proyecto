# Módulo networking: hub-and-spoke, DMZ, NSG por zona, UDR hacia el firewall y DNS privado.
# Ningún recurso de este módulo tiene cargo fijo por hora salvo las zonas DNS privadas
# (cargo mensual por zona), que sólo se crean con enable_private_dns = true.

locals {
  hub_reserved_names = {
    management    = "snet-management"
    gateway       = "GatewaySubnet"
    firewall      = "AzureFirewallSubnet"
    firewall_mgmt = "AzureFirewallManagementSubnet"
    bastion       = "AzureBastionSubnet"
  }

  # Flujos permitidos explícitamente (todo lo demás se deniega con prioridad 4096).
  base_rules = [
    {
      zone     = "apps", name = "permitir-dmz-https", priority = 100, direction = "Inbound", access = "Allow",
      protocol = "Tcp", sources = [var.spoke_subnets["dmz"]], ports = ["443"], destination = var.spoke_subnets["apps"]
    },
    {
      zone     = "datos", name = "permitir-apps-postgresql", priority = 100, direction = "Inbound", access = "Allow",
      protocol = "Tcp", sources = [var.spoke_subnets["apps"]], ports = ["5432"], destination = var.spoke_subnets["datos"]
    },
    {
      zone     = "privateendpoints", name = "permitir-https-endpoints-privados", priority = 100, direction = "Inbound", access = "Allow",
      protocol = "Tcp", ports = ["443"], destination = var.spoke_subnets["privateendpoints"],
      sources  = concat([var.spoke_subnets["apps"], var.spoke_subnets["gestion"], var.spoke_subnets["seguridad"]], var.onprem_address_spaces)
    },
    {
      zone     = "datos", name = "denegar-internet-salida", priority = 4000, direction = "Outbound", access = "Deny",
      protocol = "*", sources = ["*"], ports = ["*"], destination = "Internet"
    },
    {
      zone     = "privateendpoints", name = "denegar-internet-salida", priority = 4000, direction = "Outbound", access = "Deny",
      protocol = "*", sources = ["*"], ports = ["*"], destination = "Internet"
    },
  ]

  # Reglas mínimas que exige Application Gateway v2 en su subred (DMZ).
  appgw_rules = var.enable_app_gateway ? [
    {
      zone     = "dmz", name = "permitir-internet-https", priority = 100, direction = "Inbound", access = "Allow",
      protocol = "Tcp", sources = ["Internet"], ports = ["443"], destination = var.spoke_subnets["dmz"]
    },
    {
      zone     = "dmz", name = "permitir-gatewaymanager", priority = 110, direction = "Inbound", access = "Allow",
      protocol = "Tcp", sources = ["GatewayManager"], ports = ["65200-65535"], destination = "*"
    },
    {
      zone     = "dmz", name = "permitir-azureloadbalancer", priority = 120, direction = "Inbound", access = "Allow",
      protocol = "*", sources = ["AzureLoadBalancer"], ports = ["*"], destination = "*"
    },
  ] : []

  bastion_rules = var.enable_bastion_access ? [
    {
      zone     = "gestion", name = "permitir-bastion-ssh-rdp", priority = 100, direction = "Inbound", access = "Allow",
      protocol = "Tcp", sources = [var.hub_subnets["bastion"]], ports = ["22", "3389"], destination = var.spoke_subnets["gestion"]
    },
  ] : []

  nsg_rules = { for r in concat(local.base_rules, local.appgw_rules, local.bastion_rules) : "${r.zone}-${r.name}" => r }

  # UDR: cada zona envía a las demás zonas, a on-premises y (salvo la DMZ con App Gateway) a Internet vía firewall.
  routed_zones = var.enable_firewall ? var.spoke_subnets : {}
  zone_routes = {
    for zone, cidr in local.routed_zones : zone => concat(
      [for other, other_cidr in var.spoke_subnets : { name = "a-${other}", prefix = other_cidr } if other != zone],
      [for i, p in var.onprem_address_spaces : { name = "a-onprem-${i}", prefix = p }],
      zone == "dmz" ? [] : [{ name = "salida-internet", prefix = "0.0.0.0/0" }]
    )
  }

  private_dns_zones = var.enable_private_dns ? {
    blob  = "privatelink.blob.core.windows.net"
    vault = "privatelink.vaultcore.azure.net"
  } : {}
  dns_links = {
    for pair in setproduct(keys(local.private_dns_zones), ["hub", "spoke"]) : "${pair[0]}-${pair[1]}" => {
      zone = pair[0]
      vnet = pair[1]
    }
  }
}

resource "azurerm_virtual_network" "hub" {
  name                = "vnet-${var.name}-hub"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = [var.hub_address_space]
  tags                = var.tags
}

resource "azurerm_virtual_network" "spoke" {
  name                = "vnet-${var.name}-spoke-academico"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = [var.spoke_address_space]
  tags                = var.tags
}

resource "azurerm_subnet" "hub" {
  for_each             = var.hub_subnets
  name                 = local.hub_reserved_names[each.key]
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.hub.name
  address_prefixes     = [each.value]
  # Las subredes reservadas de Azure gestionan su propia salida; la de gestión no tiene salida implícita.
  default_outbound_access_enabled = each.key == "management" ? false : null
}

resource "azurerm_subnet" "spoke" {
  for_each                          = var.spoke_subnets
  name                              = "snet-${each.key}"
  resource_group_name               = var.resource_group_name
  virtual_network_name              = azurerm_virtual_network.spoke.name
  address_prefixes                  = [each.value]
  default_outbound_access_enabled   = false
  private_endpoint_network_policies = each.key == "privateendpoints" ? "Enabled" : "Disabled"
}

resource "azurerm_virtual_network_peering" "hub_to_spoke" {
  name                         = "peer-hub-a-spoke"
  resource_group_name          = var.resource_group_name
  virtual_network_name         = azurerm_virtual_network.hub.name
  remote_virtual_network_id    = azurerm_virtual_network.spoke.id
  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  allow_gateway_transit        = var.enable_vpn_gateway
}

resource "azurerm_virtual_network_peering" "spoke_to_hub" {
  name                         = "peer-spoke-a-hub"
  resource_group_name          = var.resource_group_name
  virtual_network_name         = azurerm_virtual_network.spoke.name
  remote_virtual_network_id    = azurerm_virtual_network.hub.id
  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  # Sólo usa el gateway remoto cuando éste existe (la referencia al ID crea la dependencia).
  use_remote_gateways = var.enable_vpn_gateway && var.vpn_gateway_id != null

  depends_on = [azurerm_virtual_network_peering.hub_to_spoke]
}

resource "azurerm_network_security_group" "spoke" {
  for_each            = var.spoke_subnets
  name                = "nsg-${var.name}-${each.key}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_network_security_rule" "explicit" {
  for_each                    = local.nsg_rules
  name                        = each.value.name
  priority                    = each.value.priority
  direction                   = each.value.direction
  access                      = each.value.access
  protocol                    = each.value.protocol
  source_port_range           = "*"
  source_address_prefix       = length(each.value.sources) == 1 ? each.value.sources[0] : null
  source_address_prefixes     = length(each.value.sources) > 1 ? each.value.sources : null
  destination_port_range      = length(each.value.ports) == 1 ? each.value.ports[0] : null
  destination_port_ranges     = length(each.value.ports) > 1 ? each.value.ports : null
  destination_address_prefix  = each.value.destination
  resource_group_name         = var.resource_group_name
  network_security_group_name = azurerm_network_security_group.spoke[each.value.zone].name
  description                 = "Flujo explícito del SGSI UVCG (${each.value.zone})"
}

resource "azurerm_network_security_rule" "deny_inbound" {
  for_each                    = var.spoke_subnets
  name                        = "denegar-resto-entrante"
  priority                    = 4096
  direction                   = "Inbound"
  access                      = "Deny"
  protocol                    = "*"
  source_port_range           = "*"
  destination_port_range      = "*"
  source_address_prefix       = "*"
  destination_address_prefix  = "*"
  resource_group_name         = var.resource_group_name
  network_security_group_name = azurerm_network_security_group.spoke[each.key].name
  description                 = "Denegación por defecto del tráfico lateral y externo no autorizado"
}

resource "azurerm_subnet_network_security_group_association" "spoke" {
  for_each                  = var.spoke_subnets
  subnet_id                 = azurerm_subnet.spoke[each.key].id
  network_security_group_id = azurerm_network_security_group.spoke[each.key].id
}

# NSG de la subred de gestión del hub: sin entrada salvo denegación explícita.
resource "azurerm_network_security_group" "hub_management" {
  name                = "nsg-${var.name}-hub-management"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  security_rule {
    name                       = "denegar-resto-entrante"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "hub_management" {
  subnet_id                 = azurerm_subnet.hub["management"].id
  network_security_group_id = azurerm_network_security_group.hub_management.id
}

# ---------------------------------------------------------------- UDR (sólo con firewall)
resource "azurerm_route_table" "spoke" {
  for_each                      = local.zone_routes
  name                          = "rt-${var.name}-${each.key}"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  bgp_route_propagation_enabled = false
  tags                          = var.tags

  dynamic "route" {
    for_each = each.value
    content {
      name                   = route.value.name
      address_prefix         = route.value.prefix
      next_hop_type          = "VirtualAppliance"
      next_hop_in_ip_address = var.firewall_private_ip
    }
  }
}

resource "azurerm_subnet_route_table_association" "spoke" {
  for_each       = local.zone_routes
  subnet_id      = azurerm_subnet.spoke[each.key].id
  route_table_id = azurerm_route_table.spoke[each.key].id
}

# Tráfico que entra por la VPN hacia el spoke también pasa por el firewall.
resource "azurerm_route_table" "gateway" {
  count               = var.enable_firewall && var.enable_vpn_gateway ? 1 : 0
  name                = "rt-${var.name}-gateway"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  route {
    name                   = "spoke-via-firewall"
    address_prefix         = var.spoke_address_space
    next_hop_type          = "VirtualAppliance"
    next_hop_in_ip_address = var.firewall_private_ip
  }
}

resource "azurerm_subnet_route_table_association" "gateway" {
  count          = var.enable_firewall && var.enable_vpn_gateway ? 1 : 0
  subnet_id      = azurerm_subnet.hub["gateway"].id
  route_table_id = azurerm_route_table.gateway[0].id
}

# ---------------------------------------------------------------- DNS privado
resource "azurerm_private_dns_zone" "this" {
  for_each            = local.private_dns_zones
  name                = each.value
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "this" {
  for_each              = local.dns_links
  name                  = "link-${each.value.zone}-${each.value.vnet}"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.this[each.value.zone].name
  virtual_network_id    = each.value.vnet == "hub" ? azurerm_virtual_network.hub.id : azurerm_virtual_network.spoke.id
  registration_enabled  = false
  tags                  = var.tags
}

# ---------------------------------------------------------------- Diagnósticos
resource "azurerm_monitor_diagnostic_setting" "nsg" {
  for_each                   = var.enable_diagnostics ? var.spoke_subnets : {}
  name                       = "diag-a-law"
  target_resource_id         = azurerm_network_security_group.spoke[each.key].id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  enabled_log {
    category_group = "allLogs"
  }
}
