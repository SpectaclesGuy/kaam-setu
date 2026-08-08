"""add time_required to work requests

Revision ID: 0006_work_request_time
Revises: 0005_worker_kyc_fields
Create Date: 2026-08-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_work_request_time"
down_revision = "0005_worker_kyc_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("work_requests", sa.Column("time_required", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("work_requests", "time_required")
