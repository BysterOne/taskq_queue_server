import os
from typing import Any

import sentry_sdk

SENTRY_DSN = os.environ.get('SENTRY_DSN')
SENTRY_ENV = os.environ.get('SENTRY_ENV')
EVENT_LEVEL = 40
SENTRY_TAGS = {
    'app_name': os.environ.get('APP_LABEL', 'taskq-queue-server'),
}


def before_send(event: dict[str, Any], _: Any) -> dict[str, Any] | None:
    event.setdefault('tags', {}).update(SENTRY_TAGS)
    return event


def before_send_transaction(event: dict[str, Any], _: Any) -> dict[str, Any] | None:
    return before_send(event, _)


def propagate_sentry_tracing() -> dict[str, Any]:
    scope = sentry_sdk.get_current_scope()
    sentry_trace_id, sentry_parent_span_id, baggage = None, None, None
    if scope and scope.transaction:
        sentry_trace_id = scope.transaction.trace_id
        sentry_parent_span_id = scope.transaction.span_id
        baggage = scope.transaction.get_baggage()

    return {
        'trace_id': sentry_trace_id,
        'parent_span_id': sentry_parent_span_id,
        'parent_sampled': True if sentry_parent_span_id else None,
        'baggage': baggage,
    }

