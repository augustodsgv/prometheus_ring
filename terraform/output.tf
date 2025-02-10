# output "prometheus_ring_workers_public_ips" {
#   value = {
#     for idx, vm in mgc_virtual_machine_instances.prometheus_ring_worker:
#       idx => mgc_network_public_ips.prometheus_ring_worker[idx].public_ip
#   }
# }

# # output "prometheus_ring_workers_private_ips" {
# #   # value = {
# #   #   for vm in mgc_virtual_machine_instances.prometheus_ring_worker:
# #   #     vm => vm.ipv4
# #   # }
# #   value = [for vm in mgc_virtual_machine_instances.prometheus_ring_worker : vm.interfaces[0].ipv4]
# # }

# output "prometheus_ring_worker_ipv4" {
#   value = [for vm in mgc_virtual_machine_instances.prometheus_ring_worker : vm.network_interfaces[0].local_ipv4]
# }

# output "prometheus_ring_managers_public_ips" {
#   value = {
#     for idx, vm in mgc_virtual_machine_instances.prometheus_ring_manager:
#       idx => mgc_network_public_ips.prometheus_ring_manager[idx].public_ip
#   }
# }

# output "prometheus_ring_manager_ipv4" {
#   value = [for vm in mgc_virtual_machine_instances.prometheus_ring_manager : vm.network_interfaces[0].local_ipv4]
# }

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
