from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import structlog

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.models.conversation import Conversation, Message
from app.models.schemas import (
    ConversationInfo, 
    MessageInfo, 
    FeedbackRequest,
    ExtractKnowledgeRequest,
    ExtractKnowledgeResponse
)
from app.services.conversation_to_knowledge import ConversationToKnowledgeService

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=List[ConversationInfo])
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """Get list of all conversations."""
    try:
        conversations = (
            db.query(Conversation)
            .filter(Conversation.user_id == current_user["user_id"])
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        result = []
        for conv in conversations:
            message_count = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).count()
            
            result.append(
                ConversationInfo(
                    id=conv.id,
                    session_id=conv.session_id,
                    title=conv.title,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    message_count=message_count,
                )
            )
        
        return result

    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/messages", response_model=List[MessageInfo])
async def get_conversation_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """Get all messages from a specific conversation."""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.user_id == current_user["user_id"],
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        
        return [
            MessageInfo(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                image_url=msg.image_url,
                sources=msg.sources,
                feedback=msg.feedback,
                created_at=msg.created_at,
            )
            for msg in messages
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_conversation(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """Delete a conversation and all its messages."""
    try:
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.user_id == current_user["user_id"],
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        db.delete(conversation)
        db.commit()
        
        logger.info(f"Conversation deleted", session_id=session_id)
        
        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """Submit feedback for a message."""
    try:
        message = db.query(Message).filter(Message.id == request.message_id).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        conversation = db.query(Conversation).filter(
            Conversation.id == message.conversation_id,
            Conversation.user_id == current_user["user_id"],
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Message not found")
        
        message.feedback = request.feedback
        db.commit()
        
        logger.info(f"Feedback submitted", message_id=request.message_id, feedback=request.feedback)
        
        return {"message": "Feedback submitted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/extract-knowledge", response_model=ExtractKnowledgeResponse)
async def extract_knowledge_from_conversation(
    session_id: str,
    request: ExtractKnowledgeRequest = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """
    대화에서 지식을 추출합니다.
    긍정 피드백을 받은 메시지를 기반으로 자동으로 QA 쌍을 생성합니다.
    """
    try:
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.user_id == current_user["user_id"],
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        service = ConversationToKnowledgeService()
        
        message_ids = request.message_ids if request else None
        
        result = await service.extract_knowledge_from_conversation(
            session_id=session_id,
            db=db,
            specific_message_ids=message_ids,
            user_id=current_user["user_id"],
        )
        
        logger.info(
            "Knowledge extracted successfully",
            session_id=session_id,
            knowledge_id=result["id"]
        )
        
        return ExtractKnowledgeResponse(**result)

    except ValueError as e:
        logger.warning(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extractable")
async def list_extractable_conversations(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_required),
):
    """
    지식 추출이 가능한 대화 목록을 조회합니다.
    (긍정 피드백이 있는 대화)
    """
    try:
        service = ConversationToKnowledgeService()
        result = await service.get_extractable_conversations(
            db=db, limit=limit, user_id=current_user["user_id"]
        )
        
        return {"conversations": result, "count": len(result)}

    except Exception as e:
        logger.error(f"Error listing extractable conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
