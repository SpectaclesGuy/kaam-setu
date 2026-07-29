"""add worker gallery urls column"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0003_worker_gallery_urls"
down_revision = "0002_otp_pricing"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("worker_profiles")}
    if "work_gallery_urls" not in columns:
        op.add_column("worker_profiles", sa.Column("work_gallery_urls", sa.Text(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("worker_profiles")}
    if "work_gallery_urls" in columns:
        op.drop_column("worker_profiles", "work_gallery_urls")
