"""
Logging utilities for AutoBI backend.
Provides structured logging with request IDs and timing.
"""

import logging
import time
import uuid
from functools import wraps
from typing import Any, Callable
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('autobi')


class RequestContext:
    """Thread-local storage for request context."""
    _request_id: str = ""
    _start_time: float = 0
    
    @classmethod
    def set_request_id(cls, request_id: str = None):
        cls._request_id = request_id or str(uuid.uuid4())[:8]
        cls._start_time = time.time()
        return cls._request_id
    
    @classmethod
    def get_request_id(cls) -> str:
        return cls._request_id or "no-req"
    
    @classmethod
    def get_elapsed_ms(cls) -> float:
        if cls._start_time:
            return (time.time() - cls._start_time) * 1000
        return 0
    
    @classmethod
    def clear(cls):
        cls._request_id = ""
        cls._start_time = 0


def log_with_context(level: str, message: str, **kwargs):
    """Log with request context and optional structured data."""
    req_id = RequestContext.get_request_id()
    elapsed = RequestContext.get_elapsed_ms()
    
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    full_message = f"[{req_id}] [{elapsed:.1f}ms] {message}"
    if extra:
        full_message += f" | {extra}"
    
    getattr(logger, level)(full_message)


def log_info(message: str, **kwargs):
    log_with_context('info', message, **kwargs)


def log_error(message: str, **kwargs):
    log_with_context('error', message, **kwargs)


def log_warning(message: str, **kwargs):
    log_with_context('warning', message, **kwargs)


def log_debug(message: str, **kwargs):
    log_with_context('debug', message, **kwargs)


@contextmanager
def log_timing(operation: str):
    """Context manager to log operation timing."""
    start = time.time()
    try:
        yield
    finally:
        elapsed = (time.time() - start) * 1000
        log_info(f"{operation} completed", duration_ms=f"{elapsed:.2f}")


def timed(operation: str = None):
    """Decorator to log function execution time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            op_name = operation or func.__name__
            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start) * 1000
                log_info(f"{op_name} completed", duration_ms=f"{elapsed:.2f}")
                return result
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                log_error(f"{op_name} failed", duration_ms=f"{elapsed:.2f}", error=str(e))
                raise
        return wrapper
    return decorator


def log_query(question: str, table: str, sql: str, row_count: int, execution_time: float, confidence: float):
    """Log query execution details."""
    log_info(
        "Query executed",
        question=question[:50] + "..." if len(question) > 50 else question,
        table=table,
        rows=row_count,
        exec_ms=f"{execution_time:.2f}",
        confidence=f"{confidence:.2f}"
    )


def log_upload(filename: str, table_name: str, row_count: int, column_count: int):
    """Log file upload details."""
    log_info(
        "File uploaded",
        filename=filename,
        table=table_name,
        rows=row_count,
        columns=column_count
    )


def log_error_detail(error: Exception, context: str = ""):
    """Log detailed error information."""
    log_error(
        f"Error in {context}" if context else "Error occurred",
        type=type(error).__name__,
        message=str(error)
    )
