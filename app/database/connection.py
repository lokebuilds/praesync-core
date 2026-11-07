import os
import signal
import sys
import logging
from contextlib import contextmanager
import redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", 50))

# Instantiate a single shared ConnectionPool per worker process to prevent connection duplication
connection_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    max_connections=REDIS_MAX_CONNECTIONS,
    decode_responses=True
)

@contextmanager
def get_redis_client():
    """
    Context manager to safely handle Redis client connections from the pool.
    Guarantees client connection closure and release back to the pool upon exit or exception.
    """
    client = redis.Redis(connection_pool=connection_pool)
    try:
        yield client
    finally:
        client.close()

def shutdown_handler(signum, frame):
    logger.info(f"Received signal {signum}. Gracefully disconnecting Redis connection pool...")
    try:
        connection_pool.disconnect()
    except Exception as e:
        logger.error(f"Error disconnecting Redis pool during shutdown: {e}")
    sys.exit(0)

def process_task(task_data):
    with get_redis_client() as r:
        logger.info(f"Processing task: {task_data}")
        r.ping()
        r.lpush("completed_tasks", str(task_data))

def worker_loop():
    logger.info("Worker loop initialized.")
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    while True:
        try:
            with get_redis_client() as r:
                item = r.blpop("job_queue", timeout=5)
                if item:
                    _, task_data = item
                    process_task(task_data)
        except redis.RedisError as e:
            logger.error(f"Redis operational error: {e}")
        except Exception as e:
            logger.error(f"Unexpected worker error: {e}")

if __name__ == "__main__":
    worker_loop()
