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

resource "random_password" "postgress_password" {
  length  = 16
  special = false
}

module "monitoring_vm" {
  source         = "terraform-google-modules/bastion-host/google"
  version        = "5.0.0"
  name           = local.monitoring_name
  project        = var.project_id
  zone           = "${var.region}-a"
  network        = module.gcp_network.network_self_link
  subnet         = module.gcp_network.subnets_self_links[0]
  image_family   = "cos-97-lts"
  image_project  = "cos-cloud"
  machine_type   = var.bastion_machine_type
  disk_type      = "pd-ssd"
  members        = var.access_accounts
  startup_script = <<-EOT
    #!/bin/bash
    export TMP_VOLUME=/tmp/compose
    mkdir $TMP_VOLUME
    wget ${var.monitoring_compose_file} -O $TMP_VOLUME/docker-compose.yml
    sudo docker run --rm --env POSTGRES_PASSWORD=${random_password.postgress_password.result} -v /var/run/docker.sock:/var/run/docker.sock -v $TMP_VOLUME:$TMP_VOLUME -w $TMP_VOLUME docker/compose:1.29.2 up -d
    sleep 20s
    curl -XPUT "localhost:3000/api/datasources/1" -H "Accept: application/json" -H "Content-Type: application/json" -d '{"access":"proxy","basicAuth":false,"basicAuthPassword":"","basicAuthUser":"","database":"postgres","isDefault":false,"jsonData":{"postgresVersion":1200,"sslmode":"disable","timescaledb":true},"name":"locust_timescale","orgId":1,"password":"","readOnly":false,"secureJsonData":{"password":"${random_password.postgress_password.result}"},"type":"postgres","url": "postgres:5432","user":"postgres","version":3,"withCredentials":false}'
  EOT
}

resource "google_compute_firewall" "allow_minitoring_rules" {
  project     = var.project_id
  name        = "allow-minitoring-ports"
  network     = module.gcp_network.network_name
  description = "Postgress firewall rule for locust to monitoring server"
  direction   = "INGRESS"
  # TODO: need currect source range settings
  source_ranges           = ["0.0.0.0/0"]
  target_service_accounts = [module.monitoring_vm.service_account]

  allow {
    protocol = "tcp"
    ports    = ["3000", "5432"]
  }
}
