from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    num_chunks: int
    status: str
    created_at: datetime


class DocumentInfo(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    num_chunks: int
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    image_data: Optional[str] = None  # base64 data URL (data:image/jpeg;base64,...)
    conversation_id: Optional[str] = None
    collection_name: str = "documents"
    search_sources: List[str] = Field(default=["documents", "knowledge"])
    top_k: int = Field(default=4, ge=1, le=15)


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    sources: List[Dict[str, Any]]
    created_at: datetime


class FeedbackRequest(BaseModel):
    message_id: int
    feedback: str = Field(..., pattern="^(positive|negative)$")


class ConversationInfo(BaseModel):
    id: int
    session_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    message_count: int


class MessageInfo(BaseModel):
    id: int
    role: str
    content: str
    image_url: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]]
    feedback: Optional[str]
    created_at: datetime


# Knowledge Base Schemas
class KnowledgeEntryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    status: str = Field(default="published", pattern="^(draft|published)$")


class KnowledgeEntryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(draft|published)$")


class KnowledgeEntryResponse(BaseModel):
    id: int
    title: str
    content: str
    category: Optional[str]
    tags: List[str]
    source_type: str
    author: Optional[str]
    status: str
    num_chunks: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class KnowledgeEntryListItem(BaseModel):
    id: int
    title: str
    category: Optional[str]
    tags: List[str]
    source_type: str
    author: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    display_order: int = Field(default=0, ge=0)


class KnowledgeCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    display_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class UnifiedSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    sources: List[str] = Field(default=["documents", "knowledge"])
    top_k: int = Field(default=10, ge=1, le=20)
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class UnifiedSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ExtractKnowledgeRequest(BaseModel):
    message_ids: Optional[List[int]] = Field(default=None, description="특정 메시지 ID 리스트 (None이면 모든 긍정 피드백 메시지)")


class ExtractKnowledgeResponse(BaseModel):
    id: int
    title: str
    category: Optional[str]
    tags: List[str]
    status: str
    num_messages: int
