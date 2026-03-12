from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=True, index=True)  # "error_fix", "tech_share", "how_to"
    tags = Column(JSON, default=list)  # ["python", "docker", "bug"]

    # 메타데이터
    source_type = Column(String, nullable=False, default="manual")  # "manual", "file", "conversation"
    author = Column(String, nullable=True)
    status = Column(String, default="published", index=True)  # "draft", "published"

    # 벡터 저장소 연결
    collection_name = Column(String, default="knowledge_base")
    vector_ids = Column(JSON, default=list)  # ChromaDB document IDs
    num_chunks = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class KnowledgeCategory(Base):
    __tablename__ = "knowledge_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)  # UI 표시용 (예: "#3182f6")
    icon = Column(String, nullable=True)  # lucide-react 아이콘 이름 (예: "AlertCircle")
    display_order = Column(Integer, default=0)  # 정렬 순서

    created_at = Column(DateTime(timezone=True), server_default=func.now())
