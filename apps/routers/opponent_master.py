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

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from google.cloud import spanner
from google.cloud.spanner_v1.database import Database
from pydantic import BaseModel, Field

from .utils import create_req_tag, get_db, get_uuid, opponent_master_delay

TABLE: str = "OpponentMasters"

router = APIRouter(prefix="/opponent_master", tags=["opponent_master"])


class OpponentMaster(BaseModel):
    name: str = Field(..., example="hoge")
    kind: str = Field(..., example="huga")
    strength: int = Field(..., example=10)
    experience: int = Field(..., example=10)


class OpponentMasterResponse(BaseModel):
    opponent_id: str = Field(..., example="111111111")
    name: str = Field(..., example="hoge")
    kind: str = Field(..., example="huga")
    strength: int = Field(..., example=10)
    experience: int = Field(..., example=10)


@router.get("/", tags=["opponent_master"], response_model=OpponentMasterResponse)
def get_random_opponent_master(db: Database = Depends(get_db)) -> JSONResponse:
    """Get a random opponent masters for test"""
    with db.snapshot(exact_staleness=timedelta(seconds=opponent_master_delay)) as snapshot:
        query = f"SELECT OpponentId, Name, Kind, Strength, Experience FROM {TABLE} TABLESAMPLE RESERVOIR (1 ROWS)"
        results = list(snapshot.execute_sql(query))
    if not results:
        return JSONResponse(content={})
    return JSONResponse(content=jsonable_encoder(OpponentMasterResponse(opponent_id=results[0][0], name=results[0][1], kind=results[0][2], strength=results[0][3], experience=results[0][4])))


@router.get("/{opponent_id}", tags=["opponent_master"], response_model=OpponentMasterResponse, responses={status.HTTP_404_NOT_FOUND: {"description": "Opponent does not found", "content": {"application/json": {"example": {"detail": "This opponent does not found"}}}}})
def get_opponent_master(opponent_id: int, db: Database = Depends(get_db)) -> JSONResponse:
    """Get a opponent master"""
    with db.snapshot() as snapshot:
        query = f"SELECT OpponentId, Name, Kind, Strength, Experience From {TABLE} WHERE OpponentId=@OpponentId"
        params = {"OpponentId": opponent_id}
        params_type = {"OpponentId": spanner.param_types.INT64}
        request_options = {"request_tag": create_req_tag("select", "get_opponent_master", "opponent_masters")}
        results = list(snapshot.execute_sql(query, params=params, param_types=params_type, request_options=request_options))
    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This opponent does not found")
    return JSONResponse(content=jsonable_encoder(OpponentMasterResponse(opponent_id=results[0][0], name=results[0][1], kind=results[0][2], strength=results[0][3], experience=results[0][4])))


@router.post("/", tags=["opponent_master"], response_model=OpponentMasterResponse, status_code=status.HTTP_201_CREATED)
def create_opponent_master(opponent_master: OpponentMaster, db: Database = Depends(get_db)) -> JSONResponse:
    """Create opponent master"""
    with db.batch() as batch:
        uid = get_uuid()
        batch.insert(table=TABLE, columns=("OpponentId", "Name", "Kind", "Strength", "Experience", "CreatedAt", "UpdatedAt"),
                     values=[(uid, opponent_master.name, opponent_master.kind, opponent_master.strength, opponent_master.experience, spanner.COMMIT_TIMESTAMP, spanner.COMMIT_TIMESTAMP)])
        res = OpponentMasterResponse(opponent_id=uid, name=opponent_master.name, kind=opponent_master.kind,
                                     strength=opponent_master.strength, experience=opponent_master.experience)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=jsonable_encoder(res))


@router.delete("/", tags=["opponent_master"])
def delete_opponent_master(db: Database = Depends(get_db)) -> JSONResponse:
    db.execute_partitioned_dml(f"DELETE FROM {TABLE} WHERE OpponentId > 0")
    return JSONResponse(content=jsonable_encoder({}))
