import logging
from typing import  TypeVar
from ..enums import EncodingStrategy
from ..exc import RedisClientException
from .base import BaseCacheClient
from ..access_patterns import AccessPatternDB

logger = logging.getLogger(__name__)
T = TypeVar("T")

class CacheClientDB(BaseCacheClient[T]):
    """
    Database-aware cache client implementing read-through caching pattern.
    
    This client specializes in caching database query results with automatic
    fallback to database queries when cache misses occur. Uses pickle serialization
    to preserve complex Python objects including Django model instances.
    
    Key characteristics:
    - Pickle encoding for full Python object preservation
    - Read-through pattern: cache miss automatically triggers DB query
    - Automatic QuerySet evaluation to prevent lazy loading issues (converts to list)
    - Circuit breaker integration for graceful cache failure handling
    - Guaranteed data availability: always returns data (cache or DB)

    The client provides resilience during cache outages by transparently falling
    back to database-only operation, ensuring application functionality is maintained
    even when Redis is unavailable.
    """
    def get(self, access_pattern: AccessPatternDB, **kwargs) -> T:
        if self.circuit_breaker.allow_request:
            cached_data = self._get_from_cache(access_pattern, **kwargs)
            if cached_data is None:
                self._set_from_db(access_pattern, **kwargs)
                cached_data = self._get_from_cache(access_pattern, **kwargs)
                if cached_data is None:
                    msg = f"Read-through cache lookup failed with AccessPattern `{access_pattern.__class__.__name__}`"
                    logger.error(msg)
                    raise RedisClientException(msg)
        else:
            logger.warning("Cache circuit breaker open, bypassing cache")
            cached_data = self._get_from_db(access_pattern)

        return cached_data

    def _get_from_db(self, access_pattern: AccessPatternDB) -> T:
        try:
            db_data = access_pattern.query(**access_pattern.params)
        except Exception as e:
            msg = f"Unexpected error when querying DB with AccessPattern `{access_pattern.__class__.__name__}`"
            logger.error(msg, exc_info=True)
            raise RedisClientException(msg) from e
        else:
            logger.debug(f"Successfully queried DB with AccessPattern `{access_pattern.__class__.__name__}`")
        return db_data

    def _set_from_db(self, access_pattern: AccessPatternDB, **kwargs):
        db_data = self._get_from_db(access_pattern)
        self._set(
            value=db_data,
            access_pattern=access_pattern,
            encoding_strategy=EncodingStrategy.PICKLE,
            **kwargs
        )

    def _get_from_cache(self, access_pattern, **kwargs) -> T | None:
        cached_data = self._get(access_pattern, **kwargs)
        if cached_data is not None:
            return self._decode(cached_data, EncodingStrategy.PICKLE)
        return None