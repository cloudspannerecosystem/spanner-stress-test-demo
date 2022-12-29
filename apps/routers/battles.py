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
from random import choice, randint, random
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from google.cloud import spanner
from google.cloud.spanner_v1.database import Database
from pydantic import BaseModel, Field

from .utils import (battle_history_delay, create_req_tag, epoch_to_datetime,
                    get_db, get_entry_shard_id, get_uuid, num_shards)

OpponentMasters: str = "OpponentMasters"
Characters: str = "Characters"
# NOTE: force to use index in select
BattleHistory: str = "BattleHistory"
BattleHistoryByUserId: str = "@{FORCE_INDEX=BattleHistoryByUserId}"

router = APIRouter(prefix="/battles", tags=["battles"])


class Battles(BaseModel):
    character_id: str = Field(..., example="111111111")


class BattleResponse(BaseModel):
    retult: bool = Field(..., example=True)


class BattleHistoryResponse(BaseModel):
    user_id: str = Field(..., example="111111111")
    character_id: str = Field(..., example="111111111")
    opponent_id: str = Field(..., example="111111111")
    result: bool = Field(..., example=True)
    created_at: str = Field(..., example="2022-10-28T18:13:52.227030+00:00")
    updated_at: str = Field(..., example="2022-10-28T18:19:52.227030+00:00")


class Opponent(BaseModel):
    opponent_id: str = Field(..., example="111111111")
    kind: str = Field(..., example="hoge")
    strength: int = Field(..., example=10)
    experience: int = Field(..., example=10)


class Character(BaseModel):
    id: str = Field(..., example="111111111")
    user_id: str = Field(..., example="111111111")
    level: int = Field(..., example=10)
    experience: int = Field(..., example=10)
    strength: int = Field(..., example=10)


battle_resp_docs: Dict[int, Dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "description": "User character does not find",
        "content": {
            "application/json": {
                "example": {"detail": "This character does not found"}
            }
        },
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "description": "Oppnent master data does not exsist",
        "content": {
            "application/json": {
                "example": {"detail": "Any opponent masters does not found"}
            }
        },
    }
}


@router.post("/", tags=["battles"], response_model=BattleResponse, status_code=status.HTTP_201_CREATED, responses={**battle_resp_docs})
def battles(battles: Battles, db: Database = Depends(get_db)) -> JSONResponse:
    """Battle against a opponent"""
    def battle_repository(transaction: Any) -> None:
        update_query = f"UPDATE {Characters} SET Level=@LEVEL, Experience=@Experience, Strength=@Strength, UpdatedAt=PENDING_COMMIT_TIMESTAMP() WHERE Id=@Id AND UserId=@UserId"
        update_params = {"Level": character.level + int(random() / 0.95), "Experience": character.experience + opponent.experience, "Strength": character.strength + randint(0, opponent.experience // 100), "Id": int(character.id), "UserId": int(character.user_id)}
        update_params_type = {"Level": spanner.param_types.INT64, "Experience": spanner.param_types.INT64, "Strength": spanner.param_types.INT64, "Id": spanner.param_types.INT64, "UserId": spanner.param_types.INT64}
        update_request_options = {"request_tag": create_req_tag("update", "run_battle", "characters")}
        transaction.execute_update(update_query, params=update_params, param_types=update_params_type, request_options=update_request_options)

        insert_query = f"INSERT {BattleHistory} (BattleHistoryId, UserId, Id, OpponentId, Result, EntryShardId, CreatedAt, UpdatedAt) VALUES (@BattleHistoryId, @UserId, @Id, @OpponentId, @Result, @EntryShardId, PENDING_COMMIT_TIMESTAMP(), PENDING_COMMIT_TIMESTAMP())"
        insert_params = {"BattleHistoryId": get_uuid(), "UserId": int(character.user_id), "Id": int(character.id), "OpponentId": int(opponent.opponent_id), "Result": result, "EntryShardId": get_entry_shard_id(int(character.user_id))}
        insert_params_type = {"BattleHistoryId": spanner.param_types.INT64, "UserId": spanner.param_types.INT64, "Id": spanner.param_types.INT64, "OpponentId": spanner.param_types.INT64, "Result": spanner.param_types.BOOL, "EntryShardId": spanner.param_types.INT64}
        insert_request_options = {"request_tag": create_req_tag("insert", "run_battle", "battlehistories")}
        transaction.execute_update(insert_query, params=insert_params, param_types=insert_params_type, request_options=insert_request_options)

    with db.snapshot(multi_use=True) as snapshot:
        characters_query = f"SELECT Id, UserId, Level, Experience, Strength FROM {Characters} WHERE Id=@Id"
        characters_params, characters_params_type = {"Id": battles.character_id}, {"Id": spanner.param_types.INT64}
        characters_request_options = {"request_tag": create_req_tag("select", "read_user", "users")}
        characters = list(snapshot.execute_sql(characters_query, params=characters_params, param_types=characters_params_type, request_options=characters_request_options))
        opponents_query = f"SELECT OpponentId, Kind, Strength, Experience FROM {OpponentMasters} TABLESAMPLE RESERVOIR (1 ROWS)"
        opponents = list(snapshot.execute_sql(opponents_query, request_options={"request_tag": create_req_tag("select", "run_battles", "opponents")}))

    if not opponents:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Any opponent masters does not found")
    if not characters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This character does not found")
    opponent = Opponent(**dict(zip(Opponent.__fields__.keys(), opponents[0])))
    character = Character(**dict(zip(Character.__fields__.keys(), choice(characters))))
    # NOTE: decide results randomly, because this is dummy game
    result: bool = random() <= 0.5

    db.run_in_transaction(battle_repository)

    return JSONResponse(content=jsonable_encoder(BattleResponse(retult=result)), status_code=status.HTTP_201_CREATED)


@router.get("/history", tags=["battles"], response_model=List[Optional[BattleHistoryResponse]])
def get_battle_histories(user_id: int, since: int, until: int, db: Database = Depends(get_db)) -> JSONResponse:
    """
    Append battle history

    stale read from history table between since and until
    """
    with db.snapshot(exact_staleness=timedelta(seconds=battle_history_delay)) as snapshot:
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


@router.delete("/history", tags=["battles"], response_model=Optional[dict])
def delete_all_battle_histories(db: Database = Depends(get_db)) -> JSONResponse:
    db.execute_partitioned_dml(f"DELETE FROM {BattleHistory} WHERE BattleHistoryId > 0")
    return JSONResponse(content=jsonable_encoder({}))
