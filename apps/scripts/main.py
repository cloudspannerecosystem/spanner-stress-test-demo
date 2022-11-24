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

from argparse import ArgumentParser
from random import randint
from typing import Dict

import requests
from faker import Faker
from pydantic import BaseModel

fake = Faker('jp-JP')


class CharacterMaster(BaseModel):
    name: str
    kind: str


class OpponentMaster(BaseModel):
    name: str
    kind: str
    strength: int
    experience: int


def create_masters(args):
    # TODO: run faster than now, for example to use asyncio
    API_VERSION = args.version
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    host = args.target + ":" + args.port
    # NOTE: add character masters
    print("==== start to creare character masters ===")
    for _ in range(args.line):
        try:
            fake_character_master = CharacterMaster(name=fake.first_kana_name(), kind="fake")
            res = requests.post(url=f"{host}/api/{API_VERSION}/character_master/", headers=headers, data=fake_character_master.json())
            print(res.json())
        except Exception as e:
            print(e)
    # NOTE: add opponent masters
    print("==== start to creare opponent masters ===")
    for _ in range(args.line):
        try:
            fake_opponent_master = OpponentMaster(name=fake.first_kana_name(), kind="fake",
                                                  strength=randint(1, pow(10, 5)), experience=randint(1, pow(10, 5)))
            res = requests.post(url=f"{host}/api/{API_VERSION}/opponent_master/", headers=headers, data=fake_opponent_master.json())
            print(res.json())
        except Exception as e:
            print(e)
    print("==== finish to create masters ===")


if __name__ == "__main__":
    parser = ArgumentParser(description="importer master data for stress test")
    parser.add_argument('-t', '--target', default='http://localhost', type=str, help='target host')
    parser.add_argument('-p', '--port', default='8000', type=str, help='target port')
    parser.add_argument('-l', '--line', default=300, type=int, help='number of master data')
    parser.add_argument('-v', '--version', default="v1", type=str, help='target api version')
    create_masters(parser.parse_args())
