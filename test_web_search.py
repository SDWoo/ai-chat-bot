"""
웹 검색 서비스 단위 테스트
"""
import asyncio
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 백엔드 모듈 임포트를 위한 경로 추가
sys.path.insert(0, 'backend')

from app.services.web_search import WebSearchService


async def test_web_search():
    """웹 검색 서비스 직접 테스트"""
    print("=" * 60)
    print("웹 검색 서비스 단위 테스트")
    print("=" * 60)
    print()
    
    service = WebSearchService()
    
    # 1. 서비스 활성화 상태 확인
    print(f"웹 검색 서비스 활성화: {service.is_enabled()}")
    
    if not service.is_enabled():
        print("✗ 웹 검색 서비스가 비활성화되어 있습니다.")
        print("duckduckgo-search 패키지가 설치되어 있는지 확인하세요.")
        return
    
    print("✓ 웹 검색 서비스가 활성화되었습니다.")
    print()
    
    # 2. 간단한 검색 테스트
    print("테스트 1: 간단한 검색")
    print("-" * 60)
    
    try:
        results = await service.search(
            query="Python programming",
            max_results=3,
            region="wt-wt",  # 전세계
        )
        
        print(f"검색 결과 수: {len(results)}")
        
        if results:
            print("✓ 웹 검색 성공")
            print()
            for idx, result in enumerate(results, 1):
                print(f"결과 {idx}:")
                print(f"  제목: {result.get('metadata', {}).get('title', 'N/A')}")
                print(f"  URL: {result.get('metadata', {}).get('url', 'N/A')}")
                print(f"  점수: {result.get('relevance_score', 0):.2f}")
                print()
        else:
            print("✗ 검색 결과가 없습니다.")
            
    except Exception as e:
        print(f"✗ 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 3. 한국어 검색 테스트
    print("테스트 2: 한국어 검색")
    print("-" * 60)
    
    try:
        results = await service.search(
            query="파이썬 프로그래밍",
            max_results=3,
            region="kr-kr",
        )
        
        print(f"검색 결과 수: {len(results)}")
        
        if results:
            print("✓ 한국어 검색 성공")
            print()
            for idx, result in enumerate(results, 1):
                print(f"결과 {idx}:")
                print(f"  제목: {result.get('metadata', {}).get('title', 'N/A')}")
                print(f"  URL: {result.get('metadata', {}).get('url', 'N/A')}")
                print()
        else:
            print("✗ 검색 결과가 없습니다.")
            
    except Exception as e:
        print(f"✗ 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 4. 재시도 로직 테스트
    print("테스트 3: 재시도 로직")
    print("-" * 60)
    
    try:
        results = await service.search_with_fallback(
            query="FastAPI tutorial",
            max_results=5,
            retry_count=2,
        )
        
        print(f"검색 결과 수: {len(results)}")
        
        if results:
            print("✓ 재시도 로직 성공")
        else:
            print("✗ 재시도 후에도 결과가 없습니다.")
            
    except Exception as e:
        print(f"✗ 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_web_search())
