from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.admin.router import router as admin_router
from app.auth.router import router as auth_router
from app.bookings.router import router as bookings_router
from app.common.utils import api_response
from app.contact_router import router as contact_router
from app.contractor.router import router as contractor_router
from app.core.config import settings
from app.core.database import Base, engine, ping_database
from app.disputes.router import router as disputes_router
from app.location.router import router as location_router
from app.notifications.router import router as notifications_router
from app.operator.router import router as operator_router
from app.profiles.router import router as profiles_router
from app.reviews.router import router as reviews_router
from app.users.models import User  # noqa: F401
from app.verification.router import router as verification_router
from app.verification.models import VerificationDocument  # noqa: F401
from app.bookings.models import Booking  # noqa: F401
from app.profiles.models import (  # noqa: F401
    Category,
    ContractorProfile,
    EmployerProfile,
    OperatorProfile,
    WorkerAvailability,
    WorkerLanguage,
    WorkerProfile,
    WorkerSkill,
)
from app.contractor.models import SavedWorker  # noqa: F401
from app.disputes.models import Dispute  # noqa: F401
from app.notifications.models import Notification  # noqa: F401
from app.reviews.models import Review  # noqa: F401
from app.work_requests.models import WorkRequest, WorkRequestApplication  # noqa: F401
from app.work_requests.router import router as work_requests_router
from app.workers.router import router as workers_router

BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(workers_router)
app.include_router(location_router)
app.include_router(work_requests_router)
app.include_router(bookings_router)
app.include_router(reviews_router)
app.include_router(verification_router)
app.include_router(contact_router)
app.include_router(operator_router)
app.include_router(contractor_router)
app.include_router(admin_router)
app.include_router(disputes_router)
app.include_router(notifications_router)


@app.get("/health")
def health():
    return api_response(
        message="KaamSetu API is healthy",
        data={"database": "up" if ping_database() else "down"},
    )


@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse(BASE_DIR / "homepage.html")


@app.get("/find-workers", include_in_schema=False)
def find_workers_page():
    return FileResponse(BASE_DIR / "find_workers.html")


@app.get("/worker-profile", include_in_schema=False)
def worker_profile_page():
    return FileResponse(BASE_DIR / "worker_profile.html")


@app.get("/workers/{worker_id}", include_in_schema=False)
def worker_profile_detail_page(worker_id: str):
    return FileResponse(BASE_DIR / "worker_profile.html")
