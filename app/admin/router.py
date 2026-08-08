from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.admin.schemas import AdminSettingsUpdate, AdminUserUpdate
from app.admin.service import (
    dashboard_metrics,
    delete_admin_user,
    list_admin_runtime_settings,
    list_admin_users,
    seed_categories,
    update_admin_runtime_settings,
    update_admin_user,
)
from app.bookings.models import Booking
from app.common.enums import UserRole
from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db, require_roles
from app.disputes.models import Dispute
from app.profiles.models import Category, EmployerProfile, WorkerProfile
from app.users.models import User
from app.verification.models import VerificationDocument
from app.work_requests.models import WorkRequest

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
def dashboard(user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    return api_response("Admin dashboard fetched", dashboard_metrics(db))


@router.get("/users")
def users(user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    return api_response("Users fetched", list_admin_users(db))


@router.get("/workers")
def workers(user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    return api_response("Workers fetched", [item.id for item in db.query(WorkerProfile).all()])


@router.get("/employers")
def employers(user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    return api_response("Employers fetched", [item.id for item in db.query(EmployerProfile).all()])


@router.get("/work-requests")
def work_requests(user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    return api_response("Work requests fetched", [item.id for item in db.query(WorkRequest).all()])


@router.get("/bookings")
def bookings(user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    return api_response("Bookings fetched", [item.id for item in db.query(Booking).all()])


@router.get("/disputes")
def disputes(user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    return api_response("Disputes fetched", [item.id for item in db.query(Dispute).all()])


@router.patch("/disputes/{dispute_id}")
def patch_dispute(dispute_id: str, user=Depends(require_roles(UserRole.admin))):
    return api_response("Use /disputes/admin/disputes/{id}/resolve instead", {"id": dispute_id})


@router.patch("/users/{user_id}/status")
def update_user_status(user_id: str, is_active: bool, user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.is_active = is_active
    db.commit()
    return api_response("User status updated", {"id": target.id, "is_active": target.is_active})


@router.patch("/users/{user_id}")
def patch_user(
    user_id: str,
    payload: AdminUserUpdate,
    user=Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    data = update_admin_user(
        db,
        target,
        role=payload.role,
        role_provided="role" in payload.model_fields_set,
        is_active=payload.is_active,
    )
    return api_response("User updated", data)


@router.delete("/users/{user_id}")
def remove_user(
    user_id: str,
    user=Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
):
    if user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own admin account from the admin panel.")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    delete_admin_user(db, target)
    return api_response("User deleted", {"id": user_id})


@router.get("/settings")
def admin_settings(user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    return api_response("Admin settings fetched", list_admin_runtime_settings(db))


@router.patch("/settings")
def patch_admin_settings(
    payload: AdminSettingsUpdate,
    user=Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
):
    data = update_admin_runtime_settings(
        db,
        profile_setup_require_email_verification=payload.profile_setup_require_email_verification,
        profile_setup_require_phone_verification=payload.profile_setup_require_phone_verification,
    )
    return api_response("Admin settings updated", data)


@router.get("/verification/pending")
def admin_pending_verification(user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    items = db.query(VerificationDocument).filter(VerificationDocument.status == "pending").all()
    return api_response("Pending verification fetched", [item.id for item in items])


@router.post("/categories")
def create_categories(names: list[str], user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)):
    seed_categories(db, names)
    return api_response("Categories created")


@router.patch("/categories/{category_id}")
def patch_category(
    category_id: str, name: str | None = None, is_active: bool | None = None, user=Depends(require_roles(UserRole.admin)), db: Session = Depends(get_db)
):
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if name is not None:
        category.name = name
        category.slug = name.lower().replace(" ", "-")
    if is_active is not None:
        category.is_active = is_active
    db.commit()
    return api_response("Category updated", {"id": category.id})
