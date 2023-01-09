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

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from google.cloud import spanner
from google.cloud.spanner_v1.database import Database
from pydantic import BaseModel, EmailStr, Field, SecretStr

from .utils import create_req_tag, get_db, get_password_hash, get_uuid

TABLE: str = "Users"

router = APIRouter(prefix="/users", tags=["users"])


class User(BaseModel):
    name: str = Field(..., example="hoge")
    mail: EmailStr = Field(..., example="hoge@example.com")
    password: SecretStr = Field(min_length=8, max_length=16, example="hogehoge")


class UserResponse(BaseModel):
    user_id: str = Field(..., example="111111111")
    name: str = Field(..., example="hoge")
    mail: EmailStr = Field(..., example="hoge@example.com")


@router.get("/", tags=["users"], response_model=List[UserResponse])
def get_random_users(db: Database = Depends(get_db)) -> JSONResponse:
    """Get 1,000 random users for tests initial requests"""
    with db.snapshot() as snapshot:
        query = f"SELECT UserId, Name, Mail From {TABLE} TABLESAMPLE RESERVOIR (1000 ROWS)"
        results = list(snapshot.execute_sql(query))
    return JSONResponse(content=jsonable_encoder([UserResponse(**dict(zip(UserResponse.__fields__.keys(), result))).dict() for result in results]))


@router.get("/{user_id}", tags=["users"], response_model=UserResponse, responses={status.HTTP_404_NOT_FOUND: {"description": "User does not found", "content": {"application/json": {"example": {"detail": "This user does not found"}}}}})
def get_user(user_id: str, db: Database = Depends(get_db)) -> JSONResponse:
    """Get a user"""
    with db.snapshot() as snapshot:
        query = f"SELECT UserId, Name, Mail From {TABLE} WHERE UserId=@UserId"
        params, params_type = {"UserId": user_id}, {"UserId": spanner.param_types.INT64}
        request_options = {"request_tag": create_req_tag("select", "read_user", "users")}
        results = list(snapshot.execute_sql(query, params=params, param_types=params_type, request_options=request_options))

    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This character did not found")

    return JSONResponse(content=jsonable_encoder(UserResponse(user_id=results[0][0], name=results[0][1], mail=results[0][2])))


@router.post("/", tags=["users"], response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: User, db: Database = Depends(get_db)) -> JSONResponse:
    """Create a user"""
    def create_user_repository(transaction):
        query = f"INSERT {TABLE} ( UserId, Name, Mail, Password, CreatedAt, UpdatedAt ) VALUES ( @UserId, @Name, @Mail, @Password, PENDING_COMMIT_TIMESTAMP(), PENDING_COMMIT_TIMESTAMP() )"
        params = {"UserId": user_id, "Name": user.name, "Mail": user.mail, "Password": hashed_password}
        params_type = {"UserId": spanner.param_types.INT64, "Name": spanner.param_types.STRING, "Password": spanner.param_types.STRING}
        request_options = {"request_tag": create_req_tag("insert", "create_user", "users")}
        transaction.execute_update(query, params=params, param_types=params_type, request_options=request_options)

    user_id = get_uuid()
    hashed_password = get_password_hash(user.password.get_secret_value())

    db.run_in_transaction(create_user_repository)

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=jsonable_encoder(UserResponse(user_id=user_id, name=user.name, mail=user.mail)))


@router.delete("/", tags=["users"], response_model=Optional[dict])
def delete_all_users(db: Database = Depends(get_db)) -> JSONResponse:
    """Delete all users"""
    db.execute_partitioned_dml(f"DELETE FROM {TABLE} WHERE UserId > 0")
    return JSONResponse(content=jsonable_encoder({}))
