from pydantic import BaseModel, Field, model_validator

from app.common.enums import WorkRequestStatus, WorkUrgency


class WorkRequestCreate(BaseModel):
    category_id: str | None = None
    title: str
    description: str
    location_text: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    date_required: str
    urgency: WorkUrgency = WorkUrgency.normal
    budget_min: float | None = Field(default=None, ge=0)
    budget_max: float | None = Field(default=None, ge=0)
    workers_needed: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_budget(self):
        if self.budget_min is not None and self.budget_max is not None and self.budget_min > self.budget_max:
            raise ValueError("budget_min cannot exceed budget_max")
        return self


class WorkRequestUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: WorkRequestStatus | None = None


class ApplyToRequest(BaseModel):
    message: str | None = None


class AssignWorkerRequest(BaseModel):
    worker_id: str
