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
ENV PATH="/usr/local/bin/:$PATH"
ENV PYTHONUNBUFFERED=1
COPY --from=builder /tmp/requirements.txt /user/src/app/requirements.txt
# ref: https://github.com/locustio/locust/blob/a0bcd31e3dbed934dccaf6dd33daf16eb96550b6/Dockerfile#L5
RUN apt-get update && apt-get upgrade -y && apt install -y --no-install-recommends git gcc python3-dev && pip install --no-cache-dir --upgrade -r /user/src/app/requirements.txt
COPY ./locustfile.py /user/src/app/locustfile.py