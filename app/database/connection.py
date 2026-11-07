"""
Hotfix: Sev-1 DB Connection Pool Exhaustion in auth-db-primary

Remediation Summary:
1. Increased pool_size from 5 (exhaustion threshold) to 50 with max_overflow=10.
2. Enabled pool_pre_ping=True to prevent stale connections from causing timeouts.
3. Added pool_timeout=10 and pool_recycle=1800 for automatic pool management.
4. Implemented resilient session handling with automatic rollback and retry logic.
"""

import os
import logging
import time
from contextlib import contextmanager
from typing import Generator

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import OperationalError, DBAPIError

logger = logging.getLogger("auth_db")
logger.setLevel(logging.INFO)

# Configuration with hotfix defaults
DB_URI = os.getenv("AUTH_DB_URI", "postgresql://auth_user:auth_pass@auth-db-primary:5432/auth_db")
POOL_SIZE = int(os.getenv("DB_MAX_CONNS", "50"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "10"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))

# Initialize Engine with optimized connection pool configuration
engine = create_engine(
    DB_URI,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    pool_pre_ping=True,
)

SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
ScopedSessionManager = scoped_session(SessionFactory)


@contextmanager
def get_db_session(max_retries: int = 3, backoff_factor: float = 0.5) -> Generator:
    """
    Context manager providing safe database session execution with connection retry logic.
    Ensures connection is returned to the pool properly upon completion.
    """
    session = ScopedSessionManager()
    retry_count = 0
    try:
        while True:
            try:
                yield session
                session.commit()
                break
            except (OperationalError, DBAPIError) as e:
                session.rollback()
                retry_count += 1
                if retry_count > max_retries:
                    logger.error(f"DB connection failed after {max_retries} retries: {str(e)}")
                    raise e
                sleep_time = backoff_factor * (2 ** (retry_count - 1))
                logger.warning(
                    f"DB OperationalError encountered. Retrying in {sleep_time}s... (Attempt {retry_count}/{max_retries})"
                )
                time.sleep(sleep_time)
            except Exception as e:
                session.rollback()
                logger.error(f"Unhandled exception during DB session: {str(e)}")
                raise e
    finally:
        ScopedSessionManager.remove()


def check_db_health() -> dict:
    """Health check endpoint to verify pool status and primary connection status."""
    try:
        pool_status = {
            "size": engine.pool.size(),
            "checkedin": engine.pool.checkedin(),
            "overflow": engine.pool.overflow(),
            "checkedout": engine.pool.checkedout(),
        }
        with get_db_session() as session:
            session.execute(sqlalchemy.text("SELECT 1"))
        return {"status": "healthy", "pool": pool_status}
    except Exception as e:
        logger.critical(f"DB health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}
