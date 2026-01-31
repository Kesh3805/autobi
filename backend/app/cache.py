"""
Simple in-memory caching for AutoBI.
Caches schema profiles and repeated queries.
"""

import time
import hashlib
from typing import Any, Dict, Optional, Callable
from functools import wraps
from threading import Lock


class Cache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry['expires_at'] > time.time():
                    self._hits += 1
                    return entry['value']
                else:
                    # Expired, remove it
                    del self._cache[key]
            self._misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache with TTL."""
        ttl = ttl or self._default_ttl
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
    
    def delete(self, key: str):
        """Delete a key from cache."""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys containing the pattern."""
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
    
    def cleanup_expired(self):
        """Remove all expired entries."""
        current_time = time.time()
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items() 
                if v['expires_at'] <= current_time
            ]
            for key in expired_keys:
                del self._cache[key]
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': f"{hit_rate:.1f}%"
            }


# Global cache instances
schema_cache = Cache(default_ttl=600)  # 10 minutes for schema
query_cache = Cache(default_ttl=120)   # 2 minutes for query results


def cached(cache: Cache, ttl: int = None, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Usage:
        @cached(schema_cache, ttl=300)
        def get_schema(table_name):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = key_prefix + cache._make_key(*args, **kwargs)
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        # Add cache control methods to wrapper
        wrapper.invalidate = lambda *args, **kwargs: cache.delete(
            key_prefix + cache._make_key(*args, **kwargs)
        )
        wrapper.clear_cache = lambda: cache.invalidate_pattern(key_prefix)
        
        return wrapper
    return decorator


def cache_schema(table_name: str, profile: Dict[str, Any]):
    """Cache a schema profile."""
    schema_cache.set(f"schema:{table_name}", profile)


def get_cached_schema(table_name: str) -> Optional[Dict[str, Any]]:
    """Get cached schema profile."""
    return schema_cache.get(f"schema:{table_name}")


def invalidate_table_cache(table_name: str):
    """Invalidate all cache entries for a table."""
    schema_cache.invalidate_pattern(table_name)
    query_cache.invalidate_pattern(table_name)


def cache_query_result(question: str, table: str, result: Dict[str, Any]):
    """Cache a query result."""
    key = f"query:{table}:{hashlib.md5(question.encode()).hexdigest()}"
    query_cache.set(key, result)


def get_cached_query(question: str, table: str) -> Optional[Dict[str, Any]]:
    """Get cached query result."""
    key = f"query:{table}:{hashlib.md5(question.encode()).hexdigest()}"
    return query_cache.get(key)
