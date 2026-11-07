import time
import logging
import psycopg2
from psycopg2 import OperationalError

logger = logging.getLogger(__name__)

def connect_with_retry(db_config, max_retries=5, initial_backoff=1.0, backoff_factor=2.0):
    """
    Establishes a connection to auth-db-primary with exponential backoff retry logic
    and configured TCP keepalives to remediate Sev-1 connection timeouts.
    """
    retries = 0
    backoff = initial_backoff
    
    while True:
        try:
            logger.info(f"Attempting connection to auth-db-primary (attempt {retries + 1}/{max_retries})...")
            conn = psycopg2.connect(
                dbname=db_config.get("dbname"),
                user=db_config.get("user"),
                password=db_config.get("password"),
                host=db_config.get("host"),
                port=db_config.get("port"),
                connect_timeout=db_config.get("connect_timeout", 10),
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            logger.info("Successfully connected to auth-db-primary.")
            return conn
        except OperationalError as err:
            retries += 1
            if retries >= max_retries:
                logger.error(f"Failed to connect to auth-db-primary after {max_retries} attempts: {err}")
                raise err
            
            logger.warning(f"Connection failed: {err}. Retrying in {backoff:.2f}s...")
            time.sleep(backoff)
            backoff *= backoff_factor
