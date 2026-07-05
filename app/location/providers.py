from typing import Protocol


class GeocoderProvider(Protocol):
    def geocode(self, address: str) -> dict: ...
    def reverse_geocode(self, lat: float, lng: float) -> dict: ...


class MockNominatimProvider:
    def geocode(self, address: str) -> dict:
        return {"address": address, "latitude": 28.6139, "longitude": 77.2090}

    def reverse_geocode(self, lat: float, lng: float) -> dict:
        return {"address": f"Approximate location near {lat},{lng}", "latitude": lat, "longitude": lng}
