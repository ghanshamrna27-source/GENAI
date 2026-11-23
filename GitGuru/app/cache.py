"""
app/cache.py
In-memory LRU/TTL response cache for GitGuru.
Reduces inference latency, prevents repeated LLM API calls, and minimizes token spend.
"""

import time
import threading
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict


class SimpleResponseCache:
    """
    Thread-safe in-memory LRU cache with TTL support and observability tracking.
    """

    def __init__(self, max_size: int = 500, default_ttl_seconds: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        self._cache: OrderedDict[str, Tuple[Any, float, int]] = OrderedDict()  # key -> (data, expire_at, tokens)
        self._lock = threading.Lock()

        # Observability metrics
        self._hits = 0
        self._misses = 0
        self._tokens_saved = 0

    def _normalize_key(self, key: str) -> str:
        """Normalizes cache key (lowercase, stripped, collapsed spaces)."""
        return " ".join(key.strip().lower().split())

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves an item from the cache if present and not expired.
        Updates LRU ordering and metrics.
        """
        norm_key = self._normalize_key(key)
        now = time.time()

        with self._lock:
            if norm_key not in self._cache:
                self._misses += 1
                return None

            data, expire_at, tokens = self._cache[norm_key]

            # Check expiration
            if now > expire_at:
                del self._cache[norm_key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(norm_key)
            self._hits += 1
            self._tokens_saved += tokens
            return data

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, estimated_tokens: int = 0) -> None:
        """
        Stores an item in the cache with a specified or default TTL.
        Evicts oldest entry if max_size is reached.
        """
        norm_key = self._normalize_key(key)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expire_at = time.time() + ttl

        with self._lock:
            # If already present, update and move to end
            if norm_key in self._cache:
                self._cache.move_to_end(norm_key)
            elif len(self._cache) >= self.max_size:
                # Evict least recently used (first item)
                self._cache.popitem(last=False)

            self._cache[norm_key] = (value, expire_at, estimated_tokens)

    def clear(self) -> None:
        """Flushes the cache."""
        with self._lock:
            self._cache.clear()

    def stats(self) -> Dict[str, Any]:
        """Returns cache telemetry and performance statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100.0) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "total_lookups": total,
                "hit_rate_percent": round(hit_rate, 2),
                "tokens_saved": self._tokens_saved,
            }


# Global singleton cache instance
GLOBAL_CACHE = SimpleResponseCache(max_size=500, default_ttl_seconds=3600)
