from math import asin, cos, radians, sin, sqrt
from typing import Any


def api_response(message: str, data: Any = None, success: bool = True) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data}


def error_response(message: str, error_code: str) -> dict[str, Any]:
    return {"success": False, "message": message, "error_code": error_code}


def haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return round(2 * radius * asin(sqrt(a)), 2)
