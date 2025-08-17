import threading
from datetime import timedelta
from django.utils import timezone
from .enums import Seconds


class CacheCircuitBreaker:
    """
        Circuit breaker for cache operations that prevents cascading failures.
        
        When cache (Redis) is down or experiencing issues, this circuit breaker:
        1. Detects failures through consecutive error tracking
        2. "Opens" the circuit to block cache operations and prevent timeouts
        3. Allows periodic test requests to check if cache has recovered
        4. "Closes" the circuit when cache is healthy again
        
        This is implemented as a singleton because cache health is service-wide state.
        All cache clients within a single service should share the same circuit breaker
        to ensure consistent behavior - if cache is down for one operation, it's down
        for all operations in that service.
        
        Each microservice gets its own singleton instance (isolated between services),
        but all cache operations within a service share the same health tracking.
        
        Usage:
            circuit_breaker = CacheCircuitBreaker()  # Always returns same instance
            if circuit_breaker.should_allow_request():
                try:
                    result = cache.get(key)
                    circuit_breaker.record_success()
                except Exception:
                    circuit_breaker.record_failure()
                    # Fall back to DB or return None
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Prevent re-initialization of singleton
        if hasattr(self, '_initialized'):
            return
        
        self._lock = threading.Lock()
        self.consecutive_failures = 0
        self.failure_threshold = 3
        self.circuit_open = False  # Start closed (normal operation)
        self.last_failure_time = None
        self.retry_timeout = timedelta(seconds=Seconds.MINUTE_HALF.value)  # 30 seconds
        self._initialized = True
    
    @property
    def allow_request(self) -> bool:
        if not self.circuit_open:
            return True
        return self._should_attempt_retry()
    
    def fail(self):
        """Record a cache operation failure"""
        with self._lock:
            self.consecutive_failures += 1
            self.last_failure_time = timezone.now()
            
            if self.consecutive_failures >= self.failure_threshold:
                self._open_circuit()
    
    def success(self):
        """Record a successful cache operation"""
        with self._lock:
            self.consecutive_failures = 0
            if self.circuit_open:
                self._close_circuit()
    
    def _open_circuit(self):
        """Open the circuit (block cache operations)"""
        self.circuit_open = True
    
    def _close_circuit(self):
        """Close the circuit (allow cache operations)"""
        self.consecutive_failures = 0
        self.last_failure_time = None
        self.circuit_open = False
    
    def _should_attempt_retry(self) -> bool:
        """Check if enough time has passed to attempt a retry"""
        if not self.last_failure_time:
            return True
        
        elapsed = timezone.now() - self.last_failure_time
        return elapsed >= self.retry_timeout