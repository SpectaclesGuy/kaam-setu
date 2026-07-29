from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db
from app.pricing.service import find_pricing_insight, refresh_pricing_insights

router = APIRouter(prefix="/pricing-insights", tags=["pricing"])


@router.get("")
def get_pricing_insight(
    category: str = Query(..., min_length=2),
    city: str = Query(..., min_length=2),
    rate_type: str = Query(default="daily"),
    db: Session = Depends(get_db),
):
    insight = find_pricing_insight(db, category=category, city=city, rate_type=rate_type)
    if not insight:
        raise HTTPException(status_code=404, detail="No pricing insight found for this category and city")
    return api_response("Pricing insight fetched", insight)


@router.post("/refresh")
def refresh_pricing(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    count = refresh_pricing_insights(db)
    return api_response("Pricing insights refreshed", {"records_refreshed": count})
