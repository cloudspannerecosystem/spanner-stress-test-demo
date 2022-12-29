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
from typing import List

from fastapi import status
from fastapi.testclient import TestClient
from main import app
from pytest import fixture
from routers.character_master import CharacterMasterRespose
from routers.characters import Character, CreateCharacterResponse
from routers.users import UserResponse
from tests.test_routers_character_master import (create_test_character_masters,
                                                 delete_all_character_masters)
from tests.test_routers_users import create_test_users, delete_all_users

API_PATH = "/api/v1/characters/"

client = TestClient(app)


def create_test_characters(num: int, user: UserResponse, character_masters: List[CharacterMasterRespose]) -> List[CreateCharacterResponse]:
    test_users = [Character(user_id=user.user_id, character_id=choice(character_masters).character_master_id,
                            name=f"test_{i}", level=10, experience=10, strength=10) for i in range(num)]
    responses = []
    for test_user in test_users:
        res = client.post(API_PATH, data=test_user.json(), headers={"Content-Type": "application/json", "User-Agent": "unit-test-agent"})
        if res.status_code != status.HTTP_201_CREATED:
            raise Exception("Failed to create a character")
        responses.append(CreateCharacterResponse(**res.json()))
    return responses


def delete_all_characters() -> None:
    client.delete(API_PATH)


class TestCharacters:
    @fixture(scope="class", autouse=True)
    def delete_test_data(self):
        yield
        # NOTE: tear down per class
        delete_all_character_masters()
        delete_all_users()

    @fixture(scope="class", autouse=True)
    def get_users(self) -> List[UserResponse]:
        return create_test_users(2)

    @fixture(scope="class", autouse=True)
    def get_character_masters(self) -> List[CharacterMasterRespose]:
        return create_test_character_masters(5)

    @fixture(scope="function", autouse=True)
    def setup_and_teardown(self, get_users, get_character_masters):
        # NOTE: setup
        self.test_user: UserResponse = get_users[0]
        self.non_character_user: UserResponse = get_users[1]
        self.test_character_masters: List[CharacterMasterRespose] = get_character_masters
        self.test_characters: List[CreateCharacterResponse] = create_test_characters(10, self.test_user, self.test_character_masters)
        # NOTE: run test function
        yield
        # NOTE: tear down
        delete_all_characters()

    def test_get_random_characters(self):
        res = client.get(API_PATH)

        expected = sorted([(c.name, c.level, c.experience, c.strength) for c in self.test_characters])
        results = sorted([(r["nick_name"], r["level"], r["experience"], r["strength"]) for r in res.json()])

        assert res.status_code == status.HTTP_200_OK
        assert results == expected

    def test_get_character(self):
        dummy_id = "111"
        test_user_ids = [self.test_user.user_id, self.non_character_user.user_id, dummy_id]

        for i, _id in enumerate(test_user_ids):
            res = client.get(API_PATH + _id)

            if i == 0:
                expected = sorted([(c.name, c.level, c.experience, c.strength) for c in self.test_characters])
                results = sorted([(r["nick_name"], r["level"], r["experience"], r["strength"]) for r in res.json()])

                assert res.status_code == status.HTTP_200_OK
                assert results == expected
            else:

                assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_create_characters(self):
        created_users = [{"user_id": self.test_user.user_id, "character_id": self.test_character_masters[0].character_master_id, "name": "hoge", "level": 10, "experience": 10, "strength": 10}, {"test": "hoge"}]

        for i, user in enumerate(created_users):
            res = client.post(API_PATH, json=user, headers={"Content-Type": "application/json", "User-Agent": "unit-test-agent"})

            if i == 0:
                assert res.status_code == status.HTTP_201_CREATED
                result = res.json()
                del result["id"]
                assert result == user
            else:
                assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_user(self):
        res = client.delete(API_PATH)

        assert res.status_code == status.HTTP_200_OK
