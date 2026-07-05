from app.location.providers import MockNominatimProvider


def get_provider():
    return MockNominatimProvider()
