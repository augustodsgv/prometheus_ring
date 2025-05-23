resource "mgc_network_security_groups" "prometheus_ring_swarm_1" {
  provider = mgc
  name = "prometheus_ring_swarm_1"
}

resource "mgc_network_security_groups_rules" "allow_ssh" {
  provider = mgc
  for_each          = { "IPv4" : "0.0.0.0/0", "IPv6" : "::/0" }
  direction         = "ingress"
  ethertype         = each.key
  port_range_max    = 22
  port_range_min    = 22
  protocol          = "tcp"
  remote_ip_prefix  = each.value
  security_group_id = mgc_network_security_groups.prometheus_ring_swarm_1.id
}

resource "mgc_network_security_groups_rules" "allow_mimir" {
  provider = mgc
  for_each          = { "IPv4" : "0.0.0.0/0", "IPv6" : "::/0" }
  direction         = "ingress"
  ethertype         = each.key
  port_range_max    = 8080
  port_range_min    = 8080
  protocol          = "tcp"
  remote_ip_prefix  = each.value
  security_group_id = mgc_network_security_groups.prometheus_ring_swarm_1.id
}

resource "mgc_network_security_groups_rules" "allow_mimir_lb" {
  provider = mgc
  for_each          = { "IPv4" : "0.0.0.0/0", "IPv6" : "::/0" }
  direction         = "ingress"
  ethertype         = each.key
  port_range_max    = 9009
  port_range_min    = 9009
  protocol          = "tcp"
  remote_ip_prefix  = each.value
  security_group_id = mgc_network_security_groups.prometheus_ring_swarm_1.id
}

resource "mgc_network_security_groups_rules" "allow_api" {
  provider = mgc
  for_each          = { "IPv4" : "0.0.0.0/0", "IPv6" : "::/0" }
  direction         = "ingress"
  ethertype         = each.key
  port_range_max    = 9988
  port_range_min    = 9988
  protocol          = "tcp"
  remote_ip_prefix  = each.value
  security_group_id = mgc_network_security_groups.prometheus_ring_swarm_1.id
}

resource "mgc_network_security_groups_rules" "allow_api_grafana" {
  provider = mgc
  for_each          = { "IPv4" : "0.0.0.0/0", "IPv6" : "::/0" }
  direction         = "ingress"
  ethertype         = each.key
  port_range_max    = 3000
  port_range_min    = 3000
  protocol          = "tcp"
  remote_ip_prefix  = each.value
  security_group_id = mgc_network_security_groups.prometheus_ring_swarm_1.id
}