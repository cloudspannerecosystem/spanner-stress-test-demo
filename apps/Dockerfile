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

FROM python:3.9-slim-buster as builder
WORKDIR /tmp
RUN pip install pipenv
COPY Pipfile Pipfile.lock /tmp/
RUN pipenv requirements > requirements.txt

FROM python:3.9-slim-buster as runner
WORKDIR /user/src/app
COPY ./ /user/src/app
COPY --from=builder /tmp/requirements.txt /user/src/app/requirements.txt
RUN apt-get update && apt-get install -y build-essential && pip install --no-cache-dir --upgrade -r /user/src/app/requirements.txt && adduser --disabled-password --gecos '' app_user && chown -R app_user /user/src/
USER app_user
ENTRYPOINT python /user/src/app/main.py