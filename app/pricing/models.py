from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin


class PricingInsight(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "pricing_insights"

    category_name: Mapped[str] = mapped_column(String(100), index=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    rate_type: Mapped[str] = mapped_column(String(20), index=True)
    suggested_min: Mapped[float] = mapped_column(Float)
    suggested_median: Mapped[float] = mapped_column(Float)
    suggested_max: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0)
