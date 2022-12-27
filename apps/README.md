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
export GOOGLE_CLOUD_PROJECT=$(LOCAL_DEV_CLOUD_PROJECT) INSTANCE_NAME=$(INSTANCE_NAME) DATABASE_NAME=$(DATABASE_NAME) ENV=local

# run api server
$ pipenv run server
```

## Run unit-tests

TBD

## Environment values

TBD

## Contribution

Please read [contributing.md](../docs/contributing.md).