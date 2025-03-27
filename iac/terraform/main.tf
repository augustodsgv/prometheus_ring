terraform {
  required_providers {
    mgc = {
      source  = "MagaluCloud/mgc"
      version = "0.32.2"
    }
  }
}

## SSH key
resource "mgc_ssh_keys" "prom_ring_swarm" {
  provider = mgc
  key      = file(var.ssh_key_path)
  name     = "prom_ring_swarm"
}

# Worker nodes
resource "mgc_virtual_machine_instances" "prom_ring_worker" {
  provider     = mgc
  count        = var.worker_count
  name         = "prom_ring_worker_${count.index}"
  machine_type = var.swarm_machine_type
  image        = var.machine_image
  ssh_key_name = mgc_ssh_keys.prom_ring_swarm.name
}

resource "mgc_network_public_ips" "prom_ring_worker" {
  count       = var.worker_count
  provider    = mgc
  description = "Docker swarm prom_ring_worker ${count.index}"
  vpc_id      = var.vpc_id
}

resource "mgc_network_public_ips_attach" "prom_ring_worker" {
  provider     = mgc
  count        = var.worker_count
  public_ip_id = mgc_network_public_ips.prom_ring_worker[count.index].id
  interface_id = mgc_virtual_machine_instances.prom_ring_worker[count.index].network_interfaces[0].id
}

resource "mgc_network_security_groups_attach" "prom_ring_worker" {
  provider          = mgc
  count             = var.worker_count
  security_group_id = mgc_network_security_groups.prometheus_ring_swarm_1.id
  interface_id      = mgc_virtual_machine_instances.prom_ring_worker[count.index].network_interfaces[0].id
}

# Manager nodes
resource "mgc_virtual_machine_instances" "prom_ring_manager" {
  provider     = mgc
  count        = var.manager_count
  name         = "prom_ring_manager_${count.index}"
  machine_type = var.swarm_machine_type
  image        = var.machine_image
  ssh_key_name = mgc_ssh_keys.prom_ring_swarm.name
}

resource "mgc_network_public_ips" "prom_ring_manager" {
  count       = var.manager_count
  provider    = mgc
  description = "Docker swarm prom_ring_manager ${count.index}"
  vpc_id      = var.vpc_id
}

resource "mgc_network_public_ips_attach" "prom_ring_manager" {
  provider     = mgc
  count        = var.manager_count
  public_ip_id = mgc_network_public_ips.prom_ring_manager[count.index].id
  interface_id = mgc_virtual_machine_instances.prom_ring_manager[count.index].network_interfaces[0].id
}

resource "mgc_network_security_groups_attach" "prom_ring_manager" {
  provider          = mgc
  count             = var.manager_count
  security_group_id = mgc_network_security_groups.prometheus_ring_swarm_1.id
  interface_id      = mgc_virtual_machine_instances.prom_ring_manager[count.index].network_interfaces[0].id
}