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


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from google.cloud.spanner_v1.database import Database
from pydantic import BaseModel, EmailStr, Field, SecretStr

from .utils import (build_insert_query, create_req_tag, get_db,
                    get_password_hash, get_uuid)

TABLE: str = "Users"

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


class User(BaseModel):
    name: str
    mail: EmailStr
    password: SecretStr = Field(min_length=8, max_length=16)


class UserResponse(BaseModel):
    user_id: str
    name: str
    mail: EmailStr


@router.get("/", tags=["users"])
def read_random_users(db: Database = Depends(get_db)) -> JSONResponse:
    """
    Get 1,000 random users for tests initial requests
    """
    with db.snapshot() as snapshot:
        query = f"SELECT UserId, Name, Mail From {TABLE} TABLESAMPLE RESERVOIR (1000 ROWS)"
        results = list(snapshot.execute_sql(query))
    return JSONResponse(content=jsonable_encoder([UserResponse(**dict(zip(UserResponse.__fields__.keys(), result))).dict() for result in results]))


@router.get("/{user_id}", tags=["users"])
def read_user(user_id: str, db: Database = Depends(get_db)) -> JSONResponse:
    """
    Get a user
    """
    with db.snapshot() as snapshot:
        query = f"SELECT UserId, Name, Mail From {TABLE} WHERE UserId={user_id}"
        results = list(snapshot.execute_sql(query, request_options={"request_tag": create_req_tag("select", "read_user", "users")}))
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The character did not found")
    return JSONResponse(content=jsonable_encoder(UserResponse(user_id=results[0][0], name=results[0][1], mail=results[0][2])))


@router.post("/", tags=["users"])
def create_user(user: User, db: Database = Depends(get_db)) -> JSONResponse:
    """
    Create user
    """
    user_id = get_uuid()
    hashed_password = get_password_hash(user.password.get_secret_value())
    columns = ("UserId", "Name", "Mail", "Password", "CreatedAt", "UpdatedAt")
    values = (user_id, user.name, user.mail, hashed_password, "PENDING_COMMIT_TIMESTAMP()", "PENDING_COMMIT_TIMESTAMP()")
    request_options = {"request_tag": create_req_tag("insert", "create_user", "users")}
    db.run_in_transaction(build_insert_query, TABLE, columns, values, request_options)
    return JSONResponse(status_code=201, content=jsonable_encoder(UserResponse(user_id=user_id, name=user.name, mail=user.mail)))


@router.delete("/", tags=["users"])
def delete_all_users(db: Database = Depends(get_db)) -> JSONResponse:
    db.execute_partitioned_dml(f"DELETE FROM {TABLE} WHERE UserId > 0")
    return JSONResponse(content=jsonable_encoder({}))
