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
from random import randint, random
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from google.cloud import spanner
from google.cloud.spanner_v1.database import Database
from pydantic import BaseModel

from .utils import (create_req_tag, epoch_to_datetime, get_db,
                    get_entry_shard_id, get_uuid, num_shards)

OpponentMasters: str = "OpponentMasters"
Characters: str = "Characters"
# NOTE: force to use index in select
BattleHistory: str = "BattleHistory"
BattleHistoryByUserId: str = "@{FORCE_INDEX=BattleHistoryByUserId}"

router = APIRouter(prefix="/battles", tags=["battles"])


class Battles(BaseModel):
    character_id: str


class BattleHistoryResponse(BaseModel):
    user_id: str
    character_id: str
    opponent_id: str
    result: bool
    created_at: str
    updated_at: str


class Opponent(BaseModel):
    opponent_id: str
    kind: str
    strength: int
    experience: int


class Character(BaseModel):
    id: str
    user_id: str
    level: int
    experience: int
    strength: int


@router.post("/", tags=["battles"])
def battles(battles: Battles, db: Database = Depends(get_db)) -> JSONResponse:
    """
    Battles against opponents
    """
    def write_battle_result(transaction: Any) -> None:
        update_query = f"""
                        UPDATE {Characters}
                            SET 
                               Level = {character.level + int(random() / 0.95)},
                               Experience = {character.experience + opponent.experience},
                               Strength = {character.strength + randint(0, opponent.experience // 100)},
                               UpdatedAt = PENDING_COMMIT_TIMESTAMP()
                            WHERE
                               Id = {int(character.id)} AND UserId = {int(character.user_id)}
                        """
        insert_query = f"""
                        INSERT {BattleHistory}
                            (BattleHistoryId, UserId, Id, OpponentId, Result, EntryShardId, CreatedAt, UpdatedAt)
                        VALUES
                            ({get_uuid()}, {int(character.user_id)}, {int(character.id)}, {int(opponent.opponent_id)}, {result}, {get_entry_shard_id(int(character.user_id))}, PENDING_COMMIT_TIMESTAMP(), PENDING_COMMIT_TIMESTAMP())
                        """
        transaction.batch_update([update_query, insert_query], request_options={
                                 "request_tag": create_req_tag("update&insert", "run_battle", "characters&battlehistories")})

    with db.snapshot(multi_use=True) as snapshot:
        characters_query = f"SELECT Id, UserId, Level, Experience, Strength FROM {Characters} WHERE Id={battles.character_id}"
        characters = list(snapshot.execute_sql(characters_query, request_options={
                          "request_tag": create_req_tag("select", "run_battles", "characters")}))
        opponents_query = f"SELECT OpponentId, Kind, Strength, Experience FROM {OpponentMasters} TABLESAMPLE RESERVOIR (1 ROWS)"
        opponents = list(snapshot.execute_sql(opponents_query, request_options={"request_tag": create_req_tag("select", "run_battles", "opponents")}))
    if not opponents:
        raise HTTPException(status_code=503, detail="Any opponent masters does not found")
    if not characters:
        raise HTTPException(status_code=404, detail="The character did not found")
    opponent = Opponent(**dict(zip(Opponent.__fields__.keys(), opponents[0])))
    character = Character(**dict(zip(Character.__fields__.keys(), characters[0])))
    # NOTE: decide results randomly, because this is dummy game
    result: bool = random() <= 0.5
    if result:
        db.run_in_transaction(write_battle_result)
    return JSONResponse(content=jsonable_encoder({"result": result}))


@router.get("/history", tags=["battles"])
def battle_history(user_id: int, since: int, until: int, db: Database = Depends(get_db)) -> JSONResponse:
    """
    Append battle history

    stale read from history table between since and until
    """
    with db.snapshot(exact_staleness=timedelta(seconds=15)) as snapshot:
        query = f"""SELECT UserId, Id, OpponentId,  Result, CreatedAt, UpdatedAt FROM {BattleHistory+BattleHistoryByUserId}
                  WHERE UserId={user_id} AND UpdatedAt BETWEEN @Since AND @Until AND EntryShardId BETWEEN 0 AND {num_shards-1}
                  ORDER BY UpdatedAt DESC LIMIT 300"""
        params = {"Since": epoch_to_datetime(since), "Until": epoch_to_datetime(until)}
        params_type = {"Since": spanner.param_types.TIMESTAMP, "Until": spanner.param_types.TIMESTAMP}
        histories = snapshot.execute_sql(query, params=params, param_types=params_type, request_options={
            "request_tag": create_req_tag("select", "battlehistories", "battlehistory")})
    res = []
    for history in histories:
        result = dict(zip(BattleHistoryResponse.__fields__.keys(), history))
        # NOTE: need datetime to string
        result["created_at"] = result["created_at"].isoformat()
        result["updated_at"] = result["updated_at"].isoformat()
        res.append(BattleHistoryResponse(**result).dict())
    return JSONResponse(content=jsonable_encoder(res))


@router.delete("/history", tags=["battles"])
def delete_all_battle_histories(db: Database = Depends(get_db)) -> JSONResponse:
    db.execute_partitioned_dml(
        f"DELETE FROM {BattleHistory} WHERE BattleHistoryId > 0")
    return JSONResponse(content=jsonable_encoder({}))
