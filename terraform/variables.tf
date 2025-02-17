
variable "mgc_api_key" {
  type        = string
  description = "mgc api key"
}

variable "mgc_region" {
  type = string
  description = "Magalu Cloud Region"
  sensitive = true
}

variable "mgc_obj_key_id" {
  type = string
  description = "Object Storage id"
  sensitive = true
}

variable "mgc_obj_key_secret" {
  type = string
  description = "Object Storage Secret"
  sensitive = true
}

variable "ssh_key" {
  type        = string
  default     = ""
  description = "public key to insert to machines"
}

variable "ssh_key_path" {
  type        = string
  default     = "/home/augusto/.ssh/mgc.pub"
  description = "path of public key in this computers"
}

variable "machine_image" {
  type        = string
  default     = "cloud-ubuntu-22.04 LTS"
  description = "virtual machine image"
}

variable "swarm_machine_type" {
  type        = string
  default     = "BV8-32-100"
  description = "swarm node flavor"
}

variable "vpc_id" {
  type        = string
  description = "tenant vpc id"
}

variable "worker_count" {
  type        = number
  default     = 3
  description = "number of woker nodes in the cluster"
}

variable "manager_count" {
  type        = number
  default     = 1 
  description = "number of leader in the cluster"
}

variable "mimir_cluster_version"{
    type        = string
    default     = "v1.30.2"
}

variable "mimir_cluster_nodepool_flavor"{
    type        = string
    default     = "cloud-k8s.gp3.medium"
}

variable "mimir_cluster_nodepool_replicas"{
    type        = number
    default     = 8
}