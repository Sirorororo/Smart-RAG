from pydantic import BaseModel

class RetrieveRequest(BaseModel):
    query: str
    collection_name: str

class RetrieveResponse(BaseModel):
    response: str
