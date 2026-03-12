from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownTextSplitter
from langchain.schema import Document
from typing import List, Optional
import structlog
import tiktoken

from app.core.config import settings

logger = structlog.get_logger()


class ChunkingService:
    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
        model_name: str = "gpt-4",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name
        
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # 구조 인식 분리자: 섹션 → 단락 → 문장 → 단어 순으로 자연 경계 유지
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._tiktoken_length,
            separators=["\n## ", "\n# ", "\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
        )
        
        # Markdown-specific splitter
        self.markdown_splitter = MarkdownTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._tiktoken_length,
        )

    def _tiktoken_length(self, text: str) -> int:
        """Calculate the number of tokens in a text using tiktoken."""
        tokens = self.encoding.encode(text, disallowed_special=())
        return len(tokens)

    def chunk_documents(
        self, documents: List[Document], document_id: Optional[int] = None
    ) -> List[Document]:
        """
        Split documents into smaller chunks while preserving metadata and context.
        
        Uses RecursiveCharacterTextSplitter with structure-aware separators.
        For Markdown files, uses MarkdownTextSplitter to preserve document structure.
        """
        try:
            logger.info(
                "Starting document chunking",
                num_documents=len(documents),
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )

            chunks = []
            for doc_idx, doc in enumerate(documents):
                file_type = doc.metadata.get("file_type", "")
                if file_type == ".md":
                    doc_chunks = self.markdown_splitter.split_documents([doc])
                    logger.debug(f"Using MarkdownTextSplitter for document {doc_idx}")
                else:
                    doc_chunks = self.text_splitter.split_documents([doc])
                
                for chunk_idx, chunk in enumerate(doc_chunks):
                    # document_id 포함 시 삭제 시 벡터 추적 가능
                    base_id = f"doc_{document_id}" if document_id is not None else doc.metadata.get("source", "unknown")
                    chunk_id = f"{base_id}_{doc_idx}_{chunk_idx}"
                    chunk.metadata["chunk_id"] = chunk_id
                    
                    chunk.metadata.update({
                        "chunk_index": chunk_idx,
                        "total_chunks": len(doc_chunks),
                        "document_index": doc_idx,
                        "chunk_size": self._tiktoken_length(chunk.page_content),
                    })
                    if document_id is not None:
                        chunk.metadata["document_id"] = str(document_id)
                    
                    if chunk_idx > 0:
                        chunk.metadata["previous_chunk"] = doc_chunks[chunk_idx - 1].metadata.get("chunk_id", "")
                    
                chunks.extend(doc_chunks)

            logger.info(
                "Document chunking completed",
                num_documents=len(documents),
                num_chunks=len(chunks),
                avg_chunk_size=sum(self._tiktoken_length(c.page_content) for c in chunks) / len(chunks) if chunks else 0,
            )

            return chunks

        except Exception as e:
            logger.error(f"Error during document chunking: {str(e)}")
            raise

    def chunk_text(self, text: str, metadata: dict = None) -> List[Document]:
        """
        Chunk a single text string into documents.
        Useful for processing text that doesn't come from a file.
        """
        try:
            doc = Document(page_content=text, metadata=metadata or {})
            return self.chunk_documents([doc])
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise

    def get_optimal_chunk_params(self, documents: List[Document]) -> dict:
        """
        Analyze documents and suggest optimal chunking parameters.
        This can be used for adaptive chunking strategies.
        """
        total_length = sum(len(doc.page_content) for doc in documents)
        avg_doc_length = total_length / len(documents) if documents else 0
        
        total_tokens = sum(self._tiktoken_length(doc.page_content) for doc in documents)
        avg_tokens = total_tokens / len(documents) if documents else 0
        
        suggested_chunk_size = min(1000, max(500, int(avg_tokens / 3)))
        suggested_overlap = int(suggested_chunk_size * 0.2)
        
        return {
            "total_documents": len(documents),
            "total_characters": total_length,
            "total_tokens": total_tokens,
            "avg_document_tokens": avg_tokens,
            "suggested_chunk_size": suggested_chunk_size,
            "suggested_overlap": suggested_overlap,
            "current_chunk_size": self.chunk_size,
            "current_overlap": self.chunk_overlap,
        }
