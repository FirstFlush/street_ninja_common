import json
import logging
import pickle
from typing import Any
from django.db.models import QuerySet
from .exc import RedisClientException


logger = logging.getLogger(__name__)


class DataEncoder:

    @staticmethod
    def serialize(value: Any) -> bytes:
        try:
            return json.dumps(value).encode('utf-8')    
        except TypeError as e:
            msg = f"Cannot serialize {type(value)} to JSON: {e}"
            logger.error(msg, exc_info=True)
            raise RedisClientException(msg) from e
        
    @staticmethod
    def deserialize(data: bytes) -> Any:
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            msg = f"Failed to deserialize cached data: {e}"
            logger.error(msg, exc_info=True)
            raise RedisClientException(msg) from e

    @classmethod
    def pickle(cls, data: Any) -> bytes:
        if isinstance(data, QuerySet):
            data = cls._qs_to_list(data)
        try:
            pickled_data = pickle.dumps(data)
        except Exception as e:
            msg = f"Unexpected error pickling data of type `{type(data)}`"
            logger.error(msg, exc_info=True)
            raise RedisClientException(msg) from e

        else:
            logger.debug(f"Successfully pickled data of type {type(data)}")
            return pickled_data

    # @staticmethod
    # def raw(data: Any) -> bytes:
    #     if isinstance(data, bytes):
    #         return data

    #     msg = f"Unexpected raw type. Expected bytes, got `{type(data)}`"
    #     logger.error(msg)
    #     raise RedisClientException(msg)

    @staticmethod
    def unpickle(data: bytes) -> Any:
        try:
            return pickle.loads(data)
        except Exception as e:
            msg = f"Unexpected error unpickling data of size `{len(data)}` bytes"
            logger.error(msg, exc_info=True)
            raise RedisClientException(msg) from e

    @staticmethod
    def _qs_to_list(qs: QuerySet) -> list:
        return [obj for obj in qs]

