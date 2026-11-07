"""
Sev-1 Hotfix: Implement resilient DB connection retries for auth-db-primary.

Remediates connection timeouts by wrapping primary DB connection attempts with
exponential backoff, jitter, and operational error handling.
"""

import logging
import random
import time
from typing import Any, Callable, Optional, TypeVar
import psycopg2
from psycopg2 import OperationalError, InterfaceError
import sqlalchemy
from sqlalchemy.exc import DBAPIError, OperationalError as SAOperationalError

logger = logging.getLogger("auth_db_primary.connection")

T = TypeVar("T")

DEFAULT_MAX_RETRIES = 5
DEFAULT_INITIAL_BACKOFF = 0.5  # seconds
DEFAULT_MAX_BACKOFF = 10.0     # seconds
DEFAULT_BACKOFF_FACTOR = 2.0

class DBConnectionTimeoutError(Exception):
    """Raised when all DB connection retry attempts are exhausted."""
    pass

def retry_db_connection(
    connect_fn: Callable[..., T],
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_backoff: float = DEFAULT_INITIAL_BACKOFF,
    max_backoff: float = DEFAULT_MAX_BACKOFF,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    *args: Any,
    **kwargs: Any
) -> T:
    """
    Executes a DB connection function with exponential backoff and full jitter.

    Handles connection timeouts, transient network failures, and PostgreSQL
    operational errors for auth-db-primary.
    """
    attempt = 0
    backoff = initial_backoff

    retryable_exceptions = (
        OperationalError,
        InterfaceError,
        SAOperationalError,
        DBAPIError,
        TimeoutError,
        ConnectionResetError,
        ConnectionRefusedError,
    )

    while attempt < max_retries:
        attempt += 1
        try:
            logger.info("Attempting DB connection to auth-db-primary (attempt %d/%d)...", attempt, max_retries)
            connection = connect_fn(*args, **kwargs)
            logger.info("Successfully connected to auth-db-primary on attempt %d.", attempt)
            return connection
        except retryable_exceptions as exc:
            if attempt >= max_retries:
                logger.critical(
                    "Exhausted all %d connection retries to auth-db-primary. Last error: %s",
                    max_retries, exc, exc_info=True
                )
                raise DBConnectionTimeoutError(
                    f"Failed to connect to auth-db-primary after {max_retries} attempts: {exc}"
                ) from exc

            # Calculate backoff with full jitter to avoid thundering herd on primary DB
            sleep_time = random.uniform(0, min(max_backoff, backoff))
            logger.warning(
                "DB connection attempt %d/%d failed with error: %s. Retrying in %.2fs...",
                attempt, max_retries, exc, sleep_time
            )
            time.sleep(sleep_time)
            backoff *= backoff_factor

def create_resilient_engine(dsn: str, pool_size: int = 20, max_overflow: int = 10, **kwargs: Any) -> sqlalchemy.engine.Engine:
    """
    Helper to construct SQLAlchemy engine for auth-db-primary with robust pool pre-ping
    and connection timeout parameters.
    """
    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_recycle": 1800,
        "connect_args": {
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 3
        }
    }
    engine_kwargs.update(kwargs)
    
    return retry_db_connection(
        sqlalchemy.create_engine,
        dsn,
        **engine_kwargs
    )
