from pydantic import BaseModel
from datetime import datetime
from typing import List

class Job(BaseModel):
    job_id: str
    status: str
    kb_name: str
    timestamp: datetime

class JobListResponse(BaseModel):
    jobs: List[Job]
