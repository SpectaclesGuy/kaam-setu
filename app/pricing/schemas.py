from pydantic import BaseModel, Field


class PricingInsightRead(BaseModel):
    category_name: str
    city: str
    rate_type: str
    suggested_min: float
    suggested_median: float
    suggested_max: float
    sample_size: int
    confidence_score: float
    source: str


class PricingRefreshResponse(BaseModel):
    records_refreshed: int = Field(ge=0)
