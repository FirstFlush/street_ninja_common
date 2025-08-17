from ..enums import StreetNinjaEnum


# class BaseStoreEnum(StreetNinjaEnum):
#     TESTS = "tests"



class CacheStoreEnum(StreetNinjaEnum):
    DEFAULT = "default"
    SESSION = "session"
    PHONE_SESSION = "phone_session"
    RESOURCES = "resources"
    CELERY = "celery"
    GEO = "geo"
    TESTS = "tests"
    GATE = "gate"


class CacheKey(StreetNinjaEnum):
    ...


class Seconds(StreetNinjaEnum):
    """TTL for resource data in redis cache in seconds"""
   
    MINUTE_HALF = 30
    MINUTE = 60
    MINUTES_FIFTEEN = 60 * 15
    MINUTES_THIRTY = 60 * 30
    HOUR = 60 * 60
    HOURS_TWO = 60 * 60 * 2
    HOURS_FOUR = 60 * 60 * 4
    HOURS_SIX = 60 * 60 * 6
    HOURS_EIGHT = 60 * 60 * 8
    HOURS_TWELVE = 60 * 60 * 12
    DAY = 60 * 60 * 24
    DAYS_THREE = 60 * 60 * 24 * 3
    WEEK = 60 * 60 * 24 * 7
    DAYS_THIRTY = 60 * 60 * 24 * 30
    DAYS_NINETY = 60 * 60 * 24 * 90
    

class EncodingStrategy(StreetNinjaEnum):
    
    JSON = "json"
    PICKLE = "pickle"