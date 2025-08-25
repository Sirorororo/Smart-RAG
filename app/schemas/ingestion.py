from pydantic import BaseModel
from uuid import UUID

class IngestResponse(BaseModel):
    status: str
    kb_name: str