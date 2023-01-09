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

import logging
from os import getenv
from random import choice, randint
from sys import stdout
from time import time
from typing import Dict, Tuple

# NOTE: need to import to use plugins vis CLI
import locust_plugins  # noqa: F401
from faker import Faker
from google.cloud.logging.handlers import ContainerEngineHandler
from pydantic import BaseModel, EmailStr, Field
from redis import ConnectionPool, StrictRedis

from locust import HttpUser, task

ENV = getenv("ENV", "local")
LOG_LEVEL = getenv("LOG_LEVEL", "INFO")
REDIS_HOST = getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(getenv("REDIS_PORT", "6379"))
REDIS_CONNECTIONS = int(getenv("REDIS_CONNECTIONS", "3"))


logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName(LOG_LEVEL))
# NOTE: logging settings
if ENV == "production":
    logger.addHandler(ContainerEngineHandler(name=__name__, stream=stdout))
    logger.propagate = False

fake = Faker('jp-JP')


class User(BaseModel):
    name: str
    mail: EmailStr
    password: str = Field(min_length=8, max_length=16)


class Battles(BaseModel):
    character_id: str


class Character(BaseModel):
    user_id: str
    character_id: str
    name: str
    level: int
    experience: int
    strength: int


class UpdateCharacters(BaseModel):
    id: int
    level: int
    experience: int


def gen_url_and_report_name(url_tmpl: str, args: Dict[str, str]) -> Tuple[str, str]:
    return url_tmpl.format(**args), url_tmpl.format(**{k: v if k == "api_version" else f"${k}" for k, v in args.items()})


class StressScenario(HttpUser):
    def on_start(self):
        self.version = "v1"
        self.headers: Dict[str, str] = {"Content-Type": "application/json", "User-Agent": fake.chrome()}
        # TODO: tuning connection pool settings in test
        pool = ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=0, max_connections=REDIS_CONNECTIONS)
        self.redis: StrictRedis = StrictRedis(connection_pool=pool)

    @task(1)
    def create_fake_user(self):
        """create game user"""
        logger.debug("start create_fake_user")
        fake_user: User = User(name=fake.name(), mail=fake.email(), password=fake.password(length=randint(8, 16)))
        res = self.client.post(f"/api/{self.version}/users/", headers=self.headers, data=fake_user.json()).json()
        self.redis.set(res["user_id"], res["name"])
        logger.debug(f"user: {res}")
        logger.debug("end create_fake_user")

    @task(3)
    def create_character(self):
        """a random user to get a random character"""
        logger.debug("start create_character")
        user_id = self.redis.randomkey().decode()
        character = self.client.get(f"/api/{self.version}/character_master/", headers=self.headers).json()
        logger.debug(f"character master: {character}")
        fake_character: Character = Character(
            user_id=user_id,
            character_id=character["character_master_id"],
            name=fake.first_kana_name(),
            level=randint(1, 100),
            experience=randint(1, pow(10, 5)),
            strength=randint(1, pow(10, 5))
        )
        res = self.client.post(f"/api/{self.version}/characters/", headers=self.headers, data=fake_character.json()).json()
        logger.debug(f"result: {res}")
        logger.debug("end create_character")

    @task(10)
    def battle_opponent(self):
        """a random user to battle a random opponent"""
        logger.debug("start battle_opponent")
        user_id = self.redis.randomkey().decode()
        url, report_name = gen_url_and_report_name("/api/{api_version}/characters/{user_id}", {"api_version": self.version, "user_id": user_id})
        characters = list(self.client.get(url, name=report_name, headers=self.headers).json())
        if "detail" in characters:
            logger.debug("re-get character for battle")
            character = self.client.get(f"/api/{self.version}/character_master/", headers=self.headers).json()
            fake_character: Character = Character(
                user_id=user_id,
                character_id=character["character_master_id"],
                name=fake.first_kana_name(),
                level=randint(1, 100),
                experience=randint(1, pow(10, 5)),
                strength=randint(1, pow(10, 5))
            )
            characters = list(self.client.post(f"/api/{self.version}/characters/", headers=self.headers, data=fake_character.json()).json())
        logger.debug(f"characters length: {len(characters)}")
        character = choice(characters)
        logger.debug(f"character: {character}")
        if not isinstance(type(character), dict):
            return
        battle = Battles(character_id=character["id"])
        res = self.client.post(f"/api/{self.version}/battles/", headers=self.headers, data=battle.json()).json()
        logger.debug(f"result: {res}")
        logger.debug("end battle_opponent")

    @task(5)
    def get_histories(self):
        """get a battle history between random range"""
        logger.debug("start get_histories")
        user_id = self.redis.randomkey().decode()
        until = int(time())
        since = until - randint(60, 1800)
        logger.debug(f"user: {user_id}, since: {since}, until: {until}")
        url_tmpl = "/api/{api_version}/battles/history?user_id={user_id}&since={since}&until={until}"
        url, report_name = gen_url_and_report_name(url_tmpl, {"api_version": self.version, "user_id": user_id, "since": since, "until": until})
        res = self.client.get(url, name=report_name, headers=self.headers).json()
        logger.debug(f"result: {res}")
        logger.debug("end get_histories")
