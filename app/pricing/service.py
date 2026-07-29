from collections import defaultdict
from math import ceil

from sqlalchemy.orm import Session

from app.pricing.models import PricingInsight
from app.profiles.models import WorkerProfile


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def normalize_city(location_text: str | None) -> str:
    raw = (location_text or "").split(",")[0].strip()
    return raw.title() if raw else "Unknown"


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, ceil((len(ordered) - 1) * fraction)))
    return round(float(ordered[index]), 2)


def confidence_from_sample(sample_size: int) -> float:
    return round(min(1.0, sample_size / 12), 2)


def build_live_pricing_rows(db: Session) -> list[dict]:
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    workers = db.query(WorkerProfile).all()
    for worker in workers:
        city = normalize_city(worker.location_text)
        skills = [normalize_text(skill.skill_name) for skill in worker.skills if skill.skill_name]
        unique_skills = [skill for skill in dict.fromkeys(skills) if skill]
        for skill in unique_skills:
            grouped[(skill, city, "daily")].append(float(worker.daily_rate))
            if worker.hourly_rate is not None:
                grouped[(skill, city, "hourly")].append(float(worker.hourly_rate))

    rows: list[dict] = []
    for (category_name, city, rate_type), values in grouped.items():
        if not values:
            continue
        ordered = sorted(values)
        rows.append(
            {
                "category_name": category_name,
                "city": city,
                "rate_type": rate_type,
                "suggested_min": percentile(ordered, 0.25),
                "suggested_median": percentile(ordered, 0.5),
                "suggested_max": percentile(ordered, 0.75),
                "sample_size": len(ordered),
                "confidence_score": confidence_from_sample(len(ordered)),
            }
        )
    return rows


def refresh_pricing_insights(db: Session) -> int:
    rows = build_live_pricing_rows(db)
    db.query(PricingInsight).delete()
    for row in rows:
        db.add(PricingInsight(**row))
    db.commit()
    return len(rows)


def find_pricing_insight(db: Session, category: str, city: str, rate_type: str = "daily") -> dict | None:
    normalized_category = normalize_text(category)
    normalized_city = normalize_city(city)
    insight = (
        db.query(PricingInsight)
        .filter(
            PricingInsight.category_name == normalized_category,
            PricingInsight.city == normalized_city,
            PricingInsight.rate_type == rate_type,
        )
        .first()
    )
    if insight:
        return {
            "category_name": insight.category_name,
            "city": insight.city,
            "rate_type": insight.rate_type,
            "suggested_min": round(float(insight.suggested_min), 2),
            "suggested_median": round(float(insight.suggested_median), 2),
            "suggested_max": round(float(insight.suggested_max), 2),
            "sample_size": insight.sample_size,
            "confidence_score": round(float(insight.confidence_score), 2),
            "source": "cached",
        }

    live_rows = build_live_pricing_rows(db)
    for row in live_rows:
        if (
            row["category_name"] == normalized_category
            and row["city"] == normalized_city
            and row["rate_type"] == rate_type
        ):
            return {**row, "source": "live"}
    return None
