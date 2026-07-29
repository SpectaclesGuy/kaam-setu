from collections import deque
from threading import Lock
from time import monotonic, sleep
from typing import Protocol

import httpx

from app.core.config import settings


class GeocoderProvider(Protocol):
    def geocode(self, address: str) -> dict: ...
    def reverse_geocode(self, lat: float, lng: float) -> dict: ...


class RateLimiter:
    def __init__(self, rate_per_minute: int = 30):
        self.rate_per_minute = rate_per_minute
        self.events: deque[float] = deque()
        self.lock = Lock()

    def acquire(self):
        while True:
            with self.lock:
                now = monotonic()
                while self.events and now - self.events[0] > 60:
                    self.events.popleft()
                if len(self.events) < self.rate_per_minute:
                    self.events.append(now)
                    return
                wait_time = 60 - (now - self.events[0])
            sleep(max(wait_time, 0.2))


class NominatimProvider:
    def __init__(self):
        self.base_url = settings.nominatim_base_url.rstrip("/")
        self.headers = {"User-Agent": "KaamSetu/1.0 contact@example.com"}
        self.limiter = RateLimiter(rate_per_minute=20)

    def geocode(self, address: str) -> dict:
        self.limiter.acquire()
        with httpx.Client(timeout=10.0, headers=self.headers) as client:
            response = client.get(
                f"{self.base_url}/search",
                params={"q": address, "format": "jsonv2", "limit": 1},
            )
            response.raise_for_status()
            results = response.json()
            if not results:
                return {"address": address, "latitude": None, "longitude": None}
            top = results[0]
            return {
                "address": top.get("display_name", address),
                "latitude": float(top["lat"]),
                "longitude": float(top["lon"]),
            }

    def reverse_geocode(self, lat: float, lng: float) -> dict:
        self.limiter.acquire()
        with httpx.Client(timeout=10.0, headers=self.headers) as client:
            response = client.get(
                f"{self.base_url}/reverse",
                params={"lat": lat, "lon": lng, "format": "jsonv2"},
            )
            response.raise_for_status()
            payload = response.json()
            return {
                "address": payload.get("display_name", f"{lat},{lng}"),
                "latitude": lat,
                "longitude": lng,
            }
