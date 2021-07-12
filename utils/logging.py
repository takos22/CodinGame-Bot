import logging

from .text import uncolor


class NoColorFormatter(logging.Formatter):
    def format(self, record):
        record = logging.LogRecord(
            record.name,
            record.levelno,
            record.pathname,
            record.lineno,
            uncolor(record.msg),
            record.args,
            record.exc_info,
            record.funcName,
            record.stack_info,
        )
        return super().format(record)
