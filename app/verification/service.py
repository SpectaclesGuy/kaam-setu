from datetime import datetime
import hashlib
import time

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.common.enums import DocumentType, UserRole, VerificationStatus
from app.core.config import settings
from app.users.models import User
from app.verification.models import VerificationDocument
from app.verification.schemas import VerificationReview, VerificationUpload


def upload_document(db: Session, user: User, payload: VerificationUpload) -> VerificationDocument:
    document = (
        db.query(VerificationDocument)
        .filter(
            VerificationDocument.user_id == user.id,
            VerificationDocument.document_type == payload.document_type,
        )
        .first()
    )
    if not document:
        document = VerificationDocument(user_id=user.id, **payload.model_dump())
    else:
        document.document_url = payload.document_url
        document.status = VerificationStatus.pending
        document.remarks = None
        document.reviewed_by = None
        document.reviewed_at = None
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def review_document(db: Session, reviewer: User, document: VerificationDocument, payload: VerificationReview):
    if reviewer.role not in {UserRole.admin, UserRole.operator}:
        raise HTTPException(status_code=403, detail="Admin or operator access required")
    document.status = payload.status
    document.remarks = payload.remarks
    document.reviewed_by = reviewer.id
    document.reviewed_at = datetime.utcnow().isoformat()
    db.commit()
    db.refresh(document)
    if payload.status == VerificationStatus.approved:
        document_owner = db.get(User, document.user_id)
        if document_owner:
            document_owner.is_verified_user = True
            if document_owner.worker_profile:
                document_owner.worker_profile.verification_status = VerificationStatus.approved
            db.commit()
    return document


async def upload_file_to_cloudinary(*, file_bytes: bytes, filename: str, content_type: str, tag: str | None = None) -> str:
    if not settings.cloudinary_cloud_name or not settings.cloudinary_api_key or not settings.cloudinary_api_secret:
        raise HTTPException(status_code=500, detail="Cloudinary server credentials are incomplete.")

    timestamp = str(int(time.time()))
    folder = settings.cloudinary_folder or "karamsetu"
    params_to_sign = {"folder": folder, "timestamp": timestamp}
    if tag:
        params_to_sign["tags"] = tag
    signature_payload = "&".join(f"{key}={params_to_sign[key]}" for key in sorted(params_to_sign))
    signature = hashlib.sha1(f"{signature_payload}{settings.cloudinary_api_secret}".encode("utf-8")).hexdigest()

    data = {
        "api_key": settings.cloudinary_api_key,
        "timestamp": timestamp,
        "signature": signature,
        "folder": folder,
    }
    if tag:
        data["tags"] = tag

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"https://api.cloudinary.com/v1_1/{settings.cloudinary_cloud_name}/image/upload",
            data=data,
            files={"file": (filename, file_bytes, content_type)},
        )
    payload = response.json()
    if not response.is_success:
        detail = payload.get("error", {}).get("message") or "Cloudinary upload failed."
        raise HTTPException(status_code=502, detail=detail)
    secure_url = payload.get("secure_url")
    if not secure_url:
        raise HTTPException(status_code=502, detail="Cloudinary upload did not return a secure URL.")
    return secure_url


def verification_tag(document_type: DocumentType) -> str:
    if document_type == DocumentType.government_id:
        return "aadhaar-card"
    if document_type == DocumentType.skill_proof:
        return "worker-kyc-photo"
    return document_type.value
