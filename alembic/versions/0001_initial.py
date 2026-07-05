"""initial schema"""

from alembic import op

from app.core.database import Base
from app.users import models  # noqa: F401
from app.profiles import models as profile_models  # noqa: F401
from app.work_requests import models as work_request_models  # noqa: F401
from app.bookings import models as booking_models  # noqa: F401
from app.reviews import models as review_models  # noqa: F401
from app.verification import models as verification_models  # noqa: F401
from app.contractor import models as contractor_models  # noqa: F401
from app.disputes import models as dispute_models  # noqa: F401
from app.notifications import models as notification_models  # noqa: F401
from app.contact_logs import ContactLog  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
