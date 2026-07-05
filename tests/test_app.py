from app.core.security import create_access_token
from app.users.models import User


def test_health_route(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["database"] in {"up", "down"}


def test_auth_dependency_blocks_unauthenticated(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_role_based_access_for_admin_dashboard(client, db):
    user = User(email="user@test.com", full_name="Normal User", role="employer", profile_completed=True)
    db.add(user)
    db.commit()
    token = create_access_token(user.id)
    response = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_worker_search_returns_nearby_verified_worker(client, worker_user):
    response = client.get("/workers/search", params={"lat": 28.61, "lng": 77.21})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["full_name"] == "Ravi Worker"


def test_worker_distance_endpoint(client, worker_user):
    worker_id = worker_user.worker_profile.id
    response = client.get(f"/workers/{worker_id}/distance", params={"lat": 28.61, "lng": 77.21})
    assert response.status_code == 200
    assert response.json()["data"]["distance_km"] >= 0


def test_booking_creation(client, db, worker_user):
    employer = User(email="employer@test.com", full_name="Employer", role="employer", profile_completed=True)
    db.add(employer)
    db.commit()
    token = create_access_token(employer.id)
    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={"worker_id": worker_user.worker_profile.id, "scheduled_date": "2026-07-10"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "requested"


def test_review_creation_requires_completed_booking(client, db, worker_user):
    employer = User(email="employer2@test.com", full_name="Employer", role="employer", profile_completed=True)
    db.add(employer)
    db.commit()
    token = create_access_token(employer.id)
    booking_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={"worker_id": worker_user.worker_profile.id, "scheduled_date": "2026-07-10"},
    )
    booking_id = booking_response.json()["data"]["id"]
    review_response = client.post(
        "/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": booking_id, "reviewee_user_id": worker_user.id, "rating": 5, "comment": "Good work"},
    )
    assert review_response.status_code == 400


def test_admin_protected_route(client, db):
    admin = User(email="admin@test.com", full_name="Admin", role="admin", profile_completed=True)
    db.add(admin)
    db.commit()
    token = create_access_token(admin.id)
    response = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
