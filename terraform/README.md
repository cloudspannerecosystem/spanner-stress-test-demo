## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.2.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_google"></a> [google](#provider\_google) | 4.36.0 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.4.3 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_cloud_nat"></a> [cloud\_nat](#module\_cloud\_nat) | terraform-google-modules/cloud-nat/google | 2.2.1 |
| <a name="module_gcp_network"></a> [gcp\_network](#module\_gcp\_network) | terraform-google-modules/network/google | >= 4.0.1, < 5.0.0 |
| <a name="module_monitoring_vm"></a> [monitoring\_vm](#module\_monitoring\_vm) | terraform-google-modules/bastion-host/google | 5.0.0 |
| <a name="module_redis"></a> [redis](#module\_redis) | terraform-google-modules/memorystore/google | 4.4.1 |
| <a name="module_service_account"></a> [service\_account](#module\_service\_account) | terraform-google-modules/service-accounts/google | 4.1.1 |

## Resources

| Name | Type |
|------|------|
| [google_artifact_registry_repository.repository](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/artifact_registry_repository) | resource |
| [google_compute_firewall.allow_minitoring_rules](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_firewall) | resource |
| [google_compute_router.router](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_router) | resource |
| [google_container_cluster.autopilot](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster) | resource |
| [random_password.postgress_password](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/password) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_access_accounts"></a> [access\_accounts](#input\_access\_accounts) | Account List to access Bastion via IAP | `list(string)` | n/a | yes |
| <a name="input_bastion_machine_type"></a> [bastion\_machine\_type](#input\_bastion\_machine\_type) | Bastion machine type. Bastion have monitoring system and so it need many resourses. | `string` | `"n2-highcpu-16"` | no |
| <a name="input_credential_file_path"></a> [credential\_file\_path](#input\_credential\_file\_path) | Credential file path of Google Cloud | `string` | n/a | yes |
| <a name="input_memory_size_gb"></a> [memory\_size\_gb](#input\_memory\_size\_gb) | Redis memory size in GiB. Defaulted to 2 GiB | `number` | `2` | no |
| <a name="input_monitoring_compose_file"></a> [monitoring\_compose\_file](#input\_monitoring\_compose\_file) | Docker compose file of Grafana and Timescall DB <br> ref: https://github.com/SvenskaSpel/locust-plugins/blob/master/locust_plugins/dashboards/docker-compose.yml | `string` | `"https://raw.githubusercontent.com/kazu0716/spanner-stress-test-demo/main/terraform/templates/docker-compose.tmpl.yml"` | no |
| <a name="input_project_id"></a> [project\_id](#input\_project\_id) | Google Cloud project id | `string` | n/a | yes |
| <a name="input_region"></a> [region](#input\_region) | The Google Cloud region to use. | `string` | `"asia-northeast1"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_bastion_hostname"></a> [bastion\_hostname](#output\_bastion\_hostname) | Bastion's hostname for ssh-port-forwording of grafana dashboard |
| <a name="output_cluster_name"></a> [cluster\_name](#output\_cluster\_name) | GKE Cluster name of Lucust |
| <a name="output_instance_internal_ip"></a> [instance\_internal\_ip](#output\_instance\_internal\_ip) | GCE's internal ip for monitoring |
| <a name="output_postgress_password"></a> [postgress\_password](#output\_postgress\_password) | postgress password in instance for monitoring by generated terraform randomy |
| <a name="output_redis_internal_ip"></a> [redis\_internal\_ip](#output\_redis\_internal\_ip) | Memory Store for Redis's internal ip for load-testing |
| <a name="output_repository_name"></a> [repository\_name](#output\_repository\_name) | Repository name of artifactregistry |
| <a name="output_service_account"></a> [service\_account](#output\_service\_account) | Service account for compute resourse |
