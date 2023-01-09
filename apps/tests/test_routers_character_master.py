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

from time import sleep
from typing import List

from fastapi import status
from fastapi.testclient import TestClient
from main import app
from pytest import fixture
from routers.character_master import CharacterMaster, CharacterMasterRespose
from routers.utils import character_master_delay

API_PATH = "/api/v1/character_master/"

client = TestClient(app)


def create_test_character_masters(num: int) -> List[CharacterMasterRespose]:
    test_character_masters = [CharacterMaster(name=f"test_{i}", kind="test") for i in range(num)]
    responses = []
    for test_character_master in test_character_masters:
        res = client.post(API_PATH, data=test_character_master.json(), headers={"Content-Type": "application/json", "User-Agent": "unit-test-agent"})
        if res.status_code != status.HTTP_201_CREATED:
            raise Exception("Failed to create a character master")
        responses.append(CharacterMasterRespose(**res.json()))
    return responses


def delete_all_character_masters() -> None:
    client.delete(API_PATH)


class TestCharacterMaster:

    @fixture(scope="function", autouse=True)
    def setup_and_teardown(self):
        # NOTE: setup
        self.test_users = create_test_character_masters(10)
        # NOTE: run test function
        yield
        # NOTE: tear down
        delete_all_character_masters()

    def test_get_random_character_master(self):
        # NOTE: wait for stale read
        sleep(float(character_master_delay) + 0.1)

        for _ in range(5):
            res = client.get(API_PATH)

            assert res.status_code == status.HTTP_200_OK
            assert res.json() in self.test_users

    def test_get_character_master(self):
        dummy_id = "111"
        test_user_ids = [self.test_users[0].character_master_id, dummy_id]
        # NOTE: wait for stale read
        sleep(float(character_master_delay) + 0.1)

        for i, _id in enumerate(test_user_ids):
            res = client.get(API_PATH + _id)

            if i == 0:
                assert res.status_code == status.HTTP_200_OK
                assert res.json() == self.test_users[0]
            else:
                assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_create_character_master(self):
        created_users = [{"name": "hoge", "kind": "fuga"}, {"test": "hoge"}]

        for i, user in enumerate(created_users):
            res = client.post(API_PATH, json=user, headers={"Content-Type": "application/json", "User-Agent": "unit-test-agent"})

            if i == 0:
                assert res.status_code == status.HTTP_201_CREATED
                assert (res.json()["name"], res.json()["kind"]) == (user["name"], user["kind"])
            else:
                assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_character_master(self):
        res = client.delete(API_PATH)

        assert res.status_code == status.HTTP_200_OK
