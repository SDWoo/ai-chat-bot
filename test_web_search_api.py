"""
웹 검색 API 직접 테스트
"""
import asyncio
import aiohttp
import json
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


async def test_web_search_api():
    """웹 검색 API 직접 테스트"""
    print("=" * 60)
    print("웹 검색 API 테스트")
    print("=" * 60)
    print()
    
    BASE_URL = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # 테스트 1: 웹 검색만 사용
        print("테스트 1: 웹 검색만 사용 (영어)")
        print("-" * 60)
        
        search_data = {
            "query": "Python programming tutorial",
            "sources": ["web"],
            "top_k": 5
        }
        
        try:
            async with session.post(
                f"{BASE_URL}/api/search/unified",
                json=search_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                print(f"상태 코드: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get('results', [])
                    metadata = data.get('metadata', {})
                    
                    print(f"결과 수: {len(results)}")
                    print(f"메타데이터: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
                    print()
                    
                    if results:
                        print("✓ 웹 검색 성공")
                        for idx, result in enumerate(results[:3], 1):
                            print(f"\n결과 {idx}:")
                            print(f"  소스 타입: {result.get('source_type')}")
                            print(f"  제목: {result.get('metadata', {}).get('title', 'N/A')[:100]}")
                            print(f"  점수: {result.get('relevance_score', 0):.4f}")
                    else:
                        print("✗ 웹 검색 결과가 없습니다.")
                else:
                    error_text = await resp.text()
                    print(f"✗ 에러: {error_text}")
        except Exception as e:
            print(f"✗ 예외 발생: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
        
        # 테스트 2: 웹 검색만 사용 (한국어)
        print("\n테스트 2: 웹 검색만 사용 (한국어)")
        print("-" * 60)
        
        search_data = {
            "query": "파이썬 프로그래밍 강좌",
            "sources": ["web"],
            "top_k": 5
        }
        
        try:
            async with session.post(
                f"{BASE_URL}/api/search/unified",
                json=search_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                print(f"상태 코드: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get('results', [])
                    
                    print(f"결과 수: {len(results)}")
                    
                    if results:
                        print("✓ 한국어 웹 검색 성공")
                        for idx, result in enumerate(results[:3], 1):
                            print(f"\n결과 {idx}:")
                            print(f"  제목: {result.get('metadata', {}).get('title', 'N/A')[:100]}")
                    else:
                        print("✗ 웹 검색 결과가 없습니다.")
                else:
                    error_text = await resp.text()
                    print(f"✗ 에러: {error_text}")
        except Exception as e:
            print(f"✗ 예외 발생: {str(e)}")
        
        print("\n" + "=" * 60)
        
        # 테스트 3: 통합 검색 (모든 소스)
        print("\n테스트 3: 통합 검색 (모든 소스)")
        print("-" * 60)
        
        search_data = {
            "query": "FastAPI",
            "sources": ["documents", "knowledge", "web"],
            "top_k": 10
        }
        
        try:
            async with session.post(
                f"{BASE_URL}/api/search/unified",
                json=search_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                print(f"상태 코드: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get('results', [])
                    metadata = data.get('metadata', {})
                    
                    print(f"전체 결과 수: {len(results)}")
                    print(f"소스별 결과 수: {metadata.get('source_counts', {})}")
                    
                    # 소스 타입별 분류
                    source_types = {}
                    for result in results:
                        source_type = result.get('source_type', 'unknown')
                        source_types[source_type] = source_types.get(source_type, 0) + 1
                    
                    print(f"소스별 분포: {source_types}")
                    
                    if 'web' in source_types:
                        print(f"✓ 웹 검색 결과 포함됨: {source_types['web']}개")
                    else:
                        print("ℹ 웹 검색 결과가 통합 검색에 포함되지 않음")
                else:
                    error_text = await resp.text()
                    print(f"✗ 에러: {error_text}")
        except Exception as e:
            print(f"✗ 예외 발생: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_web_search_api())
