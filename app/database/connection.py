import logging
import time
import random
import os
import psycopg2
from psycopg2 import OperationalError

logger = logging.getLogger("auth_db_primary_hotfix")
logging.basicConfig(level=logging.INFO)

DB_URI = os.getenv("AUTH_DB_PRIMARY_URL", "postgresql://auth_user:auth_pass@auth-db-primary:5432/auth_db")
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 32.0     # seconds
CONNECT_TIMEOUT = 10   # seconds

def get_db_connection(db_uri=DB_URI, max_retries=MAX_RETRIES):
    """
    Establishes connection to auth-db-primary with exponential backoff retry logic.
    Remediates Sev-1 DB connection timeouts.
    """
    attempt = 0

    while attempt < max_retries:
        attempt += 1
        try:
            logger.info(f"Connecting to auth-db-primary (Attempt {attempt}/{max_retries})...")
            conn = psycopg2.connect(db_uri, connect_timeout=CONNECT_TIMEOUT)
            logger.info("Successfully connected to auth-db-primary.")
            return conn
        except OperationalError as e:
            logger.warning(f"Connection attempt {attempt} failed: {e}")
            if attempt == max_retries:
                logger.error("Max connection retries reached for auth-db-primary.")
                raise e
            
            # Exponential backoff with full jitter
            sleep_time = min(MAX_BACKOFF, INITIAL_BACKOFF * (2 ** (attempt - 1)))
            jittered_sleep = random.uniform(0, sleep_time)
            logger.info(f"Retrying in {jittered_sleep:.2f} seconds...")
            time.sleep(jittered_sleep)

if __name__ == "__main__":
    conn = get_db_connection()
    conn.close()
