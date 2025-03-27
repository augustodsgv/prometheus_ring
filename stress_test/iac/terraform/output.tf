output "prom_stress_test_managers_ips" {
  value = {
    for idx, vm in mgc_virtual_machine_instances.prom_stress_test_manager :
    "manager-${idx}" => {
      public_ip  = mgc_network_public_ips.prom_stress_test_manager[idx].public_ip,
      private_ip = vm.network_interfaces[0].local_ipv4
    }
  }
}

output "prom_stress_test_workers_ips" {
  value = {
    for idx, vm in mgc_virtual_machine_instances.prom_stress_test_worker :
    "worker-${idx}" => {
      public_ip  = mgc_network_public_ips.prom_stress_test_worker[idx].public_ip,
      private_ip = vm.network_interfaces[0].local_ipv4
    }
  }
}
