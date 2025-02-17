resource "mgc_kubernetes_cluster" "mimir_cluster" {
  name                 = "mimir-cluster"
  version              = var.mimir_cluster_version
  enabled_server_group = false
  description          = "Cluster for mimir deployment"
}

resource "mgc_kubernetes_nodepool" "mimir_nodepool" {
  name         = "mimir_nodepool"
  depends_on =  [mgc_kubernetes_cluster.mimir_cluster]
  cluster_id = mgc_kubernetes_cluster.mimir_cluster.id
  flavor_name  = var.mimir_cluster_nodepool_flavor
  replicas     = 8
}
