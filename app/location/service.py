from app.core.config import settings
from app.location.providers import NominatimProvider


def get_provider():
    if settings.map_geocoder_provider == "nominatim":
        return NominatimProvider()
    return NominatimProvider()
