import logging
import os

import sentry_sdk
import structlog
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from structlog_sentry import SentryProcessor

from settings import sentryconfig

DEBUG = bool(os.getenv('DEBUG', False))
DISABLED_LOGGERS = {
    'openai',
    'sentry_sdk',
    'celery.utils.functional',
    'git.cmd',
    'datadog',
    'numexpr',
    'faker',
}


# noinspection PyUnusedLocal
def add_sentry_tags_to_log(
    logger: logging.Logger,
    _: str,
    event_dict: structlog.stdlib.EventDict,
) -> structlog.stdlib.EventDict:
    span = sentry_sdk.get_current_span()
    if span:
        event_dict['sentry_trace_id'] = span.trace_id
        event_dict['sentry_span_id'] = span.span_id

        if span.containing_transaction:
            event_dict['transaction'] = span.containing_transaction.name

    return event_dict


def configure_logger(log_level: str = 'INFO', env_profile: str = 'dev') -> None:
    logging.basicConfig(level=log_level)

    if sentryconfig.SENTRY_DSN is not None:
        sentry_sdk.init(
            debug=False,
            environment=env_profile,
            dsn=sentryconfig.SENTRY_DSN,
            integrations=[
                DjangoIntegration(cache_spans=True),
                LoggingIntegration(event_level=None, level=None),
            ],
            ignore_errors=[],
            before_send=sentryconfig.before_send,
            before_send_transaction=sentryconfig.before_send_transaction,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            send_default_pii=True,
            auto_session_tracking=True,
        )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt='iso', key='date'),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        SentryProcessor(
            active=sentryconfig.SENTRY_DSN is not None,
            event_level=sentryconfig.EVENT_LEVEL,
            as_context=True,
            tag_keys='__all__',
        ),
        add_sentry_tags_to_log,
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    structlog.configure(
        context_class=dict,
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,  # noqa
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )

    for logger_name in DISABLED_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
