from pydantic import BaseModel


class BulkRequestCreate(BaseModel):
    category: str
    workers_needed: int
    location_text: str
    notes: str | None = None


class SavedWorkerCreate(BaseModel):
    worker_id: str
    group_name: str | None = None
