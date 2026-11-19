from dataclasses import asdict, dataclass
from typing import Optional, List, Any, Dict
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


class Citation(BaseModel):
    source: str = Field(..., description="Official documentation URL or source path")
    page: int = Field(..., description="Document page or catalog ID")
    title: str = Field(..., description="Document title from source")
    chunk_id: str = Field(..., description="Unique chunk identifier")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="The Git or GitHub question to answer")
    top_k: Optional[int] = Field(default=3, ge=1, le=10, description="Number of context chunks to retrieve")


class AskResponse(BaseModel):
    question: str = Field(..., description="The original question asked")
    answer: str = Field(..., description="The grounded answer with citations or refusal statement")
    citations: List[Citation] = Field(default=[], description="List of document citations supporting the answer")
    retrieved_chunks: List[SemanticSearchResult] = Field(default=[], description="The retrieved context chunks")
    confidence: str = Field(..., description="Confidence rating: 'high', 'medium', or 'low'")
    is_grounded: bool = Field(..., description="Whether the response is strictly grounded in retrieved chunks")


class AgentRequest(BaseModel):
    query: Optional[str] = Field(default="", description="The user query or instruction for the agent")
    thread_id: Optional[str] = Field(None, description="Optional thread/session ID for conversational memory")
    approved: Optional[bool] = Field(None, description="Set to True to approve a pending destructive action")
    agent_type: Optional[str] = Field("langgraph", description="Agent implementation: 'langgraph' or 'handwritten'")


class AgentResponse(BaseModel):
    query: str = Field(..., description="User query or command")
    answer: str = Field(..., description="Agent response and guidance")
    thread_id: str = Field(..., description="Thread / session ID in memory")
    agent_type: str = Field("langgraph", description="The agent backend used")
    pending_approval: Optional[Dict[str, Any]] = Field(None, description="Details of action awaiting human confirmation")
    tools_called: List[str] = Field(default=[], description="List of tools invoked during reasoning")
    is_approved: Optional[bool] = Field(None, description="Current approval status")
    steps: List[Dict[str, Any]] = Field(default=[], description="Reasoning trace and tool execution steps")
    messages_count: Optional[int] = Field(0, description="Total messages retained in session memory")


