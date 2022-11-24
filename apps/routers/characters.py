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


from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from google.cloud import spanner
from google.cloud.spanner_v1.database import Database
from pydantic import BaseModel

from .utils import build_insert_query, create_req_tag, get_db, get_uuid

TABLE: str = "Characters"
CHARACTER_LIMIT = 300

router = APIRouter(
    prefix="/characters",
    tags=["characters"],
)


class Character(BaseModel):
    user_id: str
    character_id: str
    name: str
    level: int
    experience: int
    strength: int


class CharacterResponse(BaseModel):
    id: str
    user_name: str
    character_name: str
    kind: str
    nick_name: str
    level: int
    experience: int
    strength: int


@router.get("/", tags=["characters"])
def read_rondom_characters(db: Database = Depends(get_db)) -> JSONResponse:
    """
    Get random 300 characters for checking test status
    """
    with db.snapshot() as snapshot:
        query = f"""SELECT Id, Users.Name,CharacterMasters.Name, Kind, {TABLE}.Name, Level, Experience, Strength FROM {TABLE} TABLESAMPLE RESERVOIR (300 ROWS)
                  INNER JOIN Users ON Characters.UserId=Users.UserId
                  INNER JOIN CharacterMasters ON Characters.CharacterId=CharacterMasters.CharacterId"""
        results = list(snapshot.execute_sql(query))
    return JSONResponse(content=jsonable_encoder([CharacterResponse(**dict(zip(CharacterResponse.__fields__.keys(), result))).dict() for result in results]))


@router.get("/{user_id}", tags=["characters"])
def read_character(user_id: int, db: Database = Depends(get_db)) -> JSONResponse:
    """
    Get characters of the user
    """
    with db.snapshot() as snapshot:
        query = f"""SELECT Id, Users.Name,CharacterMasters.Name, Kind, {TABLE}.Name, Level, Experience, Strength FROM {TABLE}
                  INNER JOIN Users ON Characters.UserId=Users.UserId
                  INNER JOIN CharacterMasters ON Characters.CharacterId=CharacterMasters.CharacterId WHERE {TABLE}.UserId={user_id}"""
        results = list(snapshot.execute_sql(query, request_options={"request_tag": create_req_tag("select", "read_character", "characters")}))
    if not results:
        raise HTTPException(status_code=404, detail="This user does not have any characters")
    return JSONResponse(content=jsonable_encoder([CharacterResponse(**dict(zip(CharacterResponse.__fields__.keys(), result))).dict() for result in results]))


@router.post("/", tags=["characters"])
def create_characters(characters: Character, db: Database = Depends(get_db)) -> JSONResponse:
    """
    Create character such as getting a monster 
    """
    with db.snapshot() as snapshot:
        cnt: int = list(snapshot.execute_sql(f"SELECT COUNT(*) FROM {TABLE} WHERE UserId={characters.user_id}",
                                             request_options={"request_tag": create_req_tag("select", "read_characters_per_user", "characters")}))[0][0]
    # NOTE: avoid to get characters more over CHARACTER_LIMIT, because it become difficult to handle a lot of characters in this game
    if cnt >= CHARACTER_LIMIT:
        return JSONResponse(content=jsonable_encoder({}))
    character_id = get_uuid()
    columns = ("Id", "UserId", "CharacterId", "Name", "Level", "Experience", "Strength", "CreatedAt", "UpdatedAt")
    # TODO: change following no needs needless cast
    # NOTE: cast xx_id str to int for creating SQL query, because pydantic's int has limited and so post data use str in id data
    values = (character_id, int(characters.user_id), int(characters.character_id), characters.name, characters.level,
              characters.experience, characters.experience, "PENDING_COMMIT_TIMESTAMP()", "PENDING_COMMIT_TIMESTAMP()")
    request_options = {"request_tag": create_req_tag("insert", "create_character", "characters")}
    db.run_in_transaction(build_insert_query, TABLE, columns, values, request_options)
    # TODO: change to use BaseModels
    res = dict(characters)
    res["id"] = character_id
    return JSONResponse(status_code=201, content=jsonable_encoder(res))
