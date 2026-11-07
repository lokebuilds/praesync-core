import os
import time
import logging
import psycopg2
from psycopg2 import OperationalError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth_db_patcher")

MAX_RETRIES = int(os.getenv("DB_MAX_RETRIES", "5"))
INITIAL_BACKOFF = float(os.getenv("DB_INITIAL_BACKOFF", "1.0"))
BACKOFF_FACTOR = float(os.getenv("DB_BACKOFF_FACTOR", "2.0"))
CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))

def get_db_connection(dsn: str = None):
    """
    Establishes a resilient database connection to auth-db-primary with exponential backoff retries.
    Mitigates transient Sev-1 DB connection timeouts.
    """
    if not dsn:
        dsn = os.getenv(
            "AUTH_DB_DSN",
            "host=auth-db-primary port=5432 dbname=auth user=auth_user connect_timeout=" + str(CONNECT_TIMEOUT)
        )

    backoff = INITIAL_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Attempting connection to auth-db-primary (Attempt %d/%d)...", attempt, MAX_RETRIES)
            conn = psycopg2.connect(dsn, connect_timeout=CONNECT_TIMEOUT)
            logger.info("Successfully established connection to auth-db-primary.")
            return conn
        except (OperationalError, Exception) as exc:
            logger.warning("Connection attempt %d to auth-db-primary failed: %s", attempt, exc)
            if attempt == MAX_RETRIES:
                logger.error("Exhausted all %d connection attempts to auth-db-primary.", MAX_RETRIES)
                raise exc
            logger.info("Retrying connection in %.2f seconds...", backoff)
            time.sleep(backoff)
            backoff *= BACKOFF_FACTOR
