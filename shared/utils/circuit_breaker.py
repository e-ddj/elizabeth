import time
import threading
from functools import wraps
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for fault tolerance.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Requests fail immediately without calling the function
    - HALF_OPEN: Allow one request to test if service recovered
    """
    
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        name: Optional[str] = None
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name or "CircuitBreaker"
        
        self._failure_count = 0
        self._last_failure_time = None
        self._state = self.CLOSED
        self._lock = threading.Lock()
        
    @property
    def state(self) -> str:
        with self._lock:
            if self._state == self.OPEN and self._should_attempt_reset():
                self._state = self.HALF_OPEN
            return self._state
    
    @property
    def failure_count(self) -> int:
        return self._failure_count
    
    @property
    def is_closed(self) -> bool:
        return self.state == self.CLOSED
    
    @property
    def is_open(self) -> bool:
        return self.state == self.OPEN
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker to a function"""
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return self.call(func, *args, **kwargs)
        
        # Store circuit breaker instance on function for testing
        wrapper.circuit_breaker = self
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        # Check if circuit is open
        if self.is_open:
            raise CircuitBreakerError(
                f"Circuit breaker {self.name} is OPEN. "
                f"Service unavailable for {self.recovery_timeout}s"
            )
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Success - update state
            self._on_success()
            return result
            
        except self.expected_exception as e:
            # Expected failure - update state
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to try resetting"""
        return (
            self._last_failure_time is not None and
            time.time() - self._last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            self._failure_count = 0
            self._state = self.CLOSED
            logger.info(f"Circuit breaker {self.name} is CLOSED")
    
    def _on_failure(self):
        """Handle failed call"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._failure_count >= self.failure_threshold:
                self._state = self.OPEN
                logger.warning(
                    f"Circuit breaker {self.name} is OPEN after "
                    f"{self._failure_count} failures"
                )
    
    def reset(self):
        """Manually reset the circuit breaker"""
        with self._lock:
            self._failure_count = 0
            self._last_failure_time = None
            self._state = self.CLOSED
            logger.info(f"Circuit breaker {self.name} manually reset")
    
    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self._last_failure_time
        }


# Convenience decorators for common use cases
def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception,
    name: Optional[str] = None
):
    """
    Decorator factory for circuit breaker
    
    Example:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30)
        def call_external_api():
            # Make API call
            pass
    """
    def decorator(func: Callable) -> Callable:
        cb = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=name or func.__name__
        )
        return cb(func)
    
    return decorator