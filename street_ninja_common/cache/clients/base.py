from abc import ABC
import logging
from django.core.cache import caches
from django.core.cache.backends.base import BaseCache
from typing import cast, TypeVar, Generic
from ..circuit_breaker import CacheCircuitBreaker
from ..encoders import DataEncoder
from ..enums import EncodingStrategy
from ..exc import RedisClientException, InvalidAccessPattern
from ..access_patterns import BaseCacheAccessPattern


logger = logging.getLogger(__name__)
T = TypeVar("T")


class BaseCacheClient(ABC, Generic[T]):

    def __init__(self, circuit_breaker: CacheCircuitBreaker):
        self.circuit_breaker = circuit_breaker

    def _get(self, access_pattern: BaseCacheAccessPattern, **kwargs) -> bytes | None:
        
        store = self._store(access_pattern)
        key = self._key(access_pattern, **kwargs)
        try:
            cached_data = store.get(
               key=key,
               default=None,
               version=access_pattern.version,
            )
        except Exception as e:
            self.circuit_breaker.fail()
            msg = f"Unexpected error fetching cached data from store `{access_pattern.store.value}` with key `{key}`"
            logger.error(msg, exc_info=True)
            raise RedisClientException(msg) from e
        else:
            self.circuit_breaker.success()
            if cached_data is not None:
                logger.debug(f"Cache hit in store `{access_pattern.store.value}` with key `{key}`")
                return cached_data
            else:
                logger.debug(f"Cache miss in store `{access_pattern.store.value}` with key `{key}`")
                return None

    def _set(self, value: T, access_pattern: BaseCacheAccessPattern, encoding_strategy: EncodingStrategy, **kwargs): 
        
        store = self._store(access_pattern)
        key = self._key(access_pattern, **kwargs)
        try:
            store.set(
                key=key, 
                value=self._encode(value, encoding_strategy), 
                timeout=access_pattern.ttl.value, 
                version=access_pattern.version
            )
        except Exception as e:
            msg = f"Unexpected error setting cache store `{access_pattern.store.value}` with key `{key}`"
            logger.error(msg, exc_info=True)
            raise RedisClientException(msg) from e
        else:
            logger.debug(f"Successfully set cache store `{access_pattern.store.value}` with key `{key}`")
            
    def _encode(self, value: T, strategy: EncodingStrategy) -> bytes:
        match strategy:
            case EncodingStrategy.JSON:
                data = DataEncoder.serialize(value)
            case EncodingStrategy.PICKLE:
                data = DataEncoder.pickle(value)
            case _:
                msg = f"Invalid EncodingStrategy for encoding: `{strategy}`"
                logger.error(msg, exc_info=True)
                raise RedisClientException(msg)
            
        return data
    
    def _decode(self, data: bytes, strategy: EncodingStrategy) -> T:
        match strategy:
            case EncodingStrategy.JSON:
                result = DataEncoder.deserialize(data)
            case EncodingStrategy.PICKLE:
                result = DataEncoder.unpickle(data)
            case _:
                msg = f"Invalid EncodingStrategy for decoding: `{strategy}`"
                logger.error(msg, exc_info=True)
                raise RedisClientException(msg)
            
        return cast(T, result)

    def _store(self, access_pattern: BaseCacheAccessPattern) -> BaseCache:
        try:
            store = caches[access_pattern.store.value]
        except KeyError as e:
            msg = f"Invalid Redis store: `{access_pattern.store}`"
            logger.error(msg, exc_info=True)
            raise RedisClientException(msg) from e
        else:
            logger.debug(f"Valid redis store: {access_pattern.store}")
            return store
    
    def _key(self, access_pattern: BaseCacheAccessPattern, **kwargs) -> str:
        try:
            key = access_pattern.key(**kwargs)
        except TypeError as e:
            msg = f"{access_pattern.__class__.__name__} invalid key enum `{access_pattern._key_enum}` with kwargs `{kwargs}`"
            logger.error(msg, exc_info=True)
            raise InvalidAccessPattern(msg) from e
        else:
            logger.debug(f"{access_pattern.__class__.__name__} key is valid")
            return key