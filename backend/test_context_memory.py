"""
Context Memory Agent 테스트 스크립트

이 스크립트는 대화 컨텍스트 유지 기능을 테스트합니다.
테스트 시나리오:
1. "3년차 복지 알려줘" → "그럼 경조사는?" (3년차 유지 확인)
2. 연속 질문 5-6번 → 컨텍스트 유지 확인
3. 새 대화 시작 → 컨텍스트 초기화 확인
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.services.rag_engine import RAGEngine
import structlog

logger = structlog.get_logger()


async def test_context_persistence():
    """Test 1: 컨텍스트 유지 테스트 (3년차 → 경조사)"""
    print("\n" + "=" * 80)
    print("Test 1: 컨텍스트 유지 테스트")
    print("=" * 80)
    
    rag_engine = RAGEngine()
    chat_history = []
    
    # First question
    query1 = "3년차 복지 알려줘"
    print(f"\n[질문 1] {query1}")
    
    result1 = await rag_engine.generate_answer(
        query=query1,
        chat_history=chat_history,
        stream=False,
    )
    
    print(f"\n[답변 1]\n{result1['answer'][:300]}...")
    print(f"\n[메타데이터] 문서 수: {result1['metadata']['documents_found']}, "
          f"컨텍스트 사용: {result1['metadata']['context_used']}")
    
    # Add to history
    chat_history.append({"role": "user", "content": query1})
    chat_history.append({"role": "assistant", "content": result1["answer"]})
    
    # Second question (should maintain "3년차" context)
    query2 = "그럼 경조사 관련해서는?"
    print(f"\n[질문 2] {query2}")
    print(f"[대화 히스토리 길이] {len(chat_history)}")
    
    result2 = await rag_engine.generate_answer(
        query=query2,
        chat_history=chat_history,
        stream=False,
    )
    
    print(f"\n[답변 2]\n{result2['answer'][:300]}...")
    print(f"\n[메타데이터] 문서 수: {result2['metadata']['documents_found']}, "
          f"컨텍스트 사용: {result2['metadata']['context_used']}")
    
    # Check if context is maintained
    if result2['metadata']['context_used']:
        print("\n✅ 컨텍스트가 성공적으로 사용되었습니다!")
    else:
        print("\n⚠️ 경고: 컨텍스트가 사용되지 않았습니다.")
    
    return chat_history


async def test_multiple_turns():
    """Test 2: 연속 질문 테스트 (5-6번)"""
    print("\n" + "=" * 80)
    print("Test 2: 연속 질문 테스트")
    print("=" * 80)
    
    rag_engine = RAGEngine()
    chat_history = []
    
    questions = [
        "연차 사용 방법 알려줘",
        "그럼 몇 일까지 사용 가능해?",
        "반차도 가능한가?",
        "신청은 어떻게 해?",
        "승인은 누가 해?",
        "취소도 가능해?",
    ]
    
    for idx, query in enumerate(questions, 1):
        print(f"\n[질문 {idx}] {query}")
        print(f"[현재 히스토리 길이] {len(chat_history)} 메시지")
        
        result = await rag_engine.generate_answer(
            query=query,
            chat_history=chat_history,
            stream=False,
        )
        
        print(f"[답변 {idx}] {result['answer'][:200]}...")
        print(f"[컨텍스트 사용] {result['metadata']['context_used']}")
        
        chat_history.append({"role": "user", "content": query})
        chat_history.append({"role": "assistant", "content": result["answer"]})
        
        # Simulate delay between questions
        await asyncio.sleep(0.5)
    
    print(f"\n[최종 히스토리 길이] {len(chat_history)} 메시지")
    print("✅ 연속 질문 테스트 완료!")


async def test_context_reset():
    """Test 3: 새 대화 시작 테스트 (컨텍스트 초기화)"""
    print("\n" + "=" * 80)
    print("Test 3: 컨텍스트 초기화 테스트")
    print("=" * 80)
    
    rag_engine = RAGEngine()
    
    # First conversation
    print("\n[대화 1 시작]")
    query1 = "5년차 복지 알려줘"
    print(f"질문: {query1}")
    
    result1 = await rag_engine.generate_answer(
        query=query1,
        chat_history=None,  # No history
        stream=False,
    )
    
    print(f"답변: {result1['answer'][:200]}...")
    print(f"컨텍스트 사용: {result1['metadata']['context_used']}")
    
    # New conversation (should not have context)
    print("\n[대화 2 시작 - 새 세션]")
    query2 = "그럼 10년차는?"
    print(f"질문: {query2}")
    
    result2 = await rag_engine.generate_answer(
        query=query2,
        chat_history=None,  # No history (new session)
        stream=False,
    )
    
    print(f"답변: {result2['answer'][:200]}...")
    print(f"컨텍스트 사용: {result2['metadata']['context_used']}")
    
    if not result2['metadata']['context_used']:
        print("\n✅ 새 대화에서 컨텍스트가 올바르게 초기화되었습니다!")
    else:
        print("\n⚠️ 경고: 새 대화인데 컨텍스트가 사용되었습니다.")


async def test_token_limit():
    """Test 4: 토큰 제한 테스트"""
    print("\n" + "=" * 80)
    print("Test 4: 토큰 제한 테스트")
    print("=" * 80)
    
    rag_engine = RAGEngine()
    
    # Create a long chat history
    chat_history = []
    for i in range(10):
        chat_history.append({
            "role": "user",
            "content": f"질문 {i+1}: 이것은 매우 긴 질문입니다. " * 20
        })
        chat_history.append({
            "role": "assistant",
            "content": f"답변 {i+1}: 이것은 매우 긴 답변입니다. " * 20
        })
    
    print(f"[테스트 히스토리] {len(chat_history)} 메시지 생성")
    
    query = "복지 알려줘"
    print(f"\n[질문] {query}")
    
    result = await rag_engine.generate_answer(
        query=query,
        chat_history=chat_history,
        stream=False,
    )
    
    print(f"\n[답변] {result['answer'][:200]}...")
    print(f"[메타데이터] 컨텍스트 사용: {result['metadata']['context_used']}")
    print("✅ 토큰 제한 테스트 완료 (에러 없이 처리됨)")


async def main():
    """Run all tests"""
    print("\n🚀 Context Memory Agent 테스트 시작\n")
    
    try:
        # Test 1: Context persistence
        await test_context_persistence()
        
        # Test 2: Multiple turns
        await test_multiple_turns()
        
        # Test 3: Context reset
        await test_context_reset()
        
        # Test 4: Token limit
        await test_token_limit()
        
        print("\n" + "=" * 80)
        print("✅ 모든 테스트 완료!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
