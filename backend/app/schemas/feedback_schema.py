from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class FeedbackBase(BaseModel):
    booking_id: str
    client_id: str
    master_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackDB(FeedbackBase):
    id: str 