#!/usr/bin/env python3
"""
간단한 스트리밍 테스트 스크립트
백엔드 서버가 실행 중일 때 사용
"""

import asyncio
import json
import sys

async def test_streaming():
    """스트리밍 엔드포인트를 테스트합니다."""
    try:
        import httpx
        
        url = "http://localhost:8000/api/chat/stream"
        data = {
            "message": "이 문서의 주요 내용을 간단히 설명해주세요.",
            "top_k": 4
        }
        
        print("🚀 스트리밍 테스트 시작...")
        print(f"URL: {url}")
        print(f"요청: {data['message']}\n")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream('POST', url, json=data) as response:
                print(f"✅ 응답 상태: {response.status_code}")
                print(f"Content-Type: {response.headers.get('content-type')}\n")
                
                if response.status_code != 200:
                    print(f"❌ 에러: {response.status_code}")
                    print(await response.aread())
                    return
                
                print("📝 스트리밍 응답:\n")
                print("-" * 80)
                
                buffer = ""
                async for chunk in response.aiter_bytes():
                    buffer += chunk.decode('utf-8')
                    
                    # SSE 라인 단위로 처리
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if not line or line.startswith(':'):
                            continue
                        
                        if line.startswith('data: '):
                            try:
                                data_str = line[6:]  # 'data: ' 제거
                                data_obj = json.loads(data_str)
                                
                                if data_obj['type'] == 'metadata':
                                    print(f"\n📋 메타데이터:")
                                    print(f"  - Conversation ID: {data_obj['conversation_id']}")
                                    print(f"  - Sources: {len(data_obj['sources'])}개\n")
                                    print("💬 답변:")
                                    
                                elif data_obj['type'] == 'content':
                                    # 실시간으로 출력 (줄바꿈 없이)
                                    print(data_obj['content'], end='', flush=True)
                                    
                                elif data_obj['type'] == 'done':
                                    print("\n\n✅ 스트리밍 완료!")
                                    
                                elif data_obj['type'] == 'error':
                                    print(f"\n\n❌ 에러: {data_obj['message']}")
                                    
                            except json.JSONDecodeError as e:
                                print(f"\n⚠️ JSON 파싱 에러: {e}")
                                print(f"라인: {line}")
                
                print("-" * 80)
                print("\n🎉 테스트 완료!")
                
    except ImportError:
        print("❌ httpx 모듈이 설치되지 않았습니다.")
        print("설치: pip install httpx")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 80)
    print("AI 챗봇 스트리밍 테스트")
    print("=" * 80)
    print()
    
    # 백엔드 서버가 실행 중인지 확인
    try:
        import httpx
        import asyncio
        
        async def check_server():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8000/health", timeout=2.0)
                    return response.status_code == 200
            except:
                return False
        
        if not asyncio.run(check_server()):
            print("⚠️  백엔드 서버가 실행되지 않은 것 같습니다.")
            print("서버 시작: cd backend && uvicorn app.main:app --reload")
            print()
            
    except ImportError:
        pass
    
    # 테스트 실행
    asyncio.run(test_streaming())
