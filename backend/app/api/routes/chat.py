from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import structlog
import uuid
from datetime import datetime
from typing import AsyncGenerator

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.conversation import Conversation, Message, DocumentUsage
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_engine import RAGEngine
from app.services.llm_service import LLMService
from app.services.unified_search import UnifiedSearchEngine

logger = structlog.get_logger()
router = APIRouter()


def _format_source(doc: dict) -> dict:
    """검색 결과를 프론트엔드 소스 형식으로 변환 (통합/단일 검색 모두 지원)"""
    meta = doc.get("metadata") or {}
    content = doc.get("content") or ""
    score = doc.get("relevance_score") or doc.get("final_score") or doc.get("weighted_score") or 0
    source = meta.get("source") or meta.get("title") or "Unknown"
    return {
        "content": content[:200] if content else "",
        "source": source,
        "page": meta.get("page", "N/A"),
        "relevance_score": float(score),
    }


async def stream_response(
    answer_stream: AsyncGenerator,
    conversation_id: str,
    sources: list,
    db: Session,
    conversation: Conversation,
) -> AsyncGenerator[str, None]:
    """Stream the response in a format suitable for frontend consumption."""
    import json
    
    try:
        # Send metadata first
        metadata = {
            'type': 'metadata',
            'conversation_id': conversation_id,
            'sources': sources,
        }
        yield f"data: {json.dumps(metadata)}\n\n"
        
        # Collect all chunks for database storage
        full_answer = ""
        
        # Stream content chunks
        async for chunk in answer_stream:
            if chunk:
                full_answer += chunk
                content_data = {
                    'type': 'content',
                    'content': chunk,
                }
                yield f"data: {json.dumps(content_data)}\n\n"
        
        # Save complete message to database
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=full_answer,
            sources=sources,
        )
        db.add(assistant_message)
        db.commit()
        
        # Send completion signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in stream_response: {str(e)}")
        error_data = {
            'type': 'error',
            'message': str(e),
        }
        yield f"data: {json.dumps(error_data)}\n\n"


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """
    Send a message and get an AI response based on uploaded documents.
    Supports streaming responses.
    """
    try:
        logger.info("Processing chat request", message=request.message)

        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
            llm_service = LLMService()
            title = await llm_service.generate_conversation_title(request.message)
            
            conversation = Conversation(
                session_id=conversation_id,
                title=title,
                user_id=current_user["user_id"],
            )
            db.add(conversation)
            db.commit()
        else:
            conversation = db.query(Conversation).filter(
                Conversation.session_id == conversation_id,
                Conversation.user_id == current_user["user_id"],
            ).first()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
        )
        db.add(user_message)
        db.commit()

        # Get chat history (excluding current message, limit to last 10 for DB query)
        # The RAG engine will further limit this to 5 most recent with token consideration
        chat_history = []
        previous_messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
            .limit(11)  # Get 11 to exclude the current message (last one)
            .all()
        )
        
        # Exclude the current user message (last one) from history
        for msg in previous_messages[:-1]:
            chat_history.append({
                "role": msg.role,
                "content": msg.content,
            })
        
        logger.info(
            "Chat history retrieved",
            conversation_id=conversation_id,
            history_length=len(chat_history)
        )

        # 통합 검색 사용 (search_sources에 따라)
        user_id = current_user["user_id"]
        if len(request.search_sources) > 1 or "knowledge" in request.search_sources or "web" in request.search_sources:
            # 통합 검색 엔진 사용 (웹 검색 포함)
            unified_search = UnifiedSearchEngine()
            result = await unified_search.generate_unified_answer(
                query=request.message,
                sources=request.search_sources,
                top_k=request.top_k,
                chat_history=chat_history,
                stream=False,
                user_id=user_id,
            )
        else:
            # 기존 RAG 엔진 사용 (단일 소스)
            rag_engine = RAGEngine()
            result = await rag_engine.generate_answer(
                query=request.message,
                collection_name=request.collection_name,
                top_k=request.top_k,
                chat_history=chat_history,
                stream=False,
                user_id=user_id,
            )

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result["answer"],
            sources=[_format_source(doc) for doc in result.get("sources", [])],
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)

        logger.info("Chat response generated", conversation_id=conversation_id)

        return ChatResponse(
            conversation_id=conversation_id,
            message=result["answer"],
            sources=assistant_message.sources,
            created_at=assistant_message.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """
    Send a message and get a streaming AI response.
    Returns a stream of JSON objects.
    재시도 시 동일 conversation_id 사용 시 중복 대화 생성 방지.
    """
    try:
        logger.info("Processing streaming chat request", message=request.message)

        conversation_id = request.conversation_id or str(uuid.uuid4())

        conversation = db.query(Conversation).filter(
            Conversation.session_id == conversation_id,
            Conversation.user_id == current_user["user_id"],
        ).first()

        if not conversation:
            # 새 대화 생성 (클라이언트 제공 ID로 재시도 시 동일 대화 유지)
            llm_service = LLMService()
            title = await llm_service.generate_conversation_title(request.message)

            conversation = Conversation(
                session_id=conversation_id,
                title=title,
                user_id=current_user["user_id"],
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # 사용자 메시지 저장 (새 대화/기존 대화 모두)
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
        )
        db.add(user_message)
        db.commit()

        # Get chat history (excluding current message, limit to last 10 for DB query)
        # The RAG engine will further limit this to 5 most recent with token consideration
        chat_history = []
        previous_messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
            .limit(11)  # Get 11 to exclude the current message (last one)
            .all()
        )
        
        # Exclude the current user message (last one) from history
        for msg in previous_messages[:-1]:
            chat_history.append({
                "role": msg.role,
                "content": msg.content,
            })
        
        logger.info(
            "Streaming chat history retrieved",
            conversation_id=conversation_id,
            history_length=len(chat_history)
        )

        # 통합 검색 사용 (search_sources에 따라)
        user_id = current_user["user_id"]
        if len(request.search_sources) > 1 or "knowledge" in request.search_sources or "web" in request.search_sources:
            # 통합 검색 엔진 사용 (웹 검색 포함)
            unified_search = UnifiedSearchEngine()
            result = await unified_search.generate_unified_answer(
                query=request.message,
                sources=request.search_sources,
                top_k=request.top_k,
                chat_history=chat_history,
                stream=True,
                user_id=user_id,
            )
        else:
            # 기존 RAG 엔진 사용 (단일 소스)
            rag_engine = RAGEngine()
            result = await rag_engine.generate_answer(
                query=request.message,
                collection_name=request.collection_name,
                top_k=request.top_k,
                chat_history=chat_history,
                stream=True,
                user_id=user_id,
            )

        sources = [_format_source(doc) for doc in result.get("sources", [])]

        return StreamingResponse(
            stream_response(
                result["answer_stream"], 
                conversation_id, 
                sources,
                db,
                conversation,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing streaming chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
