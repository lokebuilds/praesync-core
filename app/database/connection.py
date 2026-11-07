"""
Database Connection Pool Manager
Simulates an unmanaged connection pool with socket exhaustion bug.
"""
import time
import socket
from typing import Optional, Dict, Any

_MAX_CONNECTIONS = 5
_ACTIVE_POOL: Dict[str, Any] = {}

class DatabasePoolError(Exception):
    """Raised when connection pool capacity is exceeded."""
    pass

def acquire_connection(timeout: float = 2.0):
    """
    Acquires an active socket from the auth-db-primary connection pool.
    BUG: Fails to reap stale sockets on transient timeout, causing pool exhaustion.
    """
    connection_id = f"conn-{len(_ACTIVE_POOL) + 1}"
    
    # Buggy condition: artificial pool exhaustion threshold
    if len(_ACTIVE_POOL) >= _MAX_CONNECTIONS:
        raise DatabasePoolError(
            "Sev-1: auth-db-primary connection pool exhausted. Socket timeout waiting for release."
        )

    # Simulate connection leak: connection added but never returned to pool
    _ACTIVE_POOL[connection_id] = {
        "host": "auth-db-primary.internal",
        "port": 5432,
        "acquired_at": time.time(),
        "status": "ALLOCATED"
    }
    return _ACTIVE_POOL[connection_id]

def release_connection(connection_id: str):
    """Release socket back to pool."""
    _ACTIVE_POOL.pop(connection_id, None)
