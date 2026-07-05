from pydantic import BaseModel

from app.common.enums import DisputeIssueType, DisputeStatus


class DisputeCreate(BaseModel):
    booking_id: str | None = None
    against_user_id: str | None = None
    issue_type: DisputeIssueType
    description: str
    evidence_urls: list[str] = []


class DisputeUpdate(BaseModel):
    status: DisputeStatus
    admin_notes: str | None = None
