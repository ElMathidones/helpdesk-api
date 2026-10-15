from collections import defaultdict, deque
from math import ceil
from threading import Lock
from time import monotonic


class FailedAttemptRateLimiter:
    def __init__(
        self,
        *,
        max_attempts: int,
        window_seconds: int,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def get_retry_after(self, key: str) -> int | None:
        now = monotonic()

        with self._lock:
            attempts = self._attempts[key]
            self._remove_expired(attempts, now)

            if len(attempts) < self.max_attempts:
                return None

            remaining = self.window_seconds - (now - attempts[0])

            return max(1, ceil(remaining))

    def register_failure(self, key: str) -> None:
        now = monotonic()

        with self._lock:
            attempts = self._attempts[key]
            self._remove_expired(attempts, now)
            attempts.append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def _remove_expired(
        self,
        attempts: deque[float],
        now: float,
    ) -> None:
        while attempts and now - attempts[0] >= self.window_seconds:
            attempts.popleft()


class RequestRateLimiter:
    def __init__(
        self,
        *,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def consume(self, key: str) -> int | None:
        now = monotonic()

        with self._lock:
            requests = self._requests[key]

            while requests and now - requests[0] >= self.window_seconds:
                requests.popleft()

            if len(requests) >= self.max_requests:
                remaining = self.window_seconds - (now - requests[0])

                return max(1, ceil(remaining))

            requests.append(now)

        return None

    def reset(self, key: str) -> None:
        with self._lock:
            self._requests.pop(key, None)
