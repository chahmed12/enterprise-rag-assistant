from pydantic import BaseModel
from typing import Optional, List

class SourceItem(BaseModel):
    document_name: str
    page: Optional[int] = None
    score: Optional[float] = None
    section: Optional[str] = None
    
class QuestionRequest(BaseModel):
    question: str
    source_filter: Optional[str] = None
    type_filter: Optional[str] = None

class AnswerResponse(BaseModel):
    reponse: str
    sources: List[SourceItem] = []

class IngestResponse(BaseModel):
    file_name: str
    nb_passages: Optional[int] = None
    messages: str

class ReloadResponse(BaseModel):
    messages: str
