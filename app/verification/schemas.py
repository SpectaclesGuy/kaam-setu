from pydantic import BaseModel

from app.common.enums import DocumentType, VerificationStatus


class VerificationUpload(BaseModel):
    document_type: DocumentType
    document_url: str


class VerificationReview(BaseModel):
    status: VerificationStatus
    remarks: str | None = None
