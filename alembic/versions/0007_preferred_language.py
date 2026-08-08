"""add preferred language to users

Revision ID: 0007_preferred_language
Revises: 0006_work_request_time
Create Date: 2026-08-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_preferred_language"
down_revision = "0006_work_request_time"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("preferred_language", sa.String(length=10), nullable=False, server_default="en"))


def downgrade() -> None:
    op.drop_column("users", "preferred_language")
