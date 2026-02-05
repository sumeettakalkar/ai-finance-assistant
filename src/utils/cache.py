import time
from typing import Any

class TTLCache:
    def __init__(self, ttl: int=1800):
        self.ttl = ttl
        self._store : dict[str, tuple[Any, float]] = {}

    def set(self, key: str, value: Any):
        expiry = time.time() + self.ttl
        self._store[key] = (value, expiry)

    def get(self, key: str) -> Any:
        if key in self._store:
            value, expiry = self._store[key]
            if time.time() < expiry:
                return value
            else:
                del self._store[key]
        return None

    def clear(self):
        self._store.clear()
        