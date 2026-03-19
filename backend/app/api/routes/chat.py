from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
import base64
import re
import structlog
import uuid
from datetime import datetime
from pathlib import Path
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

CHAT_IMAGES_DIR = Path("./uploads/chat_images")
CHAT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _save_chat_image(data_url: str) -> str:
    """base64 data URL → 파일 저장 후 서빙 경로 반환"""
    match = re.match(r"data:image/(\w+);base64,(.+)", data_url, re.DOTALL)
    if not match:
        raise ValueError("Invalid image data URL format")
    ext = match.group(1).lower()
    if ext == "jpeg":
        ext = "jpg"
    raw_b64 = match.group(2)
    image_bytes = base64.b64decode(raw_b64)

    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = CHAT_IMAGES_DIR / filename
    filepath.write_bytes(image_bytes)

    return f"/api/chat/images/{filename}"


def _normalize_source_display_name(raw: str) -> str:
    """참고문서 표시명 정규화: 타임스탬프_파일명.pdf → 파일명.pdf"""
    if not raw or raw == "Unknown":
        return raw
    # 업로드 시 붙는 숫자_ 또는 숫자.숫자_ 접두사 제거 (예: 1739123456.789_원본.pdf)
    m = re.match(r"^\d+\.?\d*_(.+)$", raw.strip())
    return m.group(1) if m else raw


def _format_source(doc: dict) -> dict:
    """검색 결과를 프론트엔드 소스 형식으로 변환 (통합/단일 검색 모두 지원)"""
    meta = doc.get("metadata") or {}
    content = doc.get("content") or ""
    score = doc.get("relevance_score") or doc.get("final_score") or doc.get("weighted_score") or 0
    raw = meta.get("source") or meta.get("title") or "Unknown"
    source = meta.get("filename") or _normalize_source_display_name(raw) or raw
    file_type = meta.get("file_type", "")
    result: dict = {
        "content": content[:200] if content else "",
        "source": source,
        "page": meta.get("page", "N/A"),
        "relevance_score": float(score),
        "file_type": file_type,
    }
    doc_id = meta.get("document_id")
    if doc_id:
        result["document_id"] = int(doc_id) if str(doc_id).isdigit() else doc_id
    if file_type in (".sql", ".tst"):
        result["sql_type"] = meta.get("sql_type", "")
        result["sql_tables"] = meta.get("sql_tables", "")
    return result


def _filter_relevant_sources(sources: list, min_score: float = 0.15) -> list:
    """관련도가 낮은 소스 제거 — 실제 참고된 문서만 프론트에 표시"""
    if not sources:
        return sources
    filtered = [s for s in sources if s.get("relevance_score", 0) >= min_score]
    return filtered if filtered else sources[:1]


@router.get("/images/{filename}")
async def get_chat_image(filename: str):
    """채팅 이미지 서빙"""
    filepath = CHAT_IMAGES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    media_type = "image/jpeg"
    if filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".gif"):
        media_type = "image/gif"
    elif filename.endswith(".webp"):
        media_type = "image/webp"
    return FileResponse(filepath, media_type=media_type)


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
        metadata = {
            'type': 'metadata',
            'conversation_id': conversation_id,
            'sources': sources,
        }
        yield f"data: {json.dumps(metadata)}\n\n"

        full_answer = ""

        async for chunk in answer_stream:
            if chunk:
                full_answer += chunk
                content_data = {
                    'type': 'content',
                    'content': chunk,
                }
                yield f"data: {json.dumps(content_data)}\n\n"

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=full_answer,
            sources=sources,
        )
        db.add(assistant_message)
        db.commit()

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

        # 이미지 처리
        image_url = None
        image_base64 = None
        if request.image_data:
            try:
                image_url = _save_chat_image(request.image_data)
                image_base64 = request.image_data
            except Exception as img_err:
                logger.error(f"Image save failed: {img_err}")

        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            image_url=image_url,
        )
        db.add(user_message)
        db.commit()

        chat_history = []
        previous_messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
            .limit(11)
            .all()
        )

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

        user_id = current_user["user_id"]
        if len(request.search_sources) > 1 or "knowledge" in request.search_sources or "web" in request.search_sources:
            unified_search = UnifiedSearchEngine()
            result = await unified_search.generate_unified_answer(
                query=request.message,
                sources=request.search_sources,
                top_k=request.top_k,
                chat_history=chat_history,
                stream=False,
                user_id=user_id,
                image_base64=image_base64,
            )
        else:
            rag_engine = RAGEngine()
            result = await rag_engine.generate_answer(
                query=request.message,
                collection_name=request.collection_name,
                top_k=request.top_k,
                chat_history=chat_history,
                stream=False,
                user_id=user_id,
                image_base64=image_base64,
            )

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result["answer"],
            sources=_filter_relevant_sources([_format_source(doc) for doc in result.get("sources", [])]),
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

        # 이미지 처리
        image_url = None
        image_base64 = None
        if request.image_data:
            try:
                image_url = _save_chat_image(request.image_data)
                image_base64 = request.image_data
            except Exception as img_err:
                logger.error(f"Image save failed: {img_err}")

        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            image_url=image_url,
        )
        db.add(user_message)
        db.commit()

        chat_history = []
        previous_messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
            .limit(11)
            .all()
        )

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

        user_id = current_user["user_id"]
        if len(request.search_sources) > 1 or "knowledge" in request.search_sources or "web" in request.search_sources:
            unified_search = UnifiedSearchEngine()
            result = await unified_search.generate_unified_answer(
                query=request.message,
                sources=request.search_sources,
                top_k=request.top_k,
                chat_history=chat_history,
                stream=True,
                user_id=user_id,
                image_base64=image_base64,
            )
        else:
            rag_engine = RAGEngine()
            result = await rag_engine.generate_answer(
                query=request.message,
                collection_name=request.collection_name,
                top_k=request.top_k,
                chat_history=chat_history,
                stream=True,
                user_id=user_id,
                image_base64=image_base64,
            )

        sources = _filter_relevant_sources([_format_source(doc) for doc in result.get("sources", [])])

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
