from pydantic import BaseModel, Field
from typing import Optional
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
    conversation_id: Optional[str] = None
class QuizRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=120)
    difficulty: Optional[str] = "adaptive"
    count: int = Field(default=5, ge=3, le=10)
class QuizSubmit(BaseModel):
    quiz_id: str
    answers: dict[str, int]
