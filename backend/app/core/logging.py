"""
This module is used to configure the logging for the application.
"""
import logging
import os
from logging import Logger, LogRecord
import json
from datetime import datetime

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


class JSONFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        payload = {
            "timestamp" : datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level" : record.levelname,
            "logger" : record.name,
            "message" : record.getMessage(),
            "module" : record.module,
            "funcName" : record.funcName,
            "lineNo" : record.lineno,
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in ("name","msg","args","levelname","levelno",
                         "pathname","filename","module","exc_info",
                         "exc_text","stack_info","lineno","funcName",
                         "created","msecs","relativeCreated","thread",
                         "threadName","processName","process")
        }
        if extras:
            payload["extra"] = extras

        return json.dumps(payload, ensure_ascii=False)


# Configure root once; avoid duplicate handlers under reloaders
if not logging.getLogger().handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.setLevel(_LOG_LEVEL)
    root.addHandler(handler)


logger: Logger = logging.getLogger("ragops")
logger.setLevel(_LOG_LEVEL)
