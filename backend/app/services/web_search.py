"""
웹 검색 서비스
DuckDuckGo API를 사용한 외부 웹 검색 기능 제공
"""
from typing import List, Dict, Any, Optional
import asyncio
import structlog
from datetime import datetime

logger = structlog.get_logger()

# Ratelimit 시 재시도할 지역 (wt-wt=전세계, us-en=미국)
REGION_FALLBACKS = ["kr-kr", "wt-wt", "us-en", "jp-jp"]


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
        Ratelimit 시 지역 변경 및 재시도
        """
        if not self.enabled:
            logger.warning("Web search is disabled")
            return []

        regions_to_try = [region] + [r for r in REGION_FALLBACKS if r != region]
        last_error = None

        for try_region in regions_to_try:
            try:
                logger.info(
                    "Starting web search",
                    query=query,
                    max_results=max_results,
                    region=try_region,
                )
                start_time = datetime.utcnow()

                # 동기 호출을 이벤트 루프에서 분리 (블로킹 방지)
                loop = asyncio.get_event_loop()
                reg = try_region
                results = await loop.run_in_executor(
                    None,
                    lambda r=reg: list(
                        self.ddgs.text(
                            keywords=query,
                            region=r,
                            safesearch=safesearch,
                            timelimit=timelimit,
                            max_results=max_results,
                        )
                    ),
                )

                formatted_results = []
                for idx, result in enumerate(results):
                    formatted_result = self._format_result(result, idx)
                    formatted_results.append(formatted_result)

                elapsed_time = (datetime.utcnow() - start_time).total_seconds()
                logger.info(
                    "Web search completed",
                    results_count=len(formatted_results),
                    region=try_region,
                    elapsed_seconds=elapsed_time,
                )
                return formatted_results

            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                is_ratelimit = "ratelimit" in error_str or "rate limit" in error_str

                if is_ratelimit and try_region != regions_to_try[-1]:
                    wait_sec = 3
                    logger.warning(
                        f"Web search ratelimit (region={try_region}), "
                        f"waiting {wait_sec}s then retry with different region"
                    )
                    await asyncio.sleep(wait_sec)
                else:
                    logger.error(f"Error during web search (region={try_region}): {str(e)}")
                    if not is_ratelimit:
                        break

        logger.error(f"Web search failed after all retries: {last_error}")
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
            url = result.get("href") or result.get("url", "")
            snippet = result.get("body") or result.get("snippet") or result.get("content", "")
            
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
        재시도 로직이 포함된 웹 검색 (Ratelimit 대응)
        """
        for attempt in range(retry_count + 1):
            try:
                results = await self.search(query, max_results)
                if results:
                    return results

                if attempt < retry_count:
                    wait_sec = 2 * (attempt + 1)
                    logger.warning(
                        f"Web search returned no results. "
                        f"Retrying in {wait_sec}s ({attempt + 1}/{retry_count})"
                    )
                    await asyncio.sleep(wait_sec)

            except Exception as e:
                if attempt < retry_count:
                    wait_sec = 3 * (attempt + 1)
                    logger.warning(
                        f"Web search failed. Retrying in {wait_sec}s "
                        f"({attempt + 1}/{retry_count}): {str(e)}"
                    )
                    await asyncio.sleep(wait_sec)
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
