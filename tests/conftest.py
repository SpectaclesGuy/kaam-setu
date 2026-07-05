import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret"

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.profiles.models import WorkerProfile, WorkerSkill
from app.users.models import User


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_user(db):
    user = User(email="worker@test.com", full_name="Worker User")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def worker_user(db):
    user = User(email="ravi@test.com", full_name="Ravi Worker", role="worker", profile_completed=True, is_verified_user=True)
    db.add(user)
    db.flush()
    worker = WorkerProfile(
        user_id=user.id,
        phone_number="9999999999",
        location_text="Delhi",
        latitude=28.6139,
        longitude=77.2090,
        service_radius_km=20,
        experience_years=5,
        daily_rate=1000,
        available_today=True,
        emergency_available=True,
        verification_status="approved",
    )
    worker.skills = [WorkerSkill(skill_name="Electrician")]
    db.add(worker)
    db.commit()
    db.refresh(user)
    return user
