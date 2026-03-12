#!/usr/bin/env python3
"""
지식 기반 시스템 통합 테스트 스크립트
"""
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"

def print_section(title: str):
    """섹션 헤더 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def test_health():
    """Health check 테스트"""
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/../api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.status_code == 200

def test_create_knowledge():
    """지식 항목 생성 테스트"""
    print_section("2. 지식 항목 생성")
    
    data = {
        "title": "Docker 컨테이너 메모리 부족 에러 해결",
        "content": """
Docker 컨테이너에서 OOM(Out of Memory) 에러가 발생할 때 해결 방법:

1. 메모리 제한 확인
   - docker stats 명령어로 현재 메모리 사용량 확인
   - docker inspect로 메모리 제한 확인

2. 메모리 증가
   - docker-compose.yml에서 mem_limit 설정 증가
   - 예: mem_limit: 2g

3. 애플리케이션 최적화
   - 메모리 누수 확인 및 수정
   - 불필요한 캐시 제거
   - 가비지 컬렉션 튜닝

4. 스왑 메모리 사용
   - --memory-swap 옵션 추가
   - 예: --memory-swap=4g
        """.strip(),
        "author": "테스트 관리자",
        "status": "published"
    }
    
    response = requests.post(f"{BASE_URL}/knowledge", json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"Created Knowledge Entry:")
        print(f"  ID: {result['id']}")
        print(f"  Title: {result['title']}")
        print(f"  Category: {result['category']}")
        print(f"  Tags: {result['tags']}")
        print(f"  Chunks: {result['num_chunks']}")
        return result['id']
    else:
        print(f"Error: {response.text}")
        return None

def test_list_knowledge():
    """지식 항목 목록 조회 테스트"""
    print_section("3. 지식 항목 목록 조회")
    
    response = requests.get(f"{BASE_URL}/knowledge")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        entries = response.json()
        print(f"Total Entries: {len(entries)}")
        for entry in entries:
            print(f"\n- {entry['title']}")
            print(f"  Category: {entry['category']}, Tags: {entry['tags']}")
    else:
        print(f"Error: {response.text}")

def test_unified_search(query: str):
    """통합 검색 테스트"""
    print_section(f"4. 통합 검색: '{query}'")
    
    data = {
        "query": query,
        "sources": ["documents", "knowledge"],
        "top_k": 5
    }
    
    response = requests.post(f"{BASE_URL}/search/unified", json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nMetadata:")
        print(f"  Total Results: {result['metadata']['total_results']}")
        print(f"  Sources Searched: {result['metadata']['sources_searched']}")
        print(f"  Elapsed: {result['metadata']['elapsed_seconds']:.3f}s")
        
        print(f"\nTop Results:")
        for idx, res in enumerate(result['results'][:3], 1):
            print(f"\n{idx}. Source Type: {res.get('source_type', 'unknown')}")
            print(f"   Score: {res.get('final_score', res.get('weighted_score', 0)):.4f}")
            print(f"   Content: {res['content'][:100]}...")
    else:
        print(f"Error: {response.text}")

def test_chat_with_unified_search():
    """통합 검색을 사용한 채팅 테스트"""
    print_section("5. 통합 검색 채팅")
    
    data = {
        "message": "Docker 컨테이너에서 메모리 부족 에러가 발생하면 어떻게 해결하나요?",
        "search_sources": ["documents", "knowledge"],
        "top_k": 5
    }
    
    print(f"Query: {data['message']}")
    response = requests.post(f"{BASE_URL}/chat", json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nConversation ID: {result['conversation_id']}")
        print(f"\nAnswer:\n{result['message']}")
        print(f"\nSources: {len(result['sources'])} documents")
    else:
        print(f"Error: {response.text}")

def test_categories():
    """카테고리 관리 테스트"""
    print_section("6. 카테고리 조회")
    
    # 수정: 올바른 API 경로 사용
    response = requests.get(f"{BASE_URL}/knowledge/categories")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        categories = response.json()
        print(f"Total Categories: {len(categories)}")
        for cat in categories:
            print(f"- {cat['name']}: {cat.get('description', 'N/A')}")
    else:
        print(f"Error: {response.text}")

def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 80)
    print("  지식 기반 시스템 통합 테스트")
    print("=" * 80)
    
    try:
        # 1. Health Check
        if not test_health():
            print("\n[ERROR] Health check failed. Backend may not be running.")
            return
        
        # 2. 지식 항목 생성
        entry_id = test_create_knowledge()
        if entry_id:
            print(f"\n[SUCCESS] Knowledge entry created with ID: {entry_id}")
            time.sleep(2)  # 벡터 임베딩 완료 대기
        
        # 3. 지식 항목 목록 조회
        test_list_knowledge()
        
        # 4. 통합 검색
        test_unified_search("Docker 메모리 부족")
        
        # 5. 통합 검색 채팅
        test_chat_with_unified_search()
        
        # 6. 카테고리
        test_categories()
        
        print("\n" + "=" * 80)
        print("  테스트 완료!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
