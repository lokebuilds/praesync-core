import time
import logging
import random

logger = logging.getLogger("auth_db_primary")

def connect_with_retry(connect_fn, max_retries=5, base_delay=1.0, max_delay=30.0):
    """
    Establishes a connection to auth-db-primary using exponential backoff with jitter.
    Remediates Sev-1 database connection timeouts under burst traffic.
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Connecting to auth-db-primary (attempt {attempt}/{max_retries})...")
            conn = connect_fn()
            logger.info("Successfully established connection to auth-db-primary.")
            return conn
        except Exception as err:
            if attempt == max_retries:
                logger.error(f"Exhausted all {max_retries} connection attempts to auth-db-primary: {err}")
                raise err
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter = random.uniform(0, 0.1 * delay)
            total_delay = delay + jitter
            logger.warning(f"Database connection attempt {attempt} failed ({err}). Retrying in {total_delay:.2f}s...")
            time.sleep(total_delay)
