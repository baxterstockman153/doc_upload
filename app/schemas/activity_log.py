from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    method: str
    path: str
    status_code: int
    request_id: str
    error_message: Optional[str]
    created_at: datetime
