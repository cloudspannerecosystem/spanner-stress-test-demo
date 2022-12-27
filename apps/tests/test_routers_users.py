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

from typing import Dict, List

from fastapi import status
from fastapi.testclient import TestClient
from main import app
from pytest import fixture
from pytest_mock import MockFixture
from routers.users import User

API_PATH = "/api/v1/users/"

client = TestClient(app)


def create_test_users() -> List[User]:
    test_users = [User(name=f"sample_{i}", mail=f"sample_{i}@example.com", password="hogehoge") for i in range(10)]
    headers: Dict[str, str] = {"Content-Type": "application/json", "User-Agent": "unit-test-agent"}
    for test_user in test_users:
        res = client.post(API_PATH, data=test_user.json(), headers=headers)
        if res.status_code != status.HTTP_201_CREATED:
            raise Exception("Failed to create a user")
    return test_users


def delete_all_users() -> None:
    client.delete(API_PATH)


class TestUsers:
    @fixture(scope="function", autouse=True)
    def create_test_users(self):
        # NOTE: setup
        self.test_users = create_test_users()
        # NOTE: run test function
        yield
        # NOTE: tear down
        delete_all_users()

    def test_get_users(self):
        """Succeeded to get users"""
        res = client.get(API_PATH)

        assert res.status_code == status.HTTP_200_OK
        for result, expected in zip(sorted([(r["name"], r["mail"]) for r in res.json()]), self.test_users):
            assert result == (expected.name, expected.mail)
