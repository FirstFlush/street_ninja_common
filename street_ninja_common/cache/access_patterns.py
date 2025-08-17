from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Type
from .enums import CacheStoreEnum, Seconds, CacheKey


@dataclass(frozen=True)
class BaseCacheAccessPattern(ABC):

    store: CacheStoreEnum
    ttl: Seconds
    _key_enum: CacheKey
    value_type: Type[Any]
    version: int = field(default=1, init=False)

    @abstractmethod
    def key(self, **kwargs) -> str:
        pass


@dataclass(frozen=True)
class AccessPatternDB(BaseCacheAccessPattern):

    query: Callable
    params: dict[str, Any] = field(default_factory=dict)