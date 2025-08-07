import os

import sentry_sdk
import structlog
from structlog_sentry import SentryProcessor

from settings import sentryconfig

LOG_LEVELS = {
    'CRITICAL': 50,
    'ERROR': 40,
    'WARNING': 30,
    'INFO': 20,
    'DEBUG': 10,
}


# noinspection PyUnusedLocal
def add_sentry_tags_to_log(logger, _: str, event_dict):
    span = sentry_sdk.get_current_span()
    if span:
        event_dict['sentry_trace_id'] = span.trace_id
        event_dict['sentry_span_id'] = span.span_id

        if span.containing_transaction:
            event_dict['transaction'] = span.containing_transaction.name

    return event_dict


def configure_logger(log_level: str = 'INFO', env_profile: str = 'dev') -> None:
    if sentryconfig.SENTRY_DSN is not None:
        sentry_sdk.init(
            debug=False,
            environment=env_profile,
            dsn=sentryconfig.SENTRY_DSN,
            before_send=sentryconfig.before_send,
            before_send_transaction=sentryconfig.before_send_transaction,
            traces_sample_rate=1.0,
            send_default_pii=True,
            auto_session_tracking=True,
        )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt='iso', key='date'),
        structlog.processors.add_log_level,
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
        structlog.dev.ConsoleRenderer(),
    ]

    structlog.configure(
        context_class=dict,
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            LOG_LEVELS.get(log_level.upper(), 20)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
