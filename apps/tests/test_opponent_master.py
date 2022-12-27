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
from routers.opponent_master import OpponentMaster, OpponentMasterResponse
from routers.utils import opponent_master_delay

API_PATH = "/api/v1/opponent_master/"

client = TestClient(app)


def create_test_opponent_masters() -> List[OpponentMasterResponse]:
    responses = []
    for test_opponent_master in [OpponentMaster(name=f"test_{i}", kind="test", strength=10, experience=10) for i in range(10)]:
        res = client.post(API_PATH, data=test_opponent_master.json(), headers={"Content-Type": "application/json", "User-Agent": "unit-test-agent"})
        if res.status_code != status.HTTP_201_CREATED:
            raise Exception("Failed to create a character master")
        responses.append(OpponentMasterResponse(**res.json()))
    return responses


def delete_all_opponent_masters() -> None:
    client.delete(API_PATH)


class TestCharacterMaster:

    @fixture(scope="function", autouse=True)
    def create_test_users(self):
        # NOTE: setup
        self.test_users = create_test_opponent_masters()
        # NOTE: run test function
        yield
        # NOTE: tear down
        delete_all_opponent_masters()

    def test_get_random_opponent_master(self):
        # NOTE: wait for stale read
        sleep(float(opponent_master_delay) + 0.1)

        for _ in range(5):
            res = client.get(API_PATH)

            assert res.status_code == status.HTTP_200_OK
            assert res.json() in self.test_users

    def test_get_opponent_master(self):
        dummy_id = "111"
        test_user_ids = [self.test_users[0].opponent_id, dummy_id]
        # NOTE: wait for stale read
        sleep(float(opponent_master_delay) + 0.1)

        for i, _id in enumerate(test_user_ids):
            res = client.get(API_PATH + _id)

            if i == 0:
                assert res.status_code == status.HTTP_200_OK
                assert res.json() == self.test_users[0]
            else:
                assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_create_opponent_master(self):
        created_users = [{"name": "hoge", "kind": "fuga", "strength": 10, "experience": 10}, {"test": "hoge"}]

        for i, user in enumerate(created_users):
            res = client.post(API_PATH, json=user, headers={"Content-Type": "application/json", "User-Agent": "unit-test-agent"})

            if i == 0:
                assert res.status_code == status.HTTP_201_CREATED
                ret = res.json()
                assert (ret["name"], ret["kind"], ret["strength"], ret["experience"]) == (
                    user["name"], user["kind"], user["strength"], user["experience"])
            else:
                assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_opponent_master(self):
        res = client.delete(API_PATH)

        assert res.status_code == status.HTTP_200_OK
