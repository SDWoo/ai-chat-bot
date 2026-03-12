"""
대화 내용을 지식 베이스로 변환하는 서비스
긍정 피드백을 받은 대화에서 자동으로 QA 쌍을 추출합니다.
"""

from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
import structlog
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from app.core.config import settings
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeEntry
from app.services.embedding_service import EmbeddingService
from app.services.chunking import ChunkingService

logger = structlog.get_logger()


class ConversationToKnowledgeService:
    """대화를 지식으로 변환하는 서비스"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.3,
            max_tokens=2000,
            request_timeout=60,
        )
        self.embedding_service = EmbeddingService()
        self.chunking_service = ChunkingService()

    async def extract_knowledge_from_conversation(
        self, 
        session_id: str, 
        db: Session,
        specific_message_ids: Optional[List[int]] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        대화에서 지식을 추출합니다.
        
        Args:
            session_id: 대화 세션 ID
            db: 데이터베이스 세션
            specific_message_ids: 특정 메시지 ID 리스트 (None이면 긍정 피드백 받은 모든 메시지)
            
        Returns:
            생성된 지식 정보
        """
        try:
            # 1. 대화 조회
            conversation = db.query(Conversation).filter(
                Conversation.session_id == session_id
            ).first()

            if not conversation:
                raise ValueError(f"Conversation not found: {session_id}")

            # 2. 긍정 피드백을 받은 메시지 조회
            query = db.query(Message).filter(
                Message.conversation_id == conversation.id,
                Message.role == "assistant",
                Message.feedback == "positive"
            )
            
            if specific_message_ids:
                query = query.filter(Message.id.in_(specific_message_ids))
            
            positive_messages = query.order_by(Message.created_at.asc()).all()

            if not positive_messages:
                raise ValueError("No positive feedback messages found")

            # 3. 전체 대화 컨텍스트 구성
            all_messages = db.query(Message).filter(
                Message.conversation_id == conversation.id
            ).order_by(Message.created_at.asc()).all()

            conversation_context = self._build_conversation_context(all_messages, positive_messages)

            # 4. GPT를 사용하여 지식 추출
            knowledge_data = await self._extract_with_gpt(conversation_context)

            # 5. 지식 엔트리 생성 (draft 상태)
            knowledge_entry = KnowledgeEntry(
                title=knowledge_data["title"],
                content=knowledge_data["content"],
                category=knowledge_data["category"],
                tags=knowledge_data["tags"],
                source_type="conversation",
                author=f"conversation:{session_id}",
                status="draft",  # 관리자 검토를 위한 draft 상태
                user_id=user_id,
            )

            db.add(knowledge_entry)
            db.commit()
            db.refresh(knowledge_entry)

            # 6. 벡터 DB에 저장
            try:
                from langchain.schema import Document
                
                # 텍스트를 청크로 분할
                combined_text = f"{knowledge_entry.title}\n\n{knowledge_entry.content}"
                chunks = self.chunking_service.chunk_text(combined_text, metadata={})
                
                # Document 객체로 변환
                base_metadata = {
                    "type": "knowledge",
                    "knowledge_id": knowledge_entry.id,
                    "category": knowledge_entry.category or "general",
                    "tags": ", ".join(knowledge_entry.tags) if knowledge_entry.tags else "",
                    "title": knowledge_entry.title,
                    "source_type": "conversation",
                }
                if user_id is not None:
                    base_metadata["user_id"] = str(user_id)
                documents = [
                    Document(
                        page_content=chunk.page_content,
                        metadata={**base_metadata},
                    )
                    for chunk in chunks
                ]
                
                vector_ids = self.embedding_service.add_documents_to_store(
                    documents=documents,
                    collection_name="knowledge_base",
                )

                # 벡터 ID 저장
                knowledge_entry.vector_ids = vector_ids
                knowledge_entry.num_chunks = len(vector_ids)
                knowledge_entry.collection_name = "knowledge_base"
                db.commit()

            except Exception as e:
                logger.error("Failed to store in vector DB", error=str(e))
                # 벡터 DB 저장 실패해도 지식 엔트리는 유지

            logger.info(
                "Knowledge extracted from conversation",
                session_id=session_id,
                knowledge_id=knowledge_entry.id,
                status="draft",
            )

            return {
                "id": knowledge_entry.id,
                "title": knowledge_entry.title,
                "category": knowledge_entry.category,
                "tags": knowledge_entry.tags,
                "status": knowledge_entry.status,
                "num_messages": len(positive_messages),
            }

        except Exception as e:
            logger.error("Error extracting knowledge from conversation", error=str(e))
            raise

    def _build_conversation_context(
        self, 
        all_messages: List[Message], 
        positive_messages: List[Message]
    ) -> str:
        """대화 컨텍스트를 구성합니다."""
        
        context_parts = []
        
        # 전체 대화 흐름
        context_parts.append("=== 전체 대화 흐름 ===\n")
        for msg in all_messages:
            role = "사용자" if msg.role == "user" else "AI"
            feedback_mark = " ✓(긍정 피드백)" if msg in positive_messages else ""
            context_parts.append(f"{role}{feedback_mark}: {msg.content}\n")
        
        return "\n".join(context_parts)

    async def _extract_with_gpt(self, conversation_context: str) -> Dict[str, Any]:
        """GPT를 사용하여 대화에서 지식을 추출합니다."""
        
        system_prompt = """당신은 대화 내용을 분석하여 재사용 가능한 지식으로 변환하는 전문가입니다.

긍정 피드백(✓)을 받은 AI 응답을 중심으로, 다음을 추출하세요:

1. **제목**: 지식의 핵심을 담은 명확한 제목 (30자 이내)
2. **내용**: QA 형식으로 구조화된 내용
   - 질문과 답변이 명확히 구분되어야 함
   - 구체적이고 실용적인 정보 포함
   - 마크다운 형식 사용 가능
3. **카테고리**: 다음 중 하나 선택
   - "error_fix": 오류 해결, 문제 해결
   - "tech_share": 기술 설명, 개념 설명
   - "how_to": 사용법, 가이드, 튜토리얼
   - "general": 일반 정보
4. **태그**: 관련 키워드 3-5개 (배열 형태)

응답은 반드시 다음 JSON 형식으로 제공하세요:
{
  "title": "제목",
  "content": "# 질문\\n\\n사용자의 질문 내용\\n\\n# 답변\\n\\n상세한 답변 내용",
  "category": "카테고리",
  "tags": ["태그1", "태그2", "태그3"]
}
"""

        user_message = f"""다음 대화에서 지식을 추출해주세요:

{conversation_context}

위 대화 내용을 분석하여 JSON 형식으로 지식을 추출해주세요."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]

            response = await self.llm.agenerate([messages])
            result_text = response.generations[0][0].text.strip()

            # JSON 파싱
            import json
            
            # Markdown 코드 블록 제거
            if result_text.startswith("```"):
                lines = result_text.split("\n")
                result_text = "\n".join(lines[1:-1])
            
            knowledge_data = json.loads(result_text)

            # 기본값 설정
            knowledge_data.setdefault("title", "대화에서 추출한 지식")
            knowledge_data.setdefault("category", "general")
            knowledge_data.setdefault("tags", [])

            # 제목 길이 제한
            if len(knowledge_data["title"]) > 100:
                knowledge_data["title"] = knowledge_data["title"][:97] + "..."

            logger.info("Knowledge extracted with GPT", data=knowledge_data)
            
            return knowledge_data

        except json.JSONDecodeError as e:
            logger.error("Failed to parse GPT response as JSON", error=str(e))
            # Fallback: 기본 지식 생성
            return {
                "title": "대화에서 추출한 지식",
                "content": f"# 대화 내용\n\n{conversation_context}",
                "category": "general",
                "tags": ["대화", "자동추출"],
            }
        except Exception as e:
            logger.error("Error extracting with GPT", error=str(e))
            raise

    async def get_extractable_conversations(
        self, 
        db: Session, 
        limit: int = 50,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        지식 추출이 가능한 대화 목록을 조회합니다.
        (긍정 피드백이 있는 대화)
        """
        try:
            # 긍정 피드백이 있는 대화 조회
            query = db.query(Conversation).join(Message).filter(
                Message.feedback == "positive"
            )
            if user_id is not None:
                query = query.filter(Conversation.user_id == user_id)
            conversations = query.distinct().order_by(
                Conversation.updated_at.desc()
            ).limit(limit).all()

            result = []
            for conv in conversations:
                positive_count = db.query(Message).filter(
                    Message.conversation_id == conv.id,
                    Message.feedback == "positive"
                ).count()

                result.append({
                    "session_id": conv.session_id,
                    "title": conv.title,
                    "positive_feedback_count": positive_count,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                })

            return result

        except Exception as e:
            logger.error("Error getting extractable conversations", error=str(e))
            raise
