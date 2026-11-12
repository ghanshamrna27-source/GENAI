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
