import logging
from typing import TypeVar
from .base import BaseCacheClient
from ..enums import EncodingStrategy
from ..access_patterns import BaseCacheAccessPattern

T = TypeVar("T")
logger = logging.getLogger(__name__)

class CacheClient(BaseCacheClient[T]):
    """
    General-purpose cache client for non-database cached data.
    
    This client handles caching of computed values, API responses, user sessions,
    feature flags, and other data that doesn't originate from database queries.
    Uses JSON serialization for broad compatibility and human-readable cache values.
    
    Key characteristics:
    - JSON encoding only (for compatibility and debugging)
    - No fallback data source - if cache fails, operations return None
    - Suitable for: user preferences, API responses, computed results, sessions
    - Not suitable for: database query results (use CacheClientDB instead)
    
    The client integrates with a circuit breaker to fail fast when cache is down,
    preventing timeout delays and providing clear "cache unavailable" signals
    rather than hanging operations.
    """
    def get(self, access_pattern: BaseCacheAccessPattern, **kwargs) -> T | None:
        if self.circuit_breaker.allow_request:
            cached_data = self._get(access_pattern, **kwargs)
            if cached_data is not None:
                return self._decode(cached_data, EncodingStrategy.JSON)
        else:
            logger.critical("Cache circuit breaker open. Can not read from cache")
        return None

    def set(self, value: T, access_pattern: BaseCacheAccessPattern, **kwargs):
        self._set(
            value=value,
            access_pattern=access_pattern,
            encoding_strategy=EncodingStrategy.JSON,
            **kwargs
        )
