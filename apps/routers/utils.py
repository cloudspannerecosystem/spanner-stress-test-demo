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

from datetime import datetime
from os import environ, getenv
from time import time_ns
from typing import Any, Dict, Tuple
from uuid import uuid4

from google.cloud.spanner import Client, PingingPool, TransactionPingingPool
from google.cloud.spanner_v1.database import Database
from passlib.context import CryptContext

context = CryptContext(schemes=["bcrypt"], deprecated="auto")
num_shards = 100

# NOTE: Spanner Settings
PROJECT: str = getenv("GOOGLE_CLOUD_PROJECT", "test-local")
INSTANCE: str = getenv("INSTANCE_NAME", "spanner-demo")
DATABASE: str = getenv("DATABASE_NAME", "sample-game")

client = Client(project=PROJECT)
instance = client.instance(INSTANCE)
pool = PingingPool(size=30, default_timeout=5, ping_interval=300)
database = instance.database(DATABASE, pool=pool)

# NOTE: stale read settings
character_master_delay: int = 3
opponent_master_delay: int = 3

# NOTE: set host path to spanner own emulator in local env
if getenv("ENV", "local") == "local":
    environ["SPANNER_EMULATOR_HOST"] = "localhost:9010"


def get_db() -> Database:
    pool.ping()
    return database


def get_password_hash(password):
    return context.hash(password)


def get_uuid() -> int:
    return uuid4().int & (1 << 63) - 1


def get_entry_shard_id(user_id: int) -> int:

    now: int = time_ns() // 1000
    return (user_id + now + get_uuid()) % num_shards


def epoch_to_datetime(epoch: int) -> str:
    # TODO: consider how to handle timestamp
    return datetime.fromtimestamp(epoch).isoformat() + "Z"


def build_insert_query(transaction: Any, table: str, columns: Tuple[str], values: Tuple[int, str], request_options: Dict[str, str]) -> None:
    # TODO: change to build sql smarter then now
    str_columns: str = str(columns).replace("'", "")
    str_values: str = str(values).replace("'PENDING_COMMIT_TIMESTAMP()'", "PENDING_COMMIT_TIMESTAMP()")
    query = f"INSERT {table} {str_columns} VALUES {str_values}"
    transaction.execute_update(query, request_options=request_options)


def create_req_tag(action: str, service: str, target: str) -> str:
    return f"action={action},service={service},target={target}"
