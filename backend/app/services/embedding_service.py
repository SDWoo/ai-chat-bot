from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
import structlog
import hashlib
import json
from redis import Redis
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = structlog.get_logger()


class EmbeddingService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        
        try:
            self.redis_client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=False,
            )
            self.cache_enabled = True
            logger.info("Redis cache enabled for embeddings")
        except Exception as e:
            logger.warning(f"Redis connection failed, caching disabled: {str(e)}")
            self.cache_enabled = False

    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for the given text."""
        return f"embedding:{hashlib.sha256(text.encode()).hexdigest()}"

    def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Retrieve embedding from cache if available."""
        if not self.cache_enabled:
            return None
        
        try:
            cache_key = self._get_cache_key(text)
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {str(e)}")
        
        return None

    def _cache_embedding(self, text: str, embedding: List[float], ttl: int = 86400 * 7):
        """Cache an embedding with TTL (default 7 days for documents, 1 day for queries)."""
        if not self.cache_enabled:
            return
        
        try:
            cache_key = self._get_cache_key(text)
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(embedding),
            )
        except Exception as e:
            logger.warning(f"Cache storage failed: {str(e)}")

    def embed_query(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding for a query with shorter TTL (1 day)."""
        try:
            if use_cache:
                cached = self._get_cached_embedding(text)
                if cached:
                    logger.debug("Cache hit for query embedding")
                    return cached

            embedding = self.embeddings.embed_query(text)
            
            if use_cache:
                # Shorter TTL for queries (1 day)
                self._cache_embedding(text, embedding, ttl=86400)
            
            return embedding

        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding for a single text with caching and retry logic."""
        try:
            if use_cache:
                cached = self._get_cached_embedding(text)
                if cached:
                    logger.debug("Cache hit for embedding")
                    return cached

            embedding = self.embeddings.embed_query(text)
            
            if use_cache:
                self._cache_embedding(text, embedding)
            
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def embed_documents(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        This is more efficient than calling embed_text for each document.
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self.embeddings.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
                
                logger.debug(f"Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
            return all_embeddings

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise

    def create_vector_store(
        self,
        documents: List[Document],
        collection_name: str = "documents",
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> Chroma:
        """
        Create a vector store from documents and add them to ChromaDB.
        """
        try:
            logger.info(
                f"Creating vector store",
                collection=collection_name,
                num_documents=len(documents),
            )

            vector_store = Chroma(
                client=self.chroma_client,
                collection_name=collection_name,
                embedding_function=self.embeddings,
            )

            if documents:
                texts = [doc.page_content for doc in documents]
                metadatas = [doc.metadata for doc in documents]
                
                vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                )

            logger.info(f"Vector store created successfully", collection=collection_name)
            return vector_store

        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise

    def get_vector_store(self, collection_name: str = "documents") -> Chroma:
        """Get an existing vector store."""
        try:
            vector_store = Chroma(
                client=self.chroma_client,
                collection_name=collection_name,
                embedding_function=self.embeddings,
            )
            return vector_store
        except Exception as e:
            logger.error(f"Error getting vector store: {str(e)}")
            raise

    def add_documents_to_store(
        self,
        documents: List[Document],
        collection_name: str = "documents",
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add documents to an existing vector store. Custom ids enable reliable deletion."""
        try:
            logger.info(
                f"Adding documents to vector store",
                collection=collection_name,
                num_documents=len(documents),
            )

            vector_store = self.get_vector_store(collection_name)
            
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # ChromaDB 메타데이터는 str/int/float/bool만 허용
            safe_metadatas = []
            for m in metadatas:
                safe = {}
                for k, v in m.items():
                    if v is None:
                        continue
                    if isinstance(v, (str, int, float, bool)):
                        safe[k] = v
                    else:
                        safe[k] = str(v)
                safe_metadatas.append(safe)
            
            add_kwargs = {"texts": texts, "metadatas": safe_metadatas}
            if ids:
                add_kwargs["ids"] = ids
            
            result_ids = vector_store.add_texts(**add_kwargs)

            logger.info(f"Added {len(result_ids)} documents to vector store")
            return result_ids

        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise

    def delete_documents(
        self,
        document_ids: List[str],
        collection_name: str = "documents",
    ):
        """Delete documents from vector store by IDs."""
        try:
            vector_store = self.get_vector_store(collection_name)
            vector_store.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents from vector store")
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise

    def list_collections(self) -> List[str]:
        """List all collections in ChromaDB."""
        try:
            collections = self.chroma_client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            raise

    def delete_collection(self, collection_name: str):
        """Delete an entire collection."""
        try:
            self.chroma_client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise
