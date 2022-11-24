# Distrubuted load testing senario by Locust

This directory have files to run distributes load test senario to [sample game](./../apps/README.md).

## Features

### Structures

There is only a simple [locust file](https://docs.locust.io/en/stable/writing-a-locustfile.html).

```bash
$ tree
.
├── deployments.tmpl.yml : k8s manifest template
├── Dockerfile
├── locustfile.py
├── Pipfile
├── Pipfile.lock
└── README.md
```

## How to run in local

After [runing apps in local](./../apps/README.md#how-to-run), do followings:

```bash
# run apps by containers
$ make run.local-app

# run locust with other containers
$ make run.local-locust

# check if containers run or not
$ docker-compose ps
               Name                              Command               State                                         Ports                                       
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
spanner-stress-test-demo_app_1        /bin/sh -c python /user/sr ...   Up      0.0.0.0:8000->8000/tcp,:::8000->8000/tcp                                          
spanner-stress-test-demo_grafana_1    /run.sh                          Up      0.0.0.0:3000->3000/tcp,:::3000->3000/tcp                                          
spanner-stress-test-demo_locust_1     /usr/local/bin/locust --he ...   Up                                                                                        
spanner-stress-test-demo_postgres_1   docker-entrypoint.sh postgres    Up      0.0.0.0:5432->5432/tcp,:::5432->5432/tcp                                          
spanner-stress-test-demo_redis_1      docker-entrypoint.sh redis ...   Up      0.0.0.0:6379->6379/tcp,:::6379->6379/tcp                                          
spanner-stress-test-demo_spanner_1    ./gateway_main --hostname  ...   Up      0.0.0.0:9010->9010/tcp,:::9010->9010/tcp, 0.0.0.0:9020->9020/tcp,:::9020->9020/tcp

# after that, access http://127.0.0.1:3000/ via your browser to check dashboard

# stop containers
$ docker-compose down
```

### Run locust in local environment for development

```bash
# run apps by containers
$ make run.local-app

# run containers for locust
$ docker-compose up -d redis postgres grafana

# need to install python and pipenv, before doing followings:
$ cd ./locust
$ pipenv --python 3.9.14
$ pipenv install --dev
# enable virtualenv
$ pipenv shell

# run locust
$ export LOCUST_HOST=http://localhost:8000 LOCUST_USERS=10 LOCUST_RUN_TIME=5m REDIS_HOST=localhost
$ locust --headless --timescale --grafana-url=http://localhost:3000 --pghost=localhost --pguser=postgres --pgpassword=password
```

## Environment values

TBD

## Contribution

Please read [contributing.md](../docs/contributing.md).