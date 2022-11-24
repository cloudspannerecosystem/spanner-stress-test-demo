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

provider "google" {
  credentials = file(var.credential_file_path)
}

locals {
  name            = "spanner-stress-test"
  network_name    = "${local.name}-network"
  subnet_name     = "${local.name}-subnet"
  pods_range_name = "ip-range-pods-${local.name}"
  svc_range_name  = "ip-range-svc-${local.name}"
  cluster_name    = "${local.name}-gke"
  redis_name      = "${local.name}-redis"
  monitoring_name = "${local.name}-monitoring"
  router_name     = "${local.name}-router"
  nat_config_name = "${local.name}-nat-config"
  repo_name       = "${local.name}-repo"
}

module "redis" {
  source                  = "terraform-google-modules/memorystore/google"
  version                 = "4.4.1"
  name                    = local.redis_name
  project                 = var.project_id
  region                  = var.region
  transit_encryption_mode = "DISABLED"
  connect_mode            = "DIRECT_PEERING"
  authorized_network      = module.gcp_network.network_name
  memory_size_gb          = var.memory_size_gb
}

resource "google_container_cluster" "autopilot" {
  name            = local.cluster_name
  project         = var.project_id
  location        = var.region
  network         = module.gcp_network.network_name
  subnetwork      = module.gcp_network.subnets_names[0]
  networking_mode = "VPC_NATIVE"
  ip_allocation_policy {
    cluster_secondary_range_name  = local.pods_range_name
    services_secondary_range_name = local.svc_range_name
  }
  enable_autopilot = true
}

module "service_account" {
  source     = "terraform-google-modules/service-accounts/google"
  version    = "4.1.1"
  project_id = var.project_id
  names      = ["spanner-stress-test"]
  project_roles = [
    "${var.project_id}=>roles/cloudprofiler.agent",
    "${var.project_id}=>roles/containerregistry.ServiceAgent",
    "${var.project_id}=>roles/monitoring.metricWriter",
    "${var.project_id}=>roles/opsconfigmonitoring.resourceMetadata.writer",
    "${var.project_id}=>roles/spanner.admin",
    "${var.project_id}=>roles/stackdriver.resourceMetadata.writer",
    "${var.project_id}=>roles/artifactregistry.reader",
  ]
}

resource "google_artifact_registry_repository" "repository" {
  project       = var.project_id
  location      = var.region
  repository_id = local.repo_name
  description   = "repository for spanner stress test demo application"
  format        = "DOCKER"
}
