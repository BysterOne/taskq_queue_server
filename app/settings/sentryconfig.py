import logging
import os
from typing import Any
from urllib.parse import urlparse

import sentry_sdk

SENTRY_DSN = os.environ.get('SENTRY_DSN')
SENTRY_ENV = os.environ.get('SENTRY_ENV')
EVENT_LEVEL = logging.ERROR
SENTRY_TAGS = {
    'app_name': os.environ.get('APP_LABEL', 'altyn-altyn-processing'),
}


def _get_namespace() -> str:
    mapping = {
        'production': 'altyn',
        'staging': 'altyn-staging',
    }
    return os.environ.get('NAMESPACE') or mapping.get(SENTRY_ENV, 'altyn')


def _grafana_logs_link(trace_id: str) -> str:
    namespace = _get_namespace()
    return (
        f"https://grafana.bp.send2card.win/explore?schemaVersion=1&panes=%7B%22vuh%22%3A%7B%22datasource%22%3A%22P982945308D3682D1%22%2C%22queries%22%3A%5B%7B%22refId%22%3A%22A%22%2C%22expr%22%3A%22%7Bnamespace%3D%5C%22{namespace}%5C%22%7D+%7C+json+%7C+sentry_trace_id+%3D+%60{trace_id}%60%22%2C%22queryType%22%3A%22range%22%2C%22datasource%22%3A%7B%22type%22%3A%22loki%22%2C%22uid%22%3A%22P982945308D3682D1%22%7D%2C%22editorMode%22%3A%22builder%22%7D%5D%2C%22range%22%3A%7B%22from%22%3A%22now-1h%22%2C%22to%22%3A%22now%22%7D%7D%7D&orgId=1"
    )


def is_healthcheck(event: dict[str, Any]) -> bool:
    if url_string := event.get('request', {}).get('url'):
        parsed_url = urlparse(url_string)
        return parsed_url.path.startswith('/-/')

    return False


def is_request_finished(event: dict[str, Any]) -> bool:
    message = event.get('message') or event.get('logentry', {}).get('message')
    return message == 'request_finished'


def before_send(event: dict[str, Any], _: Any) -> dict[str, Any] | None:
    if is_request_finished(event):
        return None

    if url := event.get('request', {}).get('url'):
        if 'admin' in url:
            event.setdefault('tags', {}).update({'admin': True})

    event.setdefault('tags', {}).update(SENTRY_TAGS)

    trace_id = event.get('contexts', {}).get('trace', {}).get('trace_id')
    if trace_id:
        event['tags']['LOGS'] = _grafana_logs_link(trace_id)

    return event


def before_send_transaction(event: dict[str, Any], _: Any) -> dict[str, Any] | None:
    # do not send healthcheck events
    if is_healthcheck(event):
        return

    event = before_send(event, _)
    return event


def propagate_sentry_tracing() -> dict[str, Any]:
    """
    Get sentry tracing kwargs from the current scope to initialize a new child transaction.

    Usage:
    ```
    with sentry_sdk.start_transaction(
        op="usecase.execute",
        name="usecase description",
        **propagate_sentry_tracing(),
    ):
        ...
    ```
    """
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
