from enum import Enum


class UserRole(str, Enum):
    worker = "worker"
    employer = "employer"
    contractor = "contractor"
    operator = "operator"
    admin = "admin"


class VerificationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AvailabilityStatus(str, Enum):
    available = "available"
    busy = "busy"
    unavailable = "unavailable"


class WorkUrgency(str, Enum):
    low = "low"
    normal = "normal"
    urgent = "urgent"
    emergency = "emergency"


class WorkRequestStatus(str, Enum):
    open = "open"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class ApplicationStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"


class BookingStatus(str, Enum):
    requested = "requested"
    accepted = "accepted"
    rejected = "rejected"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class EmployerType(str, Enum):
    household = "household"
    shop = "shop"
    business = "business"
    farm = "farm"
    event_organizer = "event_organizer"


class DocumentType(str, Enum):
    government_id = "government_id"
    phone = "phone"
    local_reference = "local_reference"
    skill_proof = "skill_proof"


class DisputeIssueType(str, Enum):
    non_payment = "non_payment"
    no_show = "no_show"
    unsafe_behavior = "unsafe_behavior"
    fake_profile = "fake_profile"
    poor_work = "poor_work"
    other = "other"


class DisputeStatus(str, Enum):
    open = "open"
    under_review = "under_review"
    resolved = "resolved"
    rejected = "rejected"


class ContactType(str, Enum):
    call = "call"
    whatsapp = "whatsapp"
    booking_request = "booking_request"
