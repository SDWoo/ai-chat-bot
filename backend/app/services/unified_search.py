from typing import List, Dict, Any, Optional
import asyncio
import structlog
from datetime import datetime

from app.services.rag_engine import RAGEngine
from app.services.knowledge_service import KnowledgeService
from app.services.web_search import WebSearchService

logger = structlog.get_logger()


class UnifiedSearchEngine:
    """
    통합 검색 엔진
    - 문서, 지식베이스, 웹에서 병렬 검색
    - 결과 통합 및 가중치 기반 재정렬
    - 멀티소스 검색 결과 제공
    """
    
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.knowledge_service = KnowledgeService()
        self.web_search_service = WebSearchService()
        
        # 소스별 가중치 설정
        self.source_weights = {
            "knowledge_base": 1.2,  # 지식베이스 우선순위 높임
            "documents": 1.0,       # 문서는 기본
            "web": 0.8,            # 웹 검색은 낮춤
        }
    
    async def search(
        self,
        query: str,
        sources: List[str] = ["documents", "knowledge"],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        통합 검색 - 여러 소스에서 병렬 검색 후 통합
        
        Args:
            query: 검색 쿼리
            sources: 검색할 소스 리스트 ["documents", "knowledge", "web"]
            top_k: 반환할 결과 개수
            metadata_filter: 메타데이터 필터 (카테고리, 태그 등)
            
        Returns:
            통합 검색 결과 딕셔너리
        """
        try:
            logger.info(
                "Starting unified search",
                query=query,
                sources=sources,
                top_k=top_k,
            )
            
            start_time = datetime.utcnow()
            
            # 병렬 검색 태스크 생성
            tasks = []
            task_sources = []
            
            if "documents" in sources:
                tasks.append(
                    self._search_documents(query, top_k, metadata_filter, user_id)
                )
                task_sources.append("documents")
            
            if "knowledge" in sources:
                tasks.append(
                    self._search_knowledge(query, top_k, metadata_filter, user_id)
                )
                task_sources.append("knowledge")
            
            if "web" in sources:
                tasks.append(
                    self._search_web(query, top_k)
                )
                task_sources.append("web")
            
            # 병렬 실행
            all_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 수집 (에러 처리)
            source_results = {}
            for source, result in zip(task_sources, all_results):
                if isinstance(result, Exception):
                    logger.error(f"Error searching {source}: {str(result)}")
                    source_results[source] = []
                else:
                    source_results[source] = result
            
            # 결과 통합 및 재정렬
            combined = self._merge_results(source_results)
            reranked = self._rerank_unified(query, combined)
            
            # top_k 개수로 제한
            final_results = reranked[:top_k]
            
            elapsed_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                "Unified search completed",
                total_results=len(final_results),
                sources_searched=task_sources,
                elapsed_seconds=elapsed_time,
            )
            
            return {
                "results": final_results,
                "metadata": {
                    "total_results": len(final_results),
                    "sources_searched": task_sources,
                    "source_counts": {
                        source: len(results) for source, results in source_results.items()
                    },
                    "elapsed_seconds": elapsed_time,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }
            
        except Exception as e:
            logger.error(f"Error in unified search: {str(e)}")
            raise
    
    async def _search_documents(
        self,
        query: str,
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """문서 검색"""
        try:
            filter_merged = dict(metadata_filter) if metadata_filter is not None else {}
            if user_id is not None:
                filter_merged["user_id"] = str(user_id)
            results = await self.rag_engine.search(
                query=query,
                collection_name="documents",
                top_k=top_k,
                metadata_filter=filter_merged if filter_merged else None,
                use_hybrid=True,
            )
            
            # 소스 정보 추가
            for result in results:
                result["source_type"] = "documents"
            
            logger.info(f"Document search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    async def _search_knowledge(
        self,
        query: str,
        top_k: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """지식베이스 검색"""
        try:
            filter_merged = dict(metadata_filter) if metadata_filter is not None else {}
            if user_id is not None:
                filter_merged["user_id"] = str(user_id)
            results = await self.rag_engine.search(
                query=query,
                collection_name="knowledge_base",
                top_k=top_k,
                metadata_filter=filter_merged if filter_merged else None,
                use_hybrid=True,
            )
            
            # 소스 정보 추가
            for result in results:
                result["source_type"] = "knowledge"
            
            logger.info(f"Knowledge search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    async def _search_web(
        self,
        query: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        웹 검색
        DuckDuckGo API를 사용하여 외부 웹 검색 수행
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 개수
            
        Returns:
            웹 검색 결과 리스트
        """
        try:
            if not self.web_search_service.is_enabled():
                logger.warning("Web search service is not enabled")
                return []
            
            results = await self.web_search_service.search_with_fallback(
                query=query,
                max_results=top_k,
                retry_count=2,
            )
            
            # 소스 정보 추가
            for result in results:
                result["source_type"] = "web"
            
            logger.info(f"Web search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching web: {str(e)}")
            return []
    
    def _merge_results(
        self,
        source_results: Dict[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        여러 소스의 결과를 가중치 기반으로 통합
        
        Args:
            source_results: 소스별 검색 결과 딕셔너리
            
        Returns:
            통합된 결과 리스트
        """
        try:
            combined = []
            
            for source, results in source_results.items():
                weight = self.source_weights.get(source, 1.0)
                
                for result in results:
                    # 원본 relevance_score에 가중치 적용
                    original_score = result.get("relevance_score", 0.0)
                    
                    # 점수 정규화: 코사인 유사도(-1 ~ 1)를 0 ~ 1 범위로 변환
                    # 이미 0~1 범위인 경우도 처리
                    if original_score < 0:
                        normalized_score = (original_score + 1) / 2  # -1~1 -> 0~1
                    else:
                        normalized_score = original_score  # 이미 0~1 범위
                    
                    weighted_score = normalized_score * weight
                    
                    result["weighted_score"] = weighted_score
                    result["original_score"] = original_score
                    result["normalized_score"] = normalized_score
                    result["source_weight"] = weight
                    
                    combined.append(result)
            
            # 가중치 점수로 정렬
            combined.sort(key=lambda x: x.get("weighted_score", 0), reverse=True)
            
            logger.info(f"Merged {len(combined)} results from {len(source_results)} sources")
            return combined
            
        except Exception as e:
            logger.error(f"Error merging results: {str(e)}")
            return []
    
    def _rerank_unified(
        self,
        query: str,
        combined_results: List[Dict[str, Any]],
        diversity_factor: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        통합 결과를 재정렬
        - 가중치 점수 기반
        - 소스 다양성 고려
        - 중복 제거
        
        Args:
            query: 검색 쿼리
            combined_results: 통합된 결과 리스트
            diversity_factor: 다양성 가중치 (0.0 ~ 1.0)
            
        Returns:
            재정렬된 결과 리스트
        """
        try:
            if not combined_results:
                return []
            
            # 중복 제거 (내용 유사도 기반)
            deduplicated = self._remove_duplicates(combined_results)
            
            # 소스 다양성 점수 계산
            reranked = []
            source_counts = {}
            
            for result in deduplicated:
                source_type = result.get("source_type", "unknown")
                source_count = source_counts.get(source_type, 0)
                
                # 다양성 패널티 (같은 소스가 많을수록 패널티)
                diversity_penalty = diversity_factor * (source_count / len(deduplicated))
                
                # 최종 점수 = 가중치 점수 - 다양성 패널티
                final_score = result.get("weighted_score", 0) * (1 - diversity_penalty)
                result["final_score"] = final_score
                
                reranked.append(result)
                source_counts[source_type] = source_count + 1
            
            # 최종 점수로 정렬
            reranked.sort(key=lambda x: x.get("final_score", 0), reverse=True)
            
            logger.info(f"Reranked {len(reranked)} results")
            return reranked
            
        except Exception as e:
            logger.error(f"Error reranking results: {str(e)}")
            return combined_results
    
    def _remove_duplicates(
        self,
        results: List[Dict[str, Any]],
        similarity_threshold: float = 0.85,
    ) -> List[Dict[str, Any]]:
        """
        중복 또는 유사한 결과 제거
        
        Args:
            results: 검색 결과 리스트
            similarity_threshold: 유사도 임계값
            
        Returns:
            중복 제거된 결과 리스트
        """
        if not results:
            return []
        
        deduplicated = []
        
        for result in results:
            is_duplicate = False
            result_content = result.get("content", "").lower()
            result_words = set(result_content.split())
            
            for existing in deduplicated:
                existing_content = existing.get("content", "").lower()
                existing_words = set(existing_content.split())
                
                # 동일 소스 및 메타데이터 체크
                same_source = (
                    result.get("source_type") == existing.get("source_type") and
                    result.get("metadata", {}).get("source") == existing.get("metadata", {}).get("source") and
                    result.get("metadata", {}).get("page") == existing.get("metadata", {}).get("page")
                )
                
                if same_source:
                    is_duplicate = True
                    break
                
                # 내용 유사도 계산
                if result_words and existing_words:
                    overlap = len(result_words & existing_words)
                    similarity = overlap / max(len(result_words), len(existing_words))
                    
                    if similarity >= similarity_threshold:
                        # 더 높은 점수의 결과 유지
                        if result.get("weighted_score", 0) > existing.get("weighted_score", 0):
                            deduplicated.remove(existing)
                            break
                        else:
                            is_duplicate = True
                            break
            
            if not is_duplicate:
                deduplicated.append(result)
        
        logger.info(f"Removed {len(results) - len(deduplicated)} duplicates")
        return deduplicated
    
    async def generate_unified_answer(
        self,
        query: str,
        sources: List[str] = ["documents", "knowledge"],
        top_k: int = 10,
        chat_history: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        max_sources: int = 3,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        통합 검색 기반 답변 생성
        
        Args:
            query: 사용자 질문
            sources: 검색할 소스 리스트
            top_k: 검색할 결과 개수
            chat_history: 대화 히스토리
            stream: 스트리밍 여부
            max_sources: 최대 소스 개수
            
        Returns:
            답변 딕셔너리
        """
        try:
            logger.info(
                "Generating unified answer",
                query=query,
                sources=sources,
                stream=stream,
            )
            
            # 통합 검색
            search_result = await self.search(
                query=query,
                sources=sources,
                top_k=top_k,
                user_id=user_id,
            )
            
            results = search_result["results"]
            
            if not results:
                fallback_msg = "죄송합니다. 관련된 정보를 찾을 수 없습니다. 다른 질문을 시도해주세요."
                async def _fallback_stream():
                    yield fallback_msg
                return {
                    "answer": fallback_msg,
                    "answer_stream": _fallback_stream(),
                    "sources": [],
                    "metadata": {
                        "documents_found": 0,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }
            
            # 소스 제한
            limited_results = results[:max_sources]
            
            # 컨텍스트 포맷팅
            context = self._format_unified_context(limited_results)
            
            # RAG 엔진으로 답변 생성
            from app.core.prompts import RAG_SYSTEM_PROMPT, CONVERSATIONAL_SYSTEM_PROMPT
            
            use_conversational = bool(chat_history and len(chat_history) > 0)
            
            if use_conversational:
                formatted_history = self.rag_engine._format_chat_history(chat_history)
                system_prompt = CONVERSATIONAL_SYSTEM_PROMPT.format(
                    chat_history=formatted_history,
                    context=context,
                    question=query,
                )
            else:
                system_prompt = RAG_SYSTEM_PROMPT.format(
                    context=context,
                    question=query,
                )
            
            if stream:
                return {
                    "answer_stream": self.rag_engine.llm_service.generate_streaming_response(
                        system_prompt=system_prompt,
                        user_message=query,
                        chat_history=chat_history,
                    ),
                    "sources": limited_results,
                    "metadata": search_result["metadata"],
                }
            else:
                answer = await self.rag_engine.llm_service.generate_response(
                    system_prompt=system_prompt,
                    user_message=query,
                    chat_history=chat_history,
                )
                
                return {
                    "answer": answer,
                    "sources": limited_results,
                    "metadata": search_result["metadata"],
                }
            
        except Exception as e:
            logger.error(f"Error generating unified answer: {str(e)}")
            raise
    
    def _format_unified_context(self, results: List[Dict[str, Any]]) -> str:
        """
        통합 검색 결과를 컨텍스트 문자열로 포맷팅
        
        Args:
            results: 검색 결과 리스트
            
        Returns:
            포맷된 컨텍스트 문자열
        """
        context_parts = []
        
        for idx, result in enumerate(results, 1):
            source_type = result.get("source_type", "unknown")
            metadata = result.get("metadata", {})
            content = result.get("content", "")
            score = result.get("final_score", result.get("weighted_score", 0))
            
            # 소스별 포맷팅
            if source_type == "knowledge":
                source_label = f"지식베이스: {metadata.get('title', 'Unknown')}"
                category = metadata.get("category", "")
                if category:
                    source_label += f" (카테고리: {category})"
            elif source_type == "documents":
                source_label = f"문서: {metadata.get('source', 'Unknown')}"
                page = metadata.get("page", "")
                if page:
                    source_label += f" (페이지: {page})"
            elif source_type == "web":
                source_label = f"웹: {metadata.get('title', 'Unknown')}"
                url = metadata.get("url", "")
                if url:
                    source_label += f"\nURL: {url}"
            else:
                source_label = f"{source_type}: {metadata.get('source', 'Unknown')}"
            
            context_parts.append(
                f"[출처 {idx}] {source_label} (관련도: {score:.2f})\n"
                f"내용:\n{content}\n"
            )
        
        separator = "\n" + "=" * 80 + "\n"
        return separator.join(context_parts)
