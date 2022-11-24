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

import logging
from json import dumps
from multiprocessing import cpu_count
from os import getenv
from sys import stdout

import stackprinter
from gunicorn.app.base import BaseApplication
from gunicorn.glogging import Logger
from loguru import logger
# NOTE: opentelemetry libraries
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.cloud_trace_propagator import \
    CloudTraceFormatPropagator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# NOTE: settings from env values
ENV = getenv("ENV", "local")
PROJECT = getenv("GOOGLE_CLOUD_PROJECT", "local")
LOG_LEVEL = logging.getLevelName(getenv("LOG_LEVEL", "DEBUG"))
WORKERS = 2 * cpu_count() + 1


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage())


class StubbedGunicornLogger(Logger):
    def setup(self, cfg):
        handler = logging.NullHandler()
        self.error_logger = logging.getLogger("gunicorn.error")
        self.error_logger.addHandler(handler)
        self.access_logger = logging.getLogger("gunicorn.access")
        self.access_logger.addHandler(handler)
        self.error_logger.setLevel(LOG_LEVEL)
        self.access_logger.setLevel(LOG_LEVEL)


class StandaloneApplication(BaseApplication):
    """Our Gunicorn application."""

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def setup_trace() -> None:
    if ENV == "production":
        # NOTE: Cloud Trace settings
        set_global_textmap(CloudTraceFormatPropagator())
        tracer_provider = TracerProvider()
        cloud_trace_exporter = CloudTraceSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
        trace.set_tracer_provider(tracer_provider)
        trace.get_tracer(__name__)


def serialize(record):
    # NOTE: Serialize Cloud Logging format
    # ref: https://loguru.readthedocs.io/en/stable/resources/recipes.html#serializing-log-messages-using-a-custom-function
    entry = {
        "time": record["time"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "severity": record["level"].name,
        "message": record["message"],
        "logging.googleapis.com/sourceLocation": {"file": record["file"].name, "line": record["line"], "function": record["function"], "path": record["file"].path},
        "logging.googleapis.com/operation": {"process": record["process"].name, "thread": record["thread"].name, "module": record["name"]}
    }
    if record["exception"]:
        # ref: https://loguru.readthedocs.io/en/stable/resources/recipes.html#customizing-the-formatting-of-exceptions
        entry["extra"] = stackprinter.format(record["exception"])
    # TODO: add trace id to conbine cloud trace
    # entry["logging.googleapis.com/trace"] = xxx
    return dumps(entry)


def sink(message):
    # NOTE: Change sync to customize log format for Cloud Logging
    # ref: https://loguru.readthedocs.io/en/stable/resources/recipes.html#serializing-log-messages-using-a-custom-function
    print(serialize(message.record))


def setup_gunicorn() -> dict:
    # NOTE: gunicorn and uvicorn logging settings
    # ref: https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/
    intercept_handler = InterceptHandler()
    logging.basicConfig(handlers=[intercept_handler], level=LOG_LEVEL)
    logging.root.handlers = [intercept_handler]
    logging.root.setLevel(LOG_LEVEL)

    seen = set()
    for name in [
        *logging.root.manager.loggerDict.keys(),
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            logging.getLogger(name).handlers = [intercept_handler]

    if ENV == "production":
        handlers = [{"sink": sink, "serialize": True}]
    else:
        handlers = [{"sink": stdout}]
    logger.configure(handlers=handlers)

    return {
        "bind": "0.0.0.0",
        "workers": 2 * cpu_count() + 1,
        "accesslog": "-",
        "errorlog": "-",
        "worker_class": "uvicorn.workers.UvicornWorker",
        "logger_class": StubbedGunicornLogger,
        "reload": True,
    }
