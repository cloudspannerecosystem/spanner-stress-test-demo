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

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from routers.battles import router as battle_router
from routers.character_master import router as character_master_router
from routers.characters import router as characters_router
from routers.opponent_master import router as opponent_master_router
from routers.users import router as user_router
from settings import StandaloneApplication, setup_gunicorn, setup_trace

app = FastAPI(title="sample game api", description="sample game app for spanner-stress-test-demo", version=1.0)
# NOTE: API version 1
prefix_v1 = "/api/v1"
app.include_router(user_router, prefix=prefix_v1)
app.include_router(characters_router, prefix=prefix_v1)
app.include_router(character_master_router, prefix=prefix_v1)
app.include_router(opponent_master_router, prefix=prefix_v1)
app.include_router(battle_router, prefix=prefix_v1)


@app.on_event("startup")
async def startup_event():
    setup_trace()
    FastAPIInstrumentor.instrument_app(app)

if __name__ == '__main__':
    options = setup_gunicorn()
    StandaloneApplication(app, options).run()
