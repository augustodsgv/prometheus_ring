output "prometheus_ring_managers_ips" {
  value = {
    for idx, vm in mgc_virtual_machine_instances.prometheus_ring_manager :
    "manager-${idx}" => {
      public_ip  = mgc_network_public_ips.prometheus_ring_manager[idx].public_ip,
      private_ip = vm.network_interfaces[0].local_ipv4
    }
  }
}

output "prometheus_ring_workers_ips" {
  value = {
    for idx, vm in mgc_virtual_machine_instances.prometheus_ring_worker :
    "worker-${idx}" => {
      public_ip  = mgc_network_public_ips.prometheus_ring_worker[idx].public_ip,
      private_ip = vm.network_interfaces[0].local_ipv4
    }
  }
}