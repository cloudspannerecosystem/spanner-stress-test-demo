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


from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from google.cloud import spanner
from google.cloud.spanner_v1.database import Database
from pydantic import BaseModel

from .utils import create_req_tag, get_db, get_uuid

TABLE: str = "CharacterMasters"

router = APIRouter(
    prefix="/character_master",
    tags=["character_master"],
)


class CharacterMaster(BaseModel):
    name: str
    kind: str


class CharacterMasterRespose(BaseModel):
    character_master_id: str
    name: str
    kind: str


@router.get("/", tags=["character_master"])
def read_random_character_master(db: Database = Depends(get_db)) -> JSONResponse:
    """
    Get a random character masters for test
    """
    with db.snapshot(exact_staleness=timedelta(seconds=15)) as snapshot:
        query = f"SELECT CharacterId, Name, Kind From {TABLE} TABLESAMPLE RESERVOIR (1 ROWS)"
        results = list(snapshot.execute_sql(query))
    if not results:
        raise HTTPException(
            status_code=503, detail="Any character masters does not found")
    return JSONResponse(content=jsonable_encoder(CharacterMasterRespose(character_master_id=results[0][0], name=results[0][1], kind=results[0][2])))


@router.get("/{character_id}", tags=["character_master"])
def read_character_master(character_id: int, db: Database = Depends(get_db)) -> JSONResponse:
    """
    Get a character master
    """
    with db.snapshot() as snapshot:
        results = list(snapshot.execute_sql(f"SELECT CharacterId, Name, Kind From {TABLE} WHERE CharacterId={character_id}", request_options={
                       "request_tag": create_req_tag("select", "read_character_master", "character_master")}))
    if not results:
        return JSONResponse(content=jsonable_encoder({}))
    return JSONResponse(content=jsonable_encoder(CharacterMasterRespose(character_master_id=results[0][0], name=results[0][1], kind=results[0][2])))


@router.post("/", tags=["character_master"])
def create_character_master(character_master: CharacterMaster, db: Database = Depends(get_db)) -> JSONResponse:
    """
    Create a character master
    """
    with db.batch() as batch:
        batch.insert(
            table=TABLE,
            columns=("CharacterId", "Name", "Kind", "CreatedAt", "UpdatedAt"),
            values=[(get_uuid(), character_master.name, character_master.kind,
                     spanner.COMMIT_TIMESTAMP, spanner.COMMIT_TIMESTAMP)]
        )
    return JSONResponse(status_code=201, content=jsonable_encoder(character_master))


@router.delete("/", tags=["character_master"])
def delete_character_masters(db: Database = Depends(get_db)) -> JSONResponse:
    db.execute_partitioned_dml(f"DELETE FROM {TABLE} WHERE CharacterId > 0")
    return JSONResponse(content=jsonable_encoder({}))
