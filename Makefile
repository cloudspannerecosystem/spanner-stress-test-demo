# !make

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

include .env

CURRENT_DIR := $(dir $(lastword $(MAKEFILE_LIST)))
APP_DIR := $(CURRENT_DIR)/apps

LOCAL_DEV_CONFIG_NAME := emulator
LOCAL_DEV_CLOUD_PROJECT := test-local
# NOTE: add google API if you add enabled service
ENABLE_APIS := spanner.googleapis.com artifactregistry.googleapis.com run.googleapis.com cloudbuild.googleapis.com sourcerepo.googleapis.com container.googleapis.com cloudtrace.googleapis.com gkehub.googleapis.com iap.googleapis.com monitoring.googleapis.com

COMMIT_SHA = $(shell git rev-parse --short HEAD)
REPOGITORY = $(REGION)-docker.pkg.dev/$(GOOGLE_CLOUD_PROJECT)/$(REPOGITORY_NAME)

APP_URL = $(shell gcloud run services describe $(SERVICE_NAME) --platform managed --region $(REGION) --format 'value(status.url)')
INSTANCE_IP = $(shell cd $(CURRENT_DIR)/terraform && terraform output -raw instance_internal_ip)
REDIS_IP = $(shell cd $(CURRENT_DIR)/terraform && terraform output -raw redis_internal_ip)
PG_PASSWORD = $(shell cd $(CURRENT_DIR)/terraform && terraform output -raw postgress_password)
BASTION_NAME = $(shell cd $(CURRENT_DIR)/terraform && terraform output -raw bastion_hostname)
BASTION_ZONE = $(shell gcloud compute instances list --filter="name=('$(BASTION_NAME)')" --format 'csv[no-heading](zone)')
CLUSTER_NAME= $(shell cd $(CURRENT_DIR)/terraform && terraform output -raw cluster_name)
SERVICE_ACCOUNT= $(shell cd $(CURRENT_DIR)/terraform && terraform output -raw service_account)
REPOGITORY_NAME= $(shell cd $(CURRENT_DIR)/terraform && terraform output -raw repository_name)
NODE_NUM = 1

# NOTE: commands for local development followings
.PHONY: create.emulator.config
create.emulator.config:
	@gcloud config configurations create $(LOCAL_DEV_CONFIG_NAME)
	@gcloud config set auth/disable_credentials true
	@yes | gcloud config set project $(LOCAL_DEV_CLOUD_PROJECT)
	@gcloud config set api_endpoint_overrides/spanner http://localhost:9020/

.PHONY: set.emulator.config
set.emulator.config:
	@yes | gcloud config set project $(LOCAL_DEV_CLOUD_PROJECT)

.PHONY: create.emulator.database
create.emulator.database:
	@gcloud config configurations activate $(LOCAL_DEV_CONFIG_NAME)
	@gcloud spanner instances create $(INSTANCE_NAME) --config=emulator-config --description=Emulator --nodes=1
	@gcloud spanner databases create $(DATABASE_NAME) --instance=$(INSTANCE_NAME) --ddl-file=$(APP_DIR)/schemas/tables.sql

.PHONY: run.spanner-cli
run.spanner-cli:
	@docker compose up -d spanner-cli
	@docker compose exec spanner-cli spanner-cli -p $(LOCAL_DEV_CLOUD_PROJECT) -i $(INSTANCE_NAME) -d $(DATABASE_NAME)

.PHONY: run.local-app
run.local-app:
	@docker compose up -d spanner
	@sleep 3s
	@make create.emulator.database
	@GOOGLE_CLOUD_PROJECT=$(LOCAL_DEV_CLOUD_PROJECT) INSTANCE_NAME=$(INSTANCE_NAME) DATABASE_NAME=$(DATABASE_NAME) docker compose up -d app

.PHONY: run.local-locust
run.local-locust:
	@docker compose up -d redis postgres grafana
	@sleep 5s
	@docker compose up -d locust

.PHONY: load.local-data
load.local-data:
	@echo "==== build a script image ===="
	@cd $(APP_DIR)/scripts && docker build -t masterdata-generatoer:0.1 .
	@echo "==== run a script on docker to create masters ===="
	@docker run --rm masterdata-generatoer:0.1 python main.py
	@echo "==== remove a script image in local ===="
	@docker rmi -f masterdata-generatoer:0.1

.PHONY: create.dbdoc
create.dbdoc:
	@cd $(APP_DIR) && tbls doc spanner://$(GOOGLE_CLOUD_PROJECT)/$(INSTANCE_NAME)/$(DATABASE_NAME)

.PHONY: run.workflows
run.workflows:
	@act -P ubuntu-latest=lucasalt/act_base:latest

# NOTE: commands for cloud environment followings
.PHONY: set.cloud.config
set.cloud.config:
	@echo "==== Set cloud config for Google Cloud ===="
	@gcloud config set project $(GOOGLE_CLOUD_PROJECT)
	@gcloud config set run/region $(REGION)
	@gcloud config set run/platform managed
	@gcloud services enable $(ENABLE_APIS)

.PHONY: connect.cluster
connect.cluster:
	@echo "==== Connect the locust to GKE cluster ===="
	@gcloud container clusters get-credentials $(CLUSTER_NAME) --region $(REGION) --project $(GOOGLE_CLOUD_PROJECT)

.PHONY: create.database
create.database:
	@echo "==== Create instance and database of Cloud Spanner ===="
	@yes | gcloud spanner instances create $(INSTANCE_NAME) --config=regional-$(REGION) --description=$(INSTANCE_NAME) --nodes=1
	@gcloud spanner databases create $(DATABASE_NAME) --instance=$(INSTANCE_NAME) --ddl-file=$(APP_DIR)/schemas/tables.sql

.PHONY: delete.database
delete.database:
	@echo "==== Delete instances of Cloud Spanner ===="
	@yes | gcloud spanner instances delete $(INSTANCE_NAME)

.PHONY: build.apps
build.apps:
	@echo "==== Build app and push image to Google Artifactregistry ===="
	@yes | gcloud auth configure-docker $(REGION)-docker.pkg.dev
	@cd $(APP_DIR) && docker build -t $(REPOGITORY)/$(SERVICE_NAME):$(COMMIT_SHA) --no-cache .
	@docker push $(REPOGITORY)/$(SERVICE_NAME):$(COMMIT_SHA)
	@yes | docker system prune

.PHONY: deploy.apps
deploy.apps:
	@echo "==== Deploy app to Cloud Run ===="
	@gcloud run deploy $(SERVICE_NAME) --image $(REPOGITORY)/$(SERVICE_NAME):$(COMMIT_SHA) --region $(REGION) --port 8000 --concurrency 1000 --allow-unauthenticated --min-instances=100 --max-instances=1000 --timeout=10 --service-account=$(SERVICE_ACCOUNT) \
	--cpu=2 --memory=4G --set-env-vars=GOOGLE_CLOUD_PROJECT=$(GOOGLE_CLOUD_PROJECT),INSTANCE_NAME=$(INSTANCE_NAME),DATABASE_NAME=$(DATABASE_NAME),ENV=$(ENV),LOG_LEVEL=$(LOG_LEVEL),JSON_LOGS=$(JSON_LOGS),GUNICORN_WORKERS=$(GUNICORN_WORKERS)

.PHONY: delete.apps
delete.apps:
	@echo "==== Delete app on Cloud Run ===="
	@yes | gcloud run services delete $(SERVICE_NAME) --region $(REGION)

.PHONY: load.data
load.data:
	@echo "==== Load master data to Cloud Spanner  ===="
	@echo "==== Caution: a few minitues needs to load data ===="
	@echo "==== build a script image ===="
	@cd $(APP_DIR)/scripts && docker build -t masterdata-generatoer:0.1 .
	@echo "==== run a script on docker to create masters ===="
	@docker run --rm masterdata-generatoer:0.1 python main.py -t $(APP_URL) -p 443
	@echo "==== remove a script image in local ===="
	@docker rmi -f masterdata-generatoer:0.1

.PHONY: build.locust
build.locust:
	@echo "==== Build locust and push image to Google Artifactregistry ===="
	@yes | gcloud auth configure-docker $(REGION)-docker.pkg.dev
	@cd $(CURRENT_DIR)locust && docker build -t $(REPOGITORY)/locust:$(COMMIT_SHA) .
	@docker push $(REPOGITORY)/locust:$(COMMIT_SHA)
	@yes | docker system prune

.PHONY: deploy.locust
deploy.locust:
	@POD_NUM=$(POD_NUM) TARGET=$(APP_URL) USERS=$(USERS) RUN_TIME=$(RUN_TIME) LOG_LEVEL=$(LOG_LEVEL) IMAGE_URL=$(REPOGITORY)/locust IMAGE_TAG=$(COMMIT_SHA) INSTANCE_IP=$(INSTANCE_IP) PG_PASSWORD=$(PG_PASSWORD) REDIS_HOST=$(REDIS_IP) \
	envsubst < $(CURRENT_DIR)/locust/deployments.tmpl.yml | kubectl apply -f - 

.PHONY: delete.locust
delete.locust:
	@echo "==== Delete locust from GKE cluster ===="
	@kubectl delete deployment locust-standalone

.PHONY: open.grafana
open.grafana:
	@if [ -n "${WEB_HOST}" ]; then echo "Grafana dashboard: https://3443-${WEB_HOST}"; fi
	@gcloud compute ssh --zone $(BASTION_ZONE) $(BASTION_NAME) -- -N -L 3443:localhost:3000

.PHONY: ssh.bastion
ssh.bastion:
	@gcloud compute ssh --zone $(BASTION_ZONE) $(BASTION_NAME)

.PHONY: terraform.init
terraform.init:
	@cd $(CURRENT_DIR)/terraform && terraform init

.PHONY: terraform.plan
terraform.plan:
	@cd $(CURRENT_DIR)/terraform && terraform plan  -var 'project_id=$(GOOGLE_CLOUD_PROJECT)' -var 'credential_file_path=$(KEY_PATH)' -var 'access_accounts=$(ACCOUNTS)' -auto-approve --parallelism=3

.PHONY: terraform.apply
terraform.apply:
	@echo "==== Create Infra by terraform ===="
	@cd $(CURRENT_DIR)/terraform && terraform apply \
		-var 'project_id=$(GOOGLE_CLOUD_PROJECT)' \
		-var 'credential_file_path=$(KEY_PATH)' \
		-var 'access_accounts=$(ACCOUNTS)' \
		-var 'region=$(REGION)' \
		-auto-approve --parallelism=3

.PHONY: terraform.destroy
terraform.destroy:
	@echo "==== Delete Infra via terraform ===="
	@cd $(CURRENT_DIR)/terraform && terraform destroy \
		-var 'project_id=$(GOOGLE_CLOUD_PROJECT)' \
		-var 'credential_file_path=$(KEY_PATH)' \
		-var 'access_accounts=$(ACCOUNTS)' \
		-var 'region=$(REGION)' \
		-auto-approve --parallelism=3

.PHONY: create.cloud.environment
create.cloud.environment:
	@echo "==== Start to create environment on Google Cloud ===="
	@make -i set.cloud.config
	@make -i terraform.init
	@make terraform.apply
	@make -i create.database
	@make -i build.apps
	@make -i deploy.apps
	@make -i load.data
	@make -i build.locust
	@make -i connect.cluster
	@echo "==== Finish to create environment on Google Cloud ===="

.PHONY: delete.cloud.environment
delete.cloud.environment:
	@echo "==== Start to delete them on Google Cloud ===="
	@make -i delete.locust
	@make -i delete.apps
	@make -i delete.database
	@make terraform.destroy
	@echo "==== Finish to delete them on Google Cloud ===="
