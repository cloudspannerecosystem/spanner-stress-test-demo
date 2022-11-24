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

variable "project_id" {
  description = "Google Cloud project id"
  type        = string
}

variable "access_accounts" {
  description = "Account List to access Bastion via IAP"
  type        = list(string)
}

variable "credential_file_path" {
  description = "Credential file path of Google Cloud"
  type        = string
}

variable "region" {
  description = "The Google Cloud region to use."
  type        = string
  default     = "asia-northeast1"
}

variable "memory_size_gb" {
  description = "Redis memory size in GiB. Defaulted to 2 GiB"
  type        = number
  default     = 2
}

variable "bastion_machine_type" {
  description = "Bastion machine type. Bastion have monitoring system and so it need many resourses."
  type        = string
  default     = "n2-highcpu-16"
}

variable "monitoring_compose_file" {
  description = "Docker compose file of Grafana and Timescall DB \n ref: https://github.com/SvenskaSpel/locust-plugins/blob/master/locust_plugins/dashboards/docker-compose.yml"
  type        = string
  default     = "https://raw.githubusercontent.com/kazu0716/spanner-stress-test-demo/main/terraform/templates/docker-compose.tmpl.yml"
}
