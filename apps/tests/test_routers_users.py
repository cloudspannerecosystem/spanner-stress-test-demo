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

from typing import List

from fastapi import status
from fastapi.testclient import TestClient
from main import app
from pytest import fixture
from routers.users import User, UserResponse

API_PATH = "/api/v1/users/"

client = TestClient(app)


def create_test_users(num: int) -> List[UserResponse]:
    test_users = [User(name=f"sample_{i}", mail=f"sample_{i}@example.com", password="hogehoge") for i in range(num)]
    responses = []
    for test_user in test_users:
        res = client.post(API_PATH, data=test_user.json(), headers={"Content-Type": "application/json", "User-Agent": "unit-test-agent"})
        if res.status_code != status.HTTP_201_CREATED:
            raise Exception("Failed to create a user")
        responses.append(UserResponse(**res.json()))
    return responses


def delete_all_users() -> None:
    client.delete(API_PATH)


class TestUsers:
    @fixture(scope="function", autouse=True)
    def setup_and_teardown(self):
        # NOTE: setup
        self.test_users = create_test_users(10)
        # NOTE: run test function
        yield
        # NOTE: tear down
        delete_all_users()

    def test_get_users(self):
        res = client.get(API_PATH)

        assert res.status_code == status.HTTP_200_OK
        for result, expected in zip(sorted([(r["name"], r["mail"], r["user_id"]) for r in res.json()]), self.test_users):
            assert result == (expected.name, expected.mail, expected.user_id)

    def test_get_user(self):
        dummy_id = "111"
        test_user_ids = [self.test_users[0].user_id, dummy_id]

        for i, _id in enumerate(test_user_ids):
            res = client.get(API_PATH + _id)

            if i == 0:
                assert res.status_code == status.HTTP_200_OK
                assert res.json() == self.test_users[0]
            else:
                assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_create_user(self):
        created_users = [{"name": "sample_100", "mail": "sample_100@example.com", "password": "hogehoge"}, {"test": "hoge"}]

        for i, user in enumerate(created_users):
            res = client.post(API_PATH, json=user, headers={"Content-Type": "application/json", "User-Agent": "unit-test-agent"})

            if i == 0:
                assert res.status_code == status.HTTP_201_CREATED
                assert (res.json()["name"], res.json()["mail"]) == (user["name"], user["mail"])
            else:
                assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_user(self):
        res = client.delete(API_PATH)

        assert res.status_code == status.HTTP_200_OK
