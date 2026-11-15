from dataclasses import asdict, dataclass
from typing import Optional, List, Any
from pydantic import BaseModel, Field

@dataclass
class Record:
    id: int
    category: str
    title: str
    keyword: str
    question: str
    answer: str
    source_url: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=int(data["id"]),
            category=str(data.get("category", "General")),
            title=str(data.get("title", "Untitled")),
            keyword=str(data.get("keyword", "")),
            question=str(data.get("question", "")),
            answer=str(data.get("answer", "")),
            source_url=str(data.get("source_url", "")),
        )

    def to_dict(self):
        return asdict(self)


class RecordSchema(BaseModel):
    id: int
    category: str
    title: str
    keyword: str
    question: str
    answer: str
    source_url: str
    similarity_score: Optional[float] = None


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=2, description="The Git or GitHub question to ask")
    category: Optional[str] = Field(None, description="Optional category (Git, GitHub, Git Branching, Troubleshooting, GitHub Actions)")
    asker: Optional[str] = Field("learner", description="Name or ID of the user asking the question")


class QuestionResponse(BaseModel):
    status: str = "success"
    question: str
    category: Optional[str] = None
    asker: str = "learner"
    answer: Optional[str] = None
    matched_record: Optional[RecordSchema] = None
    relevant_records: List[RecordSchema] = []
    message: str


class HealthResponse(BaseModel):
    status: str
    project: str
    description: str
    records_count: int
    version: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, description="The Git/GitHub question or prompt for the assistant")
    version: Optional[str] = Field("v2", description="Prompt template version: 'v1' (direct) or 'v2' (structured & grounded)")
    provider: Optional[str] = Field(None, description="Optional LLM provider override ('groq', 'gemini')")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="The assistant's explanation or resolution")
    confidence: str = Field(..., description="Confidence rating: 'high', 'medium', or 'low'")
    follow_up: str = Field(..., description="Recommended follow-up command or proactive question")
    provider: Optional[str] = Field(None, description="The backend provider that handled the request")
    model: Optional[str] = Field(None, description="The model used to generate the response")


class SemanticSearchResult(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier")
    text: str = Field(..., description="The chunk text segment")
    title: str = Field(..., description="Document title from source")
    source: str = Field(..., description="Official documentation URL or source path")
    page: int = Field(..., description="Page or document catalog ID")
    category: str = Field(..., description="Domain category")
    similarity_score: float = Field(..., description="Dense embedding cosine similarity score (0.0 to 1.0)")
    distance: float = Field(..., description="Cosine distance metric (1.0 - similarity)")
