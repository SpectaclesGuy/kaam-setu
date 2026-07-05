from fastapi import APIRouter, Query

from app.common.utils import api_response
from app.location.service import get_provider

router = APIRouter(prefix="/location", tags=["location"])


@router.get("/geocode")
def geocode(address: str = Query(..., min_length=3)):
    return api_response("Geocoded successfully", get_provider().geocode(address))


@router.get("/reverse-geocode")
def reverse_geocode(lat: float, lng: float):
    return api_response("Reverse geocoded successfully", get_provider().reverse_geocode(lat, lng))
