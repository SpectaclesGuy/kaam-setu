from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.bookings.models import Booking
from app.contact_logs import ContactLog
from app.contractor.models import SavedWorker
from app.core.config import settings
from app.core.database import Base
from app.disputes.models import Dispute
from app.notifications.models import Notification
from app.profiles.models import (
    Category,
    ContractorProfile,
    EmployerProfile,
    OperatorProfile,
    WorkerAvailability,
    WorkerLanguage,
    WorkerProfile,
    WorkerSkill,
)
from app.reviews.models import Review
from app.users.models import User
from app.verification.models import VerificationDocument
from app.work_requests.models import WorkRequest, WorkRequestApplication

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
