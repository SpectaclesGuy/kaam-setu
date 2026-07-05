from app.admin.service import seed_categories
from app.core.database import Base, SessionLocal, engine
from app.profiles.models import WorkerProfile, WorkerSkill
from app.users.models import User
from app.work_requests.models import WorkRequest


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_categories(
        db,
        [
            "Electrician",
            "Plumber",
            "Painter",
            "Carpenter",
            "Driver",
            "Mechanic",
            "Cleaner",
            "Farm Worker",
            "Construction Helper",
            "Loader",
            "Mason",
            "Shop Helper",
        ],
    )
    if not db.query(User).first():
        employer = User(email="employer@example.com", full_name="Demo Employer", role="employer", profile_completed=True)
        worker_user = User(
            email="worker@example.com",
            full_name="Ravi Electrician",
            role="worker",
            profile_completed=True,
            is_verified_user=True,
        )
        db.add_all([employer, worker_user])
        db.flush()
        worker = WorkerProfile(
            user_id=worker_user.id,
            phone_number="9999999999",
            location_text="Delhi",
            latitude=28.6139,
            longitude=77.2090,
            service_radius_km=15,
            experience_years=6,
            daily_rate=1200,
            available_today=True,
            emergency_available=True,
            verification_status="approved",
        )
        worker.skills = [WorkerSkill(skill_name="Electrician")]
        db.add(worker)
        db.flush()
        db.add(
            WorkRequest(
                posted_by_user_id=employer.id,
                title="Need an electrician for shop wiring",
                description="Urgent wiring repair",
                location_text="Delhi",
                latitude=28.61,
                longitude=77.21,
                date_required="2026-07-06",
                budget_min=1000,
                budget_max=1800,
                workers_needed=1,
            )
        )
        db.commit()
    db.close()


if __name__ == "__main__":
    run()
