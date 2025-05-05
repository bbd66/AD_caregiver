from pydantic import BaseModel

class DocumentRequest(BaseModel):
    user_id: int

class DocumentResponse(BaseModel):
    id: int
    title: str
    file_url: str
    upload_time: str
    digital_human_id: int
    user_id: int