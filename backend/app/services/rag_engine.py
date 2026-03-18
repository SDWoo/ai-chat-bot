from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain.schema import Document
import structlog
from datetime import datetime
import tiktoken

from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.core.prompts import RAG_SYSTEM_PROMPT, CONVERSATIONAL_SYSTEM_PROMPT, SQL_RAG_SYSTEM_PROMPT

logger = structlog.get_logger()

# Token limits for context management
MAX_CONTEXT_TOKENS = 4000  # Maximum tokens for chat history + context
MAX_HISTORY_MESSAGES = 5  # Maximum number of previous messages to include


class RAGEngine:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {str(e)}, using character approximation")
            return len(text) // 4

    async def search(
        self,
        query: str,
        collection_name: str = "documents",
        top_k: int = 4,
        metadata_filter: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using hybrid search (vector + keyword).
        
        Args:
            query: The search query
            collection_name: Name of the collection to search
            top_k: Number of results to return
            metadata_filter: Optional metadata filters
            use_hybrid: Whether to use hybrid search (vector + keyword)
        
        Returns:
            List of documents with metadata and relevance scores
        """
        try:
            logger.info(
                "Searching for relevant documents",
                query=query,
                collection=collection_name,
                top_k=top_k,
            )

            vector_store = self.embedding_service.get_vector_store(collection_name)
            
            if use_hybrid:
                # Retrieve more candidates for reranking (1.5x)
                results = vector_store.similarity_search_with_relevance_scores(
                    query=query,
                    k=int(top_k * 1.5),
                    filter=metadata_filter,
                )
                
                results = self._rerank_results(query, results)
                results = results[:top_k]
            else:
                results = vector_store.similarity_search_with_relevance_scores(
                    query=query,
                    k=top_k,
                    filter=metadata_filter,
                )

            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance_score": float(score),
                })

            logger.info(f"Found {len(formatted_results)} relevant documents")
            return formatted_results

        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise

    def _rerank_results(
        self,
        query: str,
        results: List[tuple],
        alpha: float = 0.7,
    ) -> List[tuple]:
        """
        Rerank search results using a combination of vector similarity and keyword matching.
        
        Args:
            query: The search query
            results: List of (document, score) tuples
            alpha: Weight for vector similarity (1-alpha for keyword matching)
        """
        try:
            query_lower = query.lower()
            query_terms = set(query_lower.split())
            
            reranked = []
            for doc, vector_score in results:
                content_lower = doc.page_content.lower()
                
                keyword_score = sum(1 for term in query_terms if term in content_lower)
                keyword_score = min(keyword_score / len(query_terms), 1.0) if query_terms else 0
                
                combined_score = alpha * vector_score + (1 - alpha) * keyword_score
                
                reranked.append((doc, combined_score))
            
            reranked.sort(key=lambda x: x[1], reverse=True)
            return reranked

        except Exception as e:
            logger.error(f"Error during reranking: {str(e)}")
            return results

    def _remove_duplicate_sources(
        self, 
        documents: List[Dict[str, Any]], 
        max_sources: int = 2,
        similarity_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate or highly similar sources and limit to max_sources.
        
        Args:
            documents: List of document dictionaries
            max_sources: Maximum number of sources to return
            similarity_threshold: Threshold for considering documents as similar
        
        Returns:
            Filtered list of documents
        """
        if not documents:
            return []
        
        filtered_docs = []
        
        for doc in documents:
            is_duplicate = False
            doc_content = doc['content'].lower()
            
            for existing_doc in filtered_docs:
                existing_content = existing_doc['content'].lower()
                
                # Check if documents are from the same source and page
                same_source = (
                    doc['metadata'].get('source') == existing_doc['metadata'].get('source') and
                    doc['metadata'].get('page') == existing_doc['metadata'].get('page')
                )
                
                if same_source:
                    is_duplicate = True
                    break
                
                # Calculate simple content similarity
                shorter_len = min(len(doc_content), len(existing_content))
                if shorter_len > 0:
                    # Count matching words
                    doc_words = set(doc_content.split())
                    existing_words = set(existing_content.split())
                    
                    if doc_words and existing_words:
                        overlap = len(doc_words & existing_words)
                        similarity = overlap / max(len(doc_words), len(existing_words))
                        
                        if similarity >= similarity_threshold:
                            # Keep the one with higher relevance score
                            if doc.get('relevance_score', 0) <= existing_doc.get('relevance_score', 0):
                                is_duplicate = True
                                break
                            else:
                                # Replace the existing one with the new one
                                filtered_docs.remove(existing_doc)
            
            if not is_duplicate:
                filtered_docs.append(doc)
            
            # Stop if we have enough sources
            if len(filtered_docs) >= max_sources:
                break
        
        return filtered_docs[:max_sources]

    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into a context string for the LLM."""
        context_parts = []
        
        for idx, doc in enumerate(documents, 1):
            metadata = doc["metadata"]
            source = metadata.get("source", "Unknown")
            page = metadata.get("page", "N/A")
            chunk_index = metadata.get("chunk_index", "N/A")
            relevance = doc.get("relevance_score", 0)
            
            context_parts.append(
                f"[문서 {idx}] {source} (페이지: {page}, 관련도: {relevance:.2f})\n"
                f"내용:\n{doc['content']}\n"
            )
        
        separator = "\n" + "=" * 80 + "\n"
        return separator.join(context_parts)

    async def generate_answer(
        self,
        query: str,
        collection_name: str = "documents",
        top_k: int = 4,
        chat_history: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        max_sources: int = 2,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate an answer to the query using RAG.
        
        Args:
            query: The user's question
            collection_name: Name of the collection to search
            top_k: Number of documents to retrieve
            chat_history: Previous conversation history (will be limited to recent messages)
            stream: Whether to stream the response
            max_sources: Maximum number of source documents to include
        
        Returns:
            Dict containing answer, sources, and metadata
        """
        try:
            logger.info(
                "Generating RAG answer",
                query=query,
                has_chat_history=bool(chat_history),
                chat_history_length=len(chat_history) if chat_history else 0
            )

            metadata_filter = {"user_id": str(user_id)} if user_id is not None else None
            documents = await self.search(
                query=query,
                collection_name=collection_name,
                top_k=top_k,
                metadata_filter=metadata_filter,
            )

            if not documents:
                fallback_msg = "죄송합니다. 관련된 문서를 찾을 수 없습니다. 다른 질문을 시도해주세요."
                async def _fallback_stream():
                    yield fallback_msg
                return {
                    "answer": fallback_msg,
                    "answer_stream": _fallback_stream(),
                    "sources": [],
                    "metadata": {
                        "documents_found": 0,
                        "timestamp": datetime.utcnow().isoformat(),
                        "context_used": False,
                    },
                }

            # Remove duplicates and limit sources
            filtered_documents = self._remove_duplicate_sources(documents, max_sources=max_sources)

            context = self._format_context(documents)

            # SQL 파일이 검색 결과에 포함되어 있는지 확인
            has_sql_sources = any(
                doc.get("metadata", {}).get("content_type") == "sql"
                or doc.get("metadata", {}).get("file_type") == ".sql"
                for doc in documents
            )

            use_conversational = bool(chat_history and len(chat_history) > 0)
            
            if use_conversational:
                formatted_history = self._format_chat_history(chat_history)
                system_prompt = CONVERSATIONAL_SYSTEM_PROMPT.format(
                    chat_history=formatted_history,
                    context=context,
                    question=query,
                )
                logger.info("Using conversational prompt with history")
            elif has_sql_sources:
                system_prompt = SQL_RAG_SYSTEM_PROMPT.format(
                    context=context,
                    question=query,
                )
                logger.info("Using SQL RAG prompt (SQL sources detected)")
            else:
                system_prompt = RAG_SYSTEM_PROMPT.format(
                    context=context,
                    question=query,
                )
                logger.info("Using standard RAG prompt without history")

            if stream:
                return {
                    "answer_stream": self.llm_service.generate_streaming_response(
                        system_prompt=system_prompt,
                        user_message=query,
                        chat_history=chat_history,
                    ),
                    "sources": filtered_documents,
                    "metadata": {
                        "documents_found": len(documents),
                        "filtered_sources": len(filtered_documents),
                        "timestamp": datetime.utcnow().isoformat(),
                        "context_used": use_conversational,
                    },
                }
            else:
                answer = await self.llm_service.generate_response(
                    system_prompt=system_prompt,
                    user_message=query,
                    chat_history=chat_history,
                )

                return {
                    "answer": answer,
                    "sources": filtered_documents,
                    "metadata": {
                        "documents_found": len(documents),
                        "filtered_sources": len(filtered_documents),
                        "timestamp": datetime.utcnow().isoformat(),
                        "context_used": use_conversational,
                    },
                }

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise

    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """
        Format chat history into a readable string with token limit consideration.
        
        Args:
            chat_history: List of previous messages
            
        Returns:
            Formatted chat history string limited to recent messages
        """
        if not chat_history:
            return "없음"
        
        # Limit to MAX_HISTORY_MESSAGES most recent messages
        recent_history = chat_history[-MAX_HISTORY_MESSAGES:]
        
        formatted = []
        total_tokens = 0
        
        # Format from most recent to oldest to prioritize recent context
        for msg in reversed(recent_history):
            role = "사용자" if msg["role"] == "user" else "AI"
            message_text = f"{role}: {msg['content']}"
            message_tokens = self._count_tokens(message_text)
            
            # Check if adding this message exceeds token limit
            if total_tokens + message_tokens > MAX_CONTEXT_TOKENS // 2:
                logger.info(
                    "Chat history truncated due to token limit",
                    total_tokens=total_tokens,
                    max_tokens=MAX_CONTEXT_TOKENS // 2
                )
                break
            
            formatted.insert(0, message_text)
            total_tokens += message_tokens
        
        logger.info(
            "Chat history formatted",
            messages_count=len(formatted),
            total_tokens=total_tokens
        )
        
        return "\n".join(formatted)

    async def validate_answer(self, context: str, answer: str) -> Dict[str, Any]:
        """Validate that the answer is grounded in the context."""
        return await self.llm_service.check_hallucination(context, answer)
