from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(..., description="Pergunta do usuário")
    k: int = Field(4, description="Quantidade de documentos a recuperar")

class ContextItem(BaseModel):
    source: str
    chunk: str
    score: float

class ChatResponse(BaseModel):
    answer: str
    contexts: List[ContextItem]
