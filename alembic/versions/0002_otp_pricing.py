"""add otp and pricing support"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0002_otp_pricing"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    def has_column(table_name: str, column_name: str) -> bool:
        return column_name in {column["name"] for column in inspector.get_columns(table_name)}

    def has_index(table_name: str, index_name: str) -> bool:
        return index_name in {index["name"] for index in inspector.get_indexes(table_name)}

    if not has_column("users", "phone_number"):
        op.add_column("users", sa.Column("phone_number", sa.String(length=20), nullable=True))
    if not has_column("users", "is_phone_verified"):
        op.add_column("users", sa.Column("is_phone_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    if not has_column("users", "phone_verified_at"):
        op.add_column("users", sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=True))

    if not has_column("bookings", "service_started_at"):
        op.add_column("bookings", sa.Column("service_started_at", sa.DateTime(timezone=True), nullable=True))
    if not has_column("bookings", "service_start_verified"):
        op.add_column(
            "bookings",
            sa.Column("service_start_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if not has_column("bookings", "service_start_verified_at"):
        op.add_column("bookings", sa.Column("service_start_verified_at", sa.DateTime(timezone=True), nullable=True))

    if not has_column("work_requests", "category_label"):
        op.add_column("work_requests", sa.Column("category_label", sa.String(length=100), nullable=True))

    if not inspector.has_table("otp_challenges"):
        op.create_table(
            "otp_challenges",
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("booking_id", sa.String(), nullable=True),
            sa.Column("phone_number", sa.String(length=20), nullable=False),
            sa.Column("purpose", sa.String(length=50), nullable=False),
            sa.Column("provider", sa.String(length=50), nullable=False),
            sa.Column("provider_reference", sa.String(length=255), nullable=True),
            sa.Column("verification_code", sa.String(length=20), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("id", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = inspect(bind)
    if inspector.has_table("otp_challenges"):
        if not has_index("otp_challenges", op.f("ix_otp_challenges_booking_id")):
            op.create_index(op.f("ix_otp_challenges_booking_id"), "otp_challenges", ["booking_id"], unique=False)
        if not has_index("otp_challenges", op.f("ix_otp_challenges_phone_number")):
            op.create_index(op.f("ix_otp_challenges_phone_number"), "otp_challenges", ["phone_number"], unique=False)
        if not has_index("otp_challenges", op.f("ix_otp_challenges_purpose")):
            op.create_index(op.f("ix_otp_challenges_purpose"), "otp_challenges", ["purpose"], unique=False)
        if not has_index("otp_challenges", op.f("ix_otp_challenges_user_id")):
            op.create_index(op.f("ix_otp_challenges_user_id"), "otp_challenges", ["user_id"], unique=False)

    if not inspector.has_table("pricing_insights"):
        op.create_table(
            "pricing_insights",
            sa.Column("category_name", sa.String(length=100), nullable=False),
            sa.Column("city", sa.String(length=100), nullable=False),
            sa.Column("rate_type", sa.String(length=20), nullable=False),
            sa.Column("suggested_min", sa.Float(), nullable=False),
            sa.Column("suggested_median", sa.Float(), nullable=False),
            sa.Column("suggested_max", sa.Float(), nullable=False),
            sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("id", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = inspect(bind)
    if inspector.has_table("pricing_insights"):
        if not has_index("pricing_insights", op.f("ix_pricing_insights_category_name")):
            op.create_index(op.f("ix_pricing_insights_category_name"), "pricing_insights", ["category_name"], unique=False)
        if not has_index("pricing_insights", op.f("ix_pricing_insights_city")):
            op.create_index(op.f("ix_pricing_insights_city"), "pricing_insights", ["city"], unique=False)
        if not has_index("pricing_insights", op.f("ix_pricing_insights_rate_type")):
            op.create_index(op.f("ix_pricing_insights_rate_type"), "pricing_insights", ["rate_type"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_pricing_insights_rate_type"), table_name="pricing_insights")
    op.drop_index(op.f("ix_pricing_insights_city"), table_name="pricing_insights")
    op.drop_index(op.f("ix_pricing_insights_category_name"), table_name="pricing_insights")
    op.drop_table("pricing_insights")

    op.drop_index(op.f("ix_otp_challenges_user_id"), table_name="otp_challenges")
    op.drop_index(op.f("ix_otp_challenges_purpose"), table_name="otp_challenges")
    op.drop_index(op.f("ix_otp_challenges_phone_number"), table_name="otp_challenges")
    op.drop_index(op.f("ix_otp_challenges_booking_id"), table_name="otp_challenges")
    op.drop_table("otp_challenges")

    op.drop_column("work_requests", "category_label")
    op.drop_column("bookings", "service_start_verified_at")
    op.drop_column("bookings", "service_start_verified")
    op.drop_column("bookings", "service_started_at")
    op.drop_column("users", "phone_verified_at")
    op.drop_column("users", "is_phone_verified")
    op.drop_column("users", "phone_number")
