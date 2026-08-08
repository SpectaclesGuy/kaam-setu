"""add worker aadhaar number"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0005_worker_kyc_fields"
down_revision = "0004_app_settings"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("worker_profiles")}
    if "aadhaar_number" not in columns:
        op.add_column("worker_profiles", sa.Column("aadhaar_number", sa.String(length=20), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("worker_profiles")}
    if "aadhaar_number" in columns:
        op.drop_column("worker_profiles", "aadhaar_number")
