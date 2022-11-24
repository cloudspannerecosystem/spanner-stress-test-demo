-- Copyright 2022 Google LLC
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     https://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

CREATE TABLE CharacterMasters (
    CharacterId INT64 NOT NULL,
    Name STRING(16) NOT NULL,
    Kind STRING(16) NOT NULL,
    CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp = true),
    UpdatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp = true),
) PRIMARY KEY (CharacterId);

CREATE TABLE OpponentMasters (
    OpponentId INT64 NOT NULL,
    Name STRING(32) NOT NULL,
    Kind STRING(16) NOT NULL,
    Strength INT64 NOT NULL,
    Experience INT64 NOT NULL,
    CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp = true),
    UpdatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp = true),
) PRIMARY KEY (OpponentId);

CREATE TABLE Users (
    UserId INT64 NOT NULL,
    Name STRING(32) NOT NULL,
    Mail STRING(64) NOT NULL,
    Password STRING(64) NOT NULL,
    CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp = true),
    UpdatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp = true),
) PRIMARY KEY (UserId);

CREATE TABLE Characters (
    Id INT64 NOT NULL,
    UserId INT64 NOT NULL,
    CharacterId INT64 NOT NULL,
    Name STRING(16) NOT NULL,
    Level INT64 NOT NULL,
    Experience INT64 NOT NULL,
    Strength INT64 NOT NULL,
    CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp = true),
    UpdatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp = true),
    FOREIGN KEY (UserId) REFERENCES Users (UserId),
    FOREIGN KEY (CharacterId) REFERENCES CharacterMasters (CharacterId),
) PRIMARY KEY (UserId, Id),
INTERLEAVE IN PARENT Users ON DELETE CASCADE;

CREATE TABLE BattleHistory (
    BattleHistoryId INT64 NOT NULL,
    UserId INT64 NOT NULL,
    Id INT64 NOT NULL,
    OpponentId INT64 NOT NULL,
    Result BOOL NOT NULL,
    EntryShardId INT64 NOT NULL,
    CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp = true),
    UpdatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp = true),
    FOREIGN KEY (UserId) REFERENCES Users (UserId),
    FOREIGN KEY (Id) REFERENCES Characters (Id),
    FOREIGN KEY (OpponentId) REFERENCES OpponentMasters (OpponentId),
) PRIMARY KEY (
    UserId,
    Id,
    OpponentId,
    BattleHistoryId
),
INTERLEAVE IN PARENT Users ON DELETE CASCADE;

CREATE INDEX BattleHistoryByUserId ON BattleHistory(EntryShardId, UserId, UpdatedAt DESC);