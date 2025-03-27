terraform {
  required_providers {
    mgc = {
      source = "MagaluCloud/mgc"
      version = "0.32.2"
    }
  }
}

# SSH key
resource "mgc_ssh_keys" "prom_stress_test_key" {
  provider = mgc
  key  = file(var.ssh_key_path)
  name = "prom_stress_test_key"
}

# Worker nodes
resource "mgc_virtual_machine_instances" "prom_stress_test_worker" {
  provider = mgc
  count = var.worker_count
  name         = "prom_stress_test_worker_${count.index}"
  machine_type = var.swarm_machine_type
  image        = var.machine_image
  ssh_key_name = mgc_ssh_keys.prom_stress_test_key.name
}

resource "mgc_network_public_ips" "prom_stress_test_worker" {
  count = var.worker_count
  provider = mgc
  description = "Docker swarm prom_stress_test_worker ${count.index}"
  vpc_id      = var.vpc_id
}

resource "mgc_network_public_ips_attach" "prom_stress_test_worker" {
  provider = mgc
  count = var.worker_count
  public_ip_id = mgc_network_public_ips.prom_stress_test_worker[count.index].id
  interface_id = mgc_virtual_machine_instances.prom_stress_test_worker[count.index].network_interfaces[0].id
}

resource "mgc_network_security_groups_attach" "prom_stress_test_worker" {
  provider = mgc
  count = var.worker_count
  security_group_id = mgc_network_security_groups.prom_stress_test_swarm.id
  interface_id = mgc_virtual_machine_instances.prom_stress_test_worker[count.index].network_interfaces[0].id
}

# Manager nodes
resource "mgc_virtual_machine_instances" "prom_stress_test_manager" {
  provider = mgc
  count = var.manager_count
  name         = "prom_stress_test_manager_${count.index}"
  machine_type = var.swarm_machine_type
  image        = var.machine_image
  ssh_key_name = mgc_ssh_keys.prom_stress_test_key.name
}

resource "mgc_network_public_ips" "prom_stress_test_manager" {
  count = var.manager_count
  provider = mgc
  description = "Docker swarm prom_stress_test_manager ${count.index}"
  vpc_id      = var.vpc_id
}

resource "mgc_network_public_ips_attach" "prom_stress_test_manager" {
  provider = mgc
  count = var.manager_count
  public_ip_id = mgc_network_public_ips.prom_stress_test_manager[count.index].id
  interface_id = mgc_virtual_machine_instances.prom_stress_test_manager[count.index].network_interfaces[0].id
}

resource "mgc_network_security_groups_attach" "prom_stress_test_manager" {
  provider = mgc
  count = var.manager_count
  security_group_id = mgc_network_security_groups.prom_stress_test_swarm.id
  interface_id = mgc_virtual_machine_instances.prom_stress_test_manager[count.index].network_interfaces[0].id
}