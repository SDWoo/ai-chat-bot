from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import structlog
from datetime import datetime, timedelta

from app.models.conversation import Conversation, Message
from app.models.document import Document
from app.services.embedding_service import EmbeddingService
from app.services.chunking import ChunkingService
from langchain.schema import Document as LangchainDocument

logger = structlog.get_logger()


class LearningService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chunking_service = ChunkingService()

    def get_high_quality_conversations(
        self,
        db: Session,
        min_feedback_score: float = 0.7,
        days_back: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get conversations with positive feedback for learning.
        
        Args:
            db: Database session
            min_feedback_score: Minimum feedback score to consider
            days_back: Number of days to look back
        
        Returns:
            List of high-quality QA pairs
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            messages = (
                db.query(Message)
                .filter(Message.feedback == "positive")
                .filter(Message.created_at >= cutoff_date)
                .all()
            )
            
            qa_pairs = []
            for msg in messages:
                if msg.role != "assistant":
                    continue
                
                conversation = db.query(Conversation).filter(
                    Conversation.id == msg.conversation_id
                ).first()
                
                if not conversation:
                    continue
                
                user_messages = (
                    db.query(Message)
                    .filter(Message.conversation_id == conversation.id)
                    .filter(Message.role == "user")
                    .filter(Message.created_at < msg.created_at)
                    .order_by(Message.created_at.desc())
                    .first()
                )
                
                if user_messages:
                    qa_pairs.append({
                        "question": user_messages.content,
                        "answer": msg.content,
                        "sources": msg.sources,
                        "created_at": msg.created_at,
                    })
            
            logger.info(f"Found {len(qa_pairs)} high-quality QA pairs")
            return qa_pairs

        except Exception as e:
            logger.error(f"Error getting high-quality conversations: {str(e)}")
            return []

    def format_qa_for_embedding(self, qa_pair: Dict[str, Any]) -> str:
        """
        Format a QA pair into a text suitable for embedding.
        
        Args:
            qa_pair: Dictionary containing question, answer, and metadata
        
        Returns:
            Formatted text
        """
        text = f"질문: {qa_pair['question']}\n\n답변: {qa_pair['answer']}"
        
        if qa_pair.get("sources"):
            sources_text = "\n출처: " + ", ".join([
                s.get("source", "Unknown") for s in qa_pair["sources"]
            ])
            text += sources_text
        
        return text

    async def add_conversations_to_vectorstore(
        self,
        db: Session,
        collection_name: str = "learned_conversations",
    ) -> int:
        """
        Add high-quality conversations to a separate vector store for learning.
        
        Args:
            db: Database session
            collection_name: Name of the collection for learned conversations
        
        Returns:
            Number of conversations added
        """
        try:
            logger.info("Adding conversations to vector store for learning")
            
            qa_pairs = self.get_high_quality_conversations(db)
            
            if not qa_pairs:
                logger.info("No high-quality conversations found")
                return 0
            
            documents = []
            for qa in qa_pairs:
                content = self.format_qa_for_embedding(qa)
                
                doc = LangchainDocument(
                    page_content=content,
                    metadata={
                        "type": "learned_conversation",
                        "question": qa["question"],
                        "created_at": qa["created_at"].isoformat(),
                        "sources": qa.get("sources", []),
                    },
                )
                documents.append(doc)
            
            chunks = self.chunking_service.chunk_documents(documents)
            
            self.embedding_service.add_documents_to_store(
                documents=chunks,
                collection_name=collection_name,
            )
            
            logger.info(f"Added {len(chunks)} conversation chunks to vector store")
            return len(chunks)

        except Exception as e:
            logger.error(f"Error adding conversations to vector store: {str(e)}")
            raise

    def analyze_conversation_patterns(
        self,
        db: Session,
        days_back: int = 30,
    ) -> Dict[str, Any]:
        """
        Analyze conversation patterns to identify areas for improvement.
        
        Args:
            db: Database session
            days_back: Number of days to analyze
        
        Returns:
            Analysis results
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            total_messages = (
                db.query(Message)
                .filter(Message.created_at >= cutoff_date)
                .filter(Message.role == "assistant")
                .count()
            )
            
            positive_feedback = (
                db.query(Message)
                .filter(Message.created_at >= cutoff_date)
                .filter(Message.feedback == "positive")
                .count()
            )
            
            negative_feedback = (
                db.query(Message)
                .filter(Message.created_at >= cutoff_date)
                .filter(Message.feedback == "negative")
                .count()
            )
            
            feedback_rate = (positive_feedback + negative_feedback) / total_messages if total_messages > 0 else 0
            positive_rate = positive_feedback / (positive_feedback + negative_feedback) if (positive_feedback + negative_feedback) > 0 else 0
            
            analysis = {
                "period_days": days_back,
                "total_messages": total_messages,
                "positive_feedback": positive_feedback,
                "negative_feedback": negative_feedback,
                "feedback_rate": feedback_rate,
                "positive_rate": positive_rate,
                "analyzed_at": datetime.utcnow().isoformat(),
            }
            
            logger.info("Conversation pattern analysis completed", analysis=analysis)
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing conversation patterns: {str(e)}")
            raise
