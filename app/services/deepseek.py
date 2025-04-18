from pydantic import BaseModel

class DeepSeekRequest(BaseModel):
    user_input: str

class DeepSeekResponse(BaseModel):
    reply: str