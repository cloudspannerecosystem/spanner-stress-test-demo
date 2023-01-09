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
from pydantic import BaseModel, Field

from .utils import create_req_tag, get_db, get_uuid

TABLE: str = "Characters"
CHARACTER_LIMIT = 300

router = APIRouter(prefix="/characters", tags=["characters"])


class Character(BaseModel):
    user_id: str = Field(..., example="111111111")
    character_id: str = Field(..., example="111111111")
    name: str = Field(..., example="hoge")
    level: int = Field(..., example=10)
    experience: int = Field(..., example=10)
    strength: int = Field(..., example=10)


class CreateCharacterResponse(Character):
    id: str = Field(..., example="111111111")


class CharacterResponse(BaseModel):
    id: str = Field(..., example="111111111")
    user_name: str = Field(..., example="hoge")
    character_name: str = Field(..., example="foo")
    kind: str = Field(..., example="bar")
    nick_name: str = Field(..., example="huga")
    level: int = Field(..., example=10)
    experience: int = Field(..., example=10)
    strength: int = Field(..., example=10)


@router.get("/", tags=["characters"], response_model=List[CharacterResponse])
def get_rondom_characters(db: Database = Depends(get_db)) -> JSONResponse:
    """Get random 300 characters for checking test status"""
    with db.snapshot() as snapshot:
        query = f"""SELECT Id, Users.Name,CharacterMasters.Name, Kind, {TABLE}.Name, Level, Experience, Strength FROM {TABLE} TABLESAMPLE RESERVOIR (300 ROWS)
                  INNER JOIN Users ON Characters.UserId=Users.UserId
                  INNER JOIN CharacterMasters ON Characters.CharacterId=CharacterMasters.CharacterId"""
        results = list(snapshot.execute_sql(query))
    if not results:
        return JSONResponse(content={})
    return JSONResponse(content=jsonable_encoder([CharacterResponse(**dict(zip(CharacterResponse.__fields__.keys(), result))).dict() for result in results]))


@router.get("/{user_id}", tags=["characters"], response_model=List[CharacterResponse], responses={status.HTTP_404_NOT_FOUND: {"description": "Character does not found", "content": {"application/json": {"example": {"detail": "This user does not exsist or have any characters"}}}}})
def get_character(user_id: int, db: Database = Depends(get_db)) -> JSONResponse:
    """Get characters of the user"""
    with db.snapshot() as snapshot:
        query = f"""SELECT Id, Users.Name,CharacterMasters.Name, Kind, {TABLE}.Name, Level, Experience, Strength FROM {TABLE}
                  INNER JOIN Users ON Characters.UserId=Users.UserId
                  INNER JOIN CharacterMasters ON Characters.CharacterId=CharacterMasters.CharacterId WHERE {TABLE}.UserId=@UserId"""
        params, params_type = {"UserId": user_id}, {"UserId": spanner.param_types.INT64}
        request_options = {"request_tag": create_req_tag("select", "read_character", "characters")}
        results = list(snapshot.execute_sql(query, params=params, param_types=params_type, request_options=request_options))
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This user does not exsist or have any characters")
    return JSONResponse(content=jsonable_encoder([CharacterResponse(**dict(zip(CharacterResponse.__fields__.keys(), result))).dict() for result in results]))


@router.post("/", tags=["characters"], response_model=CreateCharacterResponse, status_code=status.HTTP_201_CREATED, responses={status.HTTP_403_FORBIDDEN: {"description": "Exceeded limits of character per user", "content": {"application/json": {"example": {"detail": "This user exceeded limits of chatacters"}}}}})
def create_characters(characters: Character, db: Database = Depends(get_db)) -> JSONResponse:
    """Create character such as getting a monster"""
    def create_character_repository(transaction):
        columns = ("Id", "UserId", "CharacterId", "Name", "Level", "Experience", "Strength", "CreatedAt", "UpdatedAt")
        values = (character_id, int(characters.user_id), int(characters.character_id), characters.name, characters.level, characters.experience, characters.experience)
        types = (spanner.param_types.INT64, spanner.param_types.INT64, spanner.param_types.INT64, spanner.param_types.STRING, spanner.param_types.INT64, spanner.param_types.INT64, spanner.param_types.INT64)

        insert_query = f"INSERT {TABLE} ({','.join(columns)}) VALUES ({','.join([ '@' + c if c not in ('CreatedAt', 'UpdatedAt') else 'PENDING_COMMIT_TIMESTAMP()' for c in columns])})"
        insert_params = {columns[i]: values[i] for i in range(len(values))}
        insert_params_type = {columns[i]: types[i] for i in range(len(values))}
        request_options = {"request_tag": create_req_tag("insert", "create_character", "characters")}

        transaction.execute_update(insert_query, params=insert_params, param_types=insert_params_type, request_options=request_options)

    with db.snapshot() as snapshot:
        query = f"SELECT COUNT(*) FROM {TABLE} WHERE UserId=@UserId"
        params, params_type = {"UserId": characters.user_id}, {"UserId": spanner.param_types.INT64}
        request_options = {"request_tag": create_req_tag("select", "read_characters_per_user", "characters")}
        cnt: int = list(snapshot.execute_sql(query, params=params, param_types=params_type, request_options=request_options))[0][0]
    # NOTE: avoid to get characters more over CHARACTER_LIMIT, because it become difficult to handle a lot of characters in this game
    if cnt >= CHARACTER_LIMIT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This user exceeded limits of chatacters")

    character_id = get_uuid()

    db.run_in_transaction(create_character_repository)

    resp = CreateCharacterResponse(id=character_id, user_id=characters.user_id, character_id=characters.character_id, name=characters.name, level=characters.level, experience=characters.experience, strength=characters.strength)
    return JSONResponse(status_code=201, content=jsonable_encoder(resp))


@router.delete("/", tags=["characters"], response_model=Optional[dict])
def delete_all_characters(db: Database = Depends(get_db)) -> JSONResponse:
    """Delete all characters"""
    db.execute_partitioned_dml(f"DELETE FROM {TABLE} WHERE Id > 0")
    return JSONResponse(content=jsonable_encoder({}))
