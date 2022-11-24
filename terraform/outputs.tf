# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

output "postgress_password" {
  description = "postgress password in instance for monitoring by generated terraform randomy"
  value       = random_password.postgress_password.result
  sensitive   = true
}

output "instance_internal_ip" {
  description = "GCE's internal ip for monitoring"
  value       = module.monitoring_vm.ip_address
}

output "redis_internal_ip" {
  description = "Memory Store for Redis's internal ip for load-testing"
  value       = module.redis.host
}

output "bastion_hostname" {
  description = "Bastion's hostname for ssh-port-forwording of grafana dashboard"
  value       = module.monitoring_vm.hostname
}

output "cluster_name" {
  description = "GKE Cluster name of Lucust"
  value       = google_container_cluster.autopilot.name
}

output "service_account" {
  description = "Service account for compute resourse"
  value       = module.service_account.email
}

output "repository_name" {
  description = "Repository name of artifactregistry"
  value       = reverse(split("/", google_artifact_registry_repository.repository.id))[0]
}
