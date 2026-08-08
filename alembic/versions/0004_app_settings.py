"""add app settings table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0004_app_settings"
down_revision = "0003_worker_gallery_urls"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "app_settings" not in tables:
        op.create_table(
            "app_settings",
            sa.Column("key", sa.String(length=100), primary_key=True),
            sa.Column("value", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "app_settings" in tables:
        op.drop_table("app_settings")
