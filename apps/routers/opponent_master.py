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

TABLE: str = "OpponentMasters"

router = APIRouter(
    prefix="/opponent_master",
    tags=["opponent_master"],
)


class OpponentMaster(BaseModel):
    name: str
    kind: str
    strength: int
    experience: int


class OpponentMasterResponse(BaseModel):
    opponent_id: str
    name: str
    kind: str
    strength: int
    experience: int


@router.get("/", tags=["opponent_master"])
def read_random_opponent_master(db: Database = Depends(get_db)) -> JSONResponse:
    """
    Get a random opponent masters for test
    """
    with db.snapshot(exact_staleness=timedelta(seconds=15)) as snapshot:
        query = f"SELECT OpponentId, Name, Kind, Strength, Experience FROM {TABLE} TABLESAMPLE RESERVOIR (1 ROWS)"
        results = list(snapshot.execute_sql(query))
    if not results:
        raise HTTPException(
            status_code=503, detail="Any opponent masters does not found")
    return JSONResponse(content=jsonable_encoder(OpponentMasterResponse(opponent_id=results[0][0], name=results[0][1], kind=results[0][2], strength=results[0][3], experience=results[0][4])))


@router.get("/{opponent_id}", tags=["opponent_master"])
def read_opponent_master(opponent_id: int, db: Database = Depends(get_db)) -> JSONResponse:
    """
    Get a opponent master
    """
    with db.snapshot() as snapshot:
        query = f"SELECT OpponentId, Name, Kind, Strength, Experience From {TABLE} WHERE OpponentId={opponent_id}"
        results = list(snapshot.execute_sql(query, request_options={
                       "request_tag": create_req_tag("select", "read_opponent_master", "opponent_masters")}))
    if not results:
        raise HTTPException(
            status_code=404, detail="The opponent did not found")
    return JSONResponse(content=jsonable_encoder(OpponentMasterResponse(opponent_id=results[0][0], name=results[0][1], kind=results[0][2], strength=results[0][3], experience=results[0][4])))


@router.post("/", tags=["opponent_master"])
def create_opponent_master(opponent_master: OpponentMaster, db: Database = Depends(get_db)) -> JSONResponse:
    """
    Create opponent master
    """
    with db.batch() as batch:
        batch.insert(
            table=TABLE,
            columns=("OpponentId", "Name", "Kind", "Strength",
                     "Experience", "CreatedAt", "UpdatedAt"),
            values=[(get_uuid(), opponent_master.name, opponent_master.kind, opponent_master.strength,
                     opponent_master.experience, spanner.COMMIT_TIMESTAMP, spanner.COMMIT_TIMESTAMP)])
    return JSONResponse(status_code=201, content=jsonable_encoder(opponent_master))


@router.delete("/", tags=["opponent_master"])
def delete_opponent_master(db: Database = Depends(get_db)) -> JSONResponse:
    db.execute_partitioned_dml(f"DELETE FROM {TABLE} WHERE OpponentId > 0")
    return JSONResponse(content=jsonable_encoder({}))
