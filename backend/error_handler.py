"""
Centralized resilience and contextual error handling utilities.
"""

import time
from datetime import datetime


class ErrorRecovery:
    """Resilience helpers: retries, graceful fallback, and circuit breaker."""

    @staticmethod
    def retry_on_failure(func, max_attempts=3, backoff_seconds=1, exceptions=(Exception,), *args, **kwargs):
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= max_attempts:
                    break
                sleep_time = backoff_seconds * (2 ** (attempt - 1))
                time.sleep(sleep_time)
        raise last_error

    @staticmethod
    def graceful_degradation(primary_func, fallback_func, *args, **kwargs):
        try:
            return primary_func(*args, **kwargs)
        except Exception:
            return fallback_func(*args, **kwargs)

    @staticmethod
    def circuit_breaker(func, failure_threshold=5, timeout_seconds=60):
        state = {
            'mode': 'CLOSED',
            'failures': 0,
            'opened_at': None,
        }

        def wrapper(*args, **kwargs):
            now = time.time()

            if state['mode'] == 'OPEN':
                opened_at = state['opened_at'] or now
                if now - opened_at >= timeout_seconds:
                    state['mode'] = 'HALF_OPEN'
                else:
                    raise RuntimeError('Circuit breaker open: failing fast')

            try:
                result = func(*args, **kwargs)
                state['failures'] = 0
                state['mode'] = 'CLOSED'
                state['opened_at'] = None
                return result
            except Exception:
                state['failures'] += 1
                if state['failures'] >= failure_threshold:
                    state['mode'] = 'OPEN'
                    state['opened_at'] = now
                raise

        return wrapper


class ContextualErrors:
    """User-facing error translation and actionable suggestions."""

    ERROR_MAP = {
        'TimeoutError': 'Generation took longer than expected. Please try again.',
        'MemoryError': 'System is currently busy. Please retry shortly.',
        'ConnectionError': 'Unable to reach backend service right now.',
        'ModelNotLoaded': 'ML model is not ready yet. Use standard generation temporarily.',
        'ValueError': 'Invalid input. Please review and try again.',
        'RuntimeError': 'The service encountered a runtime issue. Please retry.',
    }

    SUGGESTION_MAP = {
        'TimeoutError': 'Lower shots or max attempts, then try again.',
        'MemoryError': 'Retry in a minute or reduce request intensity.',
        'ConnectionError': 'Check service status and network connectivity.',
        'ModelNotLoaded': 'Train/reload model via /api/ml/train or continue without correction.',
        'ValueError': 'Validate request payload fields and ranges.',
        'RuntimeError': 'Check logs and health endpoint for additional details.',
    }

    @staticmethod
    def format_error_for_user(error_type, error_message):
        friendly = ContextualErrors.ERROR_MAP.get(error_type)
        if friendly:
            return friendly
        if error_message:
            return f'Operation failed: {error_message}'
        return 'Unexpected error occurred. Please try again.'

    @staticmethod
    def suggest_action(error_type):
        return ContextualErrors.SUGGESTION_MAP.get(
            error_type,
            'Retry the request. If the issue persists, contact the administrator with timestamp and request details.',
        )

    @staticmethod
    def with_context(error_type, error_message):
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error_type': error_type,
            'message': ContextualErrors.format_error_for_user(error_type, error_message),
            'suggested_action': ContextualErrors.suggest_action(error_type),
        }
