resource "mgc_network_security_groups" "prometheus_ring_swarm" {
  provider = mgc.sudeste
  name = "prometheus_ring_swarm"
}

resource "mgc_network_security_groups_rules" "allow_ssh" {
  provider = mgc.sudeste
  for_each          = { "IPv4" : "0.0.0.0/0", "IPv6" : "::/0" }
  direction         = "ingress"
  ethertype         = each.key
  port_range_max    = 22
  port_range_min    = 22
  protocol          = "tcp"
  remote_ip_prefix  = each.value
  security_group_id = mgc_network_security_groups.prometheus_ring_swarm.id
}

resource "mgc_network_security_groups_rules" "allow_mimir" {
  provider = mgc.sudeste
  for_each          = { "IPv4" : "0.0.0.0/0", "IPv6" : "::/0" }
  direction         = "ingress"
  ethertype         = each.key
  port_range_max    = 8080
  port_range_min    = 8080
  protocol          = "tcp"
  remote_ip_prefix  = each.value
  security_group_id = mgc_network_security_groups.prometheus_ring_swarm.id
}

resource "mgc_network_security_groups_rules" "allow_mimir_lb" {
  provider = mgc.sudeste
  for_each          = { "IPv4" : "0.0.0.0/0", "IPv6" : "::/0" }
  direction         = "ingress"
  ethertype         = each.key
  port_range_max    = 9009
  port_range_min    = 9009
  protocol          = "tcp"
  remote_ip_prefix  = each.value
  security_group_id = mgc_network_security_groups.prometheus_ring_swarm.id
}

resource "mgc_network_security_groups_rules" "allow_api" {
  provider = mgc.sudeste
  for_each          = { "IPv4" : "0.0.0.0/0", "IPv6" : "::/0" }
  direction         = "ingress"
  ethertype         = each.key
  port_range_max    = 9988
  port_range_min    = 9988
  protocol          = "tcp"
  remote_ip_prefix  = each.value
  security_group_id = mgc_network_security_groups.prometheus_ring_swarm.id
}