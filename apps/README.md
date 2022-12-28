# Sample game api server

This directory is sample game api for stress testing.

## Features

Provided some RestAPI of a sample game. You can check the API docs by [Automatic docs feature](https://fastapi.tiangolo.com/features/#automatic-docs).


### Structures

Basically, we follow [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/), but some of them are optimized for this app.

```bash
├── dbdoc: schema docs file by tbls
├── Dockerfile
├── __init__.py
├── main.py
├── Pipfile
├── Pipfile.lock
├── README.md
├── routers
│   ├── battles.py
│   ├── character_master.py
│   ├── characters.py
│   ├── __init__.py
│   ├── opponent_master.py
│   ├── users.py
│   └── utils.py
├── schemas
│   └── tables.sql
├── scripts
│   ├── Dockerfile
│   ├── main.py
│   ├── README.md
│   └── requirements.txt
└── settings.py
```

### Database Schema

Please read [database schema docs](./dbdoc/README.md) by tlbs

## Requirements

If you need to develop this repository, you should install followings according to instructions of hyperlink destination:

- [python](https://www.python.org/downloads/) (auther version: 3.9.2)
  - [pip](https://pip.pypa.io/en/stable/installation/) (auther version: 22.2)
  - [pipenv](https://pipenv.pypa.io/en/latest/) (auther version: 2022.7.24)
- [docker](https://docs.docker.com/engine/install/) (auther version: 20.10.17, API version: 1.41)
- [docker-compose](https://docs.docker.jp/compose/install/index.html) (auther version: version 1.24.0)

### Recommend pyenv

I recommend to use [pyenv](https://github.com/pyenv/pyenv) to create python develop environment, because it is easy to switch python version. Of course, [anyenv](https://github.com/anyenv/anyenv) is useful wrapper tool for **env, and so you should it if you plan to develop many kinds of languages.

## How to run

### Run apps by all docker-containers

You can set up some commends and access the swagger-ui for this service api docs:

```bash
$ git clone https://github.com/kazu0716/spanner-stress-test-demo.git
$ cd spanner-stress-test-demo

# create gcloud config to run cloud-spanner emulator in local in first time
$ make create.emulator.config

# change config for local development
$ make set.emulator.config

# run cloud-spanner emulator and app containers in local
$ make run.local-app

# check if containers work or not
# after above, access http://127.0.0.1:8000/docs or http://127.0.0.1:8000/redoc by your browser
$ docker-compose ps
               Name                             Command               State                                         Ports                                       
----------------------------------------------------------------------------------------------------------------------------------------------------------------
spanner-stress-test-demo_app_1       /bin/sh -c python /user/sr ...   Up      0.0.0.0:8000->8000/tcp,:::8000->8000/tcp                                          
spanner-stress-test-demo_spanner_1   ./gateway_main --hostname  ...   Up      0.0.0.0:9010->9010/tcp,:::9010->9010/tcp, 0.0.0.0:9020->9020/tcp,:::9020->9020/tcp

# stop containers
$ docker-compose down
```

### Run api-server in local environment for development

When you would like to develop API, you may want to run them in local. Then, you should follow this instructions:

```bash
$ git clone https://github.com/kazu0716/spanner-stress-test-demo.git
$ cd spanner-stress-test-demo

# create gcloud config to run cloud-spanner emulator in local in first time
$ make create.emulator.config

# change config for local development
$ make set.emulator.config

# run spanner-container
$ docker-compose up -d spanner

# create database settings for emulator
$ make create.emulator.database

# need to install python and pipenv, before doing followings:
$ cd ./apps
$ pipenv --python 3.9.14
$ pipenv install --dev
# enable virtualenv
$ pipenv shell

# export ../.env file values in your env
export GOOGLE_CLOUD_PROJECT=$(LOCAL_DEV_CLOUD_PROJECT) INSTANCE_NAME=$(INSTANCE_NAME) DATABASE_NAME=$(DATABASE_NAME) ENV=local SPANNER_EMULATOR_HOST=localhost:9010

# run api server
$ pipenv run server
```

## Run unit-tests

*Note: If you don't finish Run API server in local part, this part do after that*

When you run unit-tests in local, you do as followings:

```bash
# need to install python and pipenv, before doing followings:
$ cd ./apps
# enable virtualenv
$ pipenv shell

$ python -m pytest --no-header -vv -s
========================================== test session starts ===========================================
collected 19 items                                                                                       

tests/test_routers_battles.py::TestBattles::test_get_battle_histories PASSED
tests/test_routers_battles.py::TestBattles::test_battle PASSED
tests/test_routers_battles.py::TestBattles::test_delete_user PASSED
tests/test_routers_character_master.py::TestCharacterMaster::test_get_random_character_master PASSED
tests/test_routers_character_master.py::TestCharacterMaster::test_get_character_master PASSED
tests/test_routers_character_master.py::TestCharacterMaster::test_create_character_master PASSED
tests/test_routers_character_master.py::TestCharacterMaster::test_delete_character_master PASSED
tests/test_routers_characters.py::TestCharacters::test_get_random_characters PASSED
tests/test_routers_characters.py::TestCharacters::test_get_character PASSED
tests/test_routers_characters.py::TestCharacters::test_create_characters PASSED
tests/test_routers_characters.py::TestCharacters::test_delete_user PASSED
tests/test_routers_opponent_master.py::TestOpponentMaster::test_get_random_opponent_master PASSED
tests/test_routers_opponent_master.py::TestOpponentMaster::test_get_opponent_master PASSED
tests/test_routers_opponent_master.py::TestOpponentMaster::test_create_opponent_master PASSED
tests/test_routers_opponent_master.py::TestOpponentMaster::test_delete_opponent_master PASSED
tests/test_routers_users.py::TestUsers::test_get_users PASSED
tests/test_routers_users.py::TestUsers::test_get_user PASSED
tests/test_routers_users.py::TestUsers::test_create_user PASSED
tests/test_routers_users.py::TestUsers::test_delete_user PASSED

========================================== 19 passed in 52.05s ===========================================
```

## Environment values

|                      |                                                                                                                                    |                                                                                                                          | 
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | 
| Key name             | Description                                                                                                                        | Example value                                                                                                            | 
| GOOGLE_CLOUD_PROJECT | Google Cloud Project ID                                                                                                            | test                                                                                                                     | 
| INSTANCE_NAME        | Cloud Spanner's instance name                                                                                                      | spanner-demo                                                                                                             | 
| DATABASE_NAME        | Cloud Spanner's database name for testing                                                                                          | sample-game                                                                                                              | 
| ENV                  | Env id, but we expected to use "production" when you deploy on Google Cloud.                                                       | production                                                                                                               | 
| LOG_LEVEL            | Loglevel of app and Locust                                                                                                         | INFO                                                                                                                     |                                                                                                                  | 
| SPANNER_EMULATOR_HOST            | Settings to connect spanner emulator                                                                                                         | localhost:9010                                                                                                                     |                                                                                                                  | 
## Contribution

Please read [contributing.md](../docs/contributing.md).