from ..enums import StreetNinjaEnum


class RedisStoreEnum(StreetNinjaEnum):
    DEFAULT = "default"
    SESSION = "session"
    PHONE_SESSION = "phone_session"
    RESOURCES = "resources"
    CELERY = "celery"
    GEO = "geo"
    TESTS = "tests"
    GATE = "gate"


class RedisKeyEnum(StreetNinjaEnum): 
    ...


class RedisKeyTTL(StreetNinjaEnum):
    """TTL for resource data in redis cache in seconds"""

    # TWENTY_SECONDS = 20  # for testing purposes
    MINUTE = 60
    MINUTES_FIFTEEN = 900
    MINUTES_THIRTY = 1800
    HOUR = 3600
    HOURS_FOUR = 14400
    DAY = 86400
