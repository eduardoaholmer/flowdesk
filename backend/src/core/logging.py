import logging
import sys
from contextvars import ContextVar

import structlog

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def _inject_request_id(
    _logger: object, _method_name: str, event_dict: structlog.types.EventDict
) -> structlog.types.EventDict:
    request_id = request_id_ctx.get()
    if request_id is not None:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging(*, log_level: str, json_output: bool) -> None:
    """Configura structlog. JSON em produção, formato legível em desenvolvimento.

    A escolha do renderer é a única diferença entre ambientes — os processadores
    (nível, timestamp, request_id) são os mesmos, para que o comportamento observado
    em desenvolvimento seja representativo do que roda em produção.
    """
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)

    shared_processors: list[structlog.types.Processor] = [
        _inject_request_id,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    renderer = (
        structlog.processors.JSONRenderer() if json_output else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.types.FilteringBoundLogger:
    logger: structlog.types.FilteringBoundLogger = structlog.get_logger(name)
    return logger
