"""
웹 검색 서비스
DuckDuckGo API를 사용한 외부 웹 검색 기능 제공
"""
from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime

logger = structlog.get_logger()


class WebSearchService:
    """
    웹 검색 서비스
    - DuckDuckGo 검색 API 사용 (무료, API 키 불필요)
    - 검색 결과 포맷팅
    - 에러 처리 및 재시도 로직
    """
    
    def __init__(self):
        """웹 검색 서비스 초기화"""
        try:
            from duckduckgo_search import DDGS
            self.ddgs = DDGS()
            self.enabled = True
            logger.info("WebSearchService initialized successfully")
        except ImportError:
            logger.warning(
                "duckduckgo-search not installed. Web search will be disabled. "
                "Install with: poetry add duckduckgo-search"
            )
            self.enabled = False
        except Exception as e:
            logger.error(f"Error initializing WebSearchService: {str(e)}")
            self.enabled = False
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        region: str = "kr-kr",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        웹 검색 수행
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 개수
            region: 지역 설정 (kr-kr: 한국)
            safesearch: 세이프서치 설정 (on, moderate, off)
            timelimit: 시간 제한 (d: 하루, w: 일주일, m: 한 달, y: 1년)
            
        Returns:
            검색 결과 리스트
        """
        if not self.enabled:
            logger.warning("Web search is disabled")
            return []
        
        try:
            logger.info(
                "Starting web search",
                query=query,
                max_results=max_results,
                region=region,
            )
            
            start_time = datetime.utcnow()
            
            # DuckDuckGo 검색 수행 (동기 메서드이므로 직접 호출)
            results = self.ddgs.text(
                keywords=query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                max_results=max_results,
            )
            
            # 결과 포맷팅
            formatted_results = []
            for idx, result in enumerate(results):
                formatted_result = self._format_result(result, idx)
                formatted_results.append(formatted_result)
            
            elapsed_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                "Web search completed",
                results_count=len(formatted_results),
                elapsed_seconds=elapsed_time,
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during web search: {str(e)}")
            return []
    
    def _format_result(self, result: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        검색 결과를 RAG 시스템 형식으로 포맷팅
        
        Args:
            result: DuckDuckGo 검색 결과
            index: 결과 인덱스
            
        Returns:
            포맷된 결과 딕셔너리
        """
        try:
            # DuckDuckGo 결과 구조:
            # {
            #   'title': str,
            #   'href': str,
            #   'body': str,
            # }
            
            title = result.get("title", "제목 없음")
            url = result.get("href", "")
            snippet = result.get("body", "")
            
            # RAG 시스템 형식으로 변환
            formatted = {
                "content": f"{title}\n\n{snippet}",
                "metadata": {
                    "source": url,
                    "title": title,
                    "page": "N/A",
                    "type": "web",
                    "url": url,
                    "rank": index + 1,
                },
                "relevance_score": 1.0 - (index * 0.05),  # 순위 기반 점수
                "source_type": "web",
            }
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting result: {str(e)}")
            return {
                "content": str(result),
                "metadata": {"source": "Unknown", "page": "N/A", "type": "web"},
                "relevance_score": 0.5,
                "source_type": "web",
            }
    
    async def search_with_fallback(
        self,
        query: str,
        max_results: int = 10,
        retry_count: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        재시도 로직이 포함된 웹 검색
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 개수
            retry_count: 재시도 횟수
            
        Returns:
            검색 결과 리스트
        """
        for attempt in range(retry_count + 1):
            try:
                results = await self.search(query, max_results)
                if results:
                    return results
                
                if attempt < retry_count:
                    logger.warning(
                        f"Web search returned no results. Retrying... ({attempt + 1}/{retry_count})"
                    )
                    
            except Exception as e:
                if attempt < retry_count:
                    logger.warning(
                        f"Web search failed. Retrying... ({attempt + 1}/{retry_count}): {str(e)}"
                    )
                else:
                    logger.error(f"Web search failed after {retry_count + 1} attempts: {str(e)}")
        
        return []
    
    def is_enabled(self) -> bool:
        """
        웹 검색 기능 활성화 여부 확인
        
        Returns:
            활성화 여부
        """
        return self.enabled
