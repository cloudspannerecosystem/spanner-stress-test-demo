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

from random import choice
from time import sleep, time
from typing import List, Tuple

from fastapi import status
from fastapi.testclient import TestClient
from main import app
from pytest import fixture
from routers.battles import BattleResponse, Battles
from routers.characters import CreateCharacterResponse
from routers.opponent_master import OpponentMasterResponse
from routers.users import UserResponse
from routers.utils import battle_history_delay
from tests.test_routers_character_master import (create_test_character_masters,
                                                 delete_all_character_masters)
from tests.test_routers_characters import create_test_characters
from tests.test_routers_opponent_master import (create_test_opponent_masters,
                                                delete_all_opponent_masters)
from tests.test_routers_users import create_test_users, delete_all_users

API_PATH_BATTLE = "/api/v1/battles/"
API_PATH_BATTLE_HISTORIES = "/api/v1/battles/history"

test_data_num = 10

client = TestClient(app)


def create_test_battle_histories(characters: List[CreateCharacterResponse]) -> None:
    test_users = [Battles(character_id=choice(characters).id) for _ in range(test_data_num)]
    for test_user in test_users:
        res = client.post(API_PATH_BATTLE, data=test_user.json(), headers={"Content-Type": "application/json", "User-Agent": "unit-test-agent"})
        if res.status_code != status.HTTP_201_CREATED:
            raise Exception("Failed to create a battle history")
        BattleResponse(**res.json())


def delete_all_battle_histories() -> None:
    client.delete(API_PATH_BATTLE_HISTORIES)


class TestBattles:
    @fixture(scope="class", autouse=True)
    def delete_test_data(self):
        yield
        # NOTE: tear down per class
        delete_all_users()
        delete_all_character_masters()
        delete_all_opponent_masters()

    @fixture(scope="class", autouse=True)
    def get_test_data(self) -> Tuple[List[UserResponse], List[OpponentMasterResponse], List[CreateCharacterResponse]]:
        test_users = create_test_users(2)
        test_character_masters = create_test_character_masters(10)
        test_opponent_masters = create_test_opponent_masters(10)
        test_characters = create_test_characters(test_data_num, test_users[0], test_character_masters)
        return test_users, test_opponent_masters, test_characters

    @fixture(scope="function", autouse=True)
    def setup_and_teardown(self, get_test_data):
        # NOTE: setup
        self.test_users, self.test_opponent_masters, self.test_characters = get_test_data
        create_test_battle_histories(self.test_characters)
        # NOTE: run test function
        yield
        # NOTE: tear down
        delete_all_battle_histories()

    def test_get_battle_histories(self):
        current_epoch_time = int(time())
        query_strins = f"user_id={self.test_users[0].user_id}&since={current_epoch_time - 72000}&until={current_epoch_time + 72000}"

        cnt = 0
        res = client.get(f"{API_PATH_BATTLE_HISTORIES}?{query_strins}")
        # NOTE: Wait to get data, because this method use stale read
        sleep(float(battle_history_delay) + 0.5)
        while cnt < 10 and not res.json():
            res = client.get(f"{API_PATH_BATTLE_HISTORIES}?{query_strins}")
            sleep(1)

        assert res.status_code == status.HTTP_200_OK
        assert len(res.json()) == test_data_num

    def test_battle(self):
        created_users = [{"character_id": choice(self.test_characters).id}, {"hoge": "hoge"}, {"character_id": 10}]

        for i, user in enumerate(created_users):
            res = client.post(API_PATH_BATTLE, json=user, headers={"Content-Type": "application/json", "User-Agent": "unit-test-agent"})

            if i == 0:
                assert res.status_code == status.HTTP_201_CREATED
            elif i == 1:
                assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            elif i == 2:
                assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_user(self):
        res = client.delete(API_PATH_BATTLE_HISTORIES)

        assert res.status_code == status.HTTP_200_OK
