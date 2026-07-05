from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import DocumentType, VerificationStatus
from app.core.database import Base, TimestampMixin, UUIDMixin


class VerificationDocument(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "verification_documents"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType))
    document_url: Mapped[str] = mapped_column(String(500))
    status: Mapped[VerificationStatus] = mapped_column(Enum(VerificationStatus), default=VerificationStatus.pending)
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
