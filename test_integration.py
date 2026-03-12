"""
통합 테스트 스크립트
모든 신규 기능을 자동으로 테스트하고 버그를 발견
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any
from datetime import datetime
import sys
import io

# Windows 환경에서 유니코드 출력 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 테스트 설정
BACKEND_URL = "http://localhost:8000"
TEST_RESULTS = []


class TestResult:
    def __init__(self, category: str, test_name: str, status: str, details: str = "", severity: str = ""):
        self.category = category
        self.test_name = test_name
        self.status = status  # PASS, FAIL, WARNING
        self.details = details
        self.severity = severity  # Critical, High, Medium, Low
        self.timestamp = datetime.now().isoformat()


async def test_backend_health():
    """백엔드 헬스 체크"""
    print("\n🏥 [1/10] 백엔드 헬스 체크...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/health", timeout=5) as response:
                if response.status == 200:
                    TEST_RESULTS.append(TestResult(
                        "시스템", "백엔드 헬스 체크", "PASS", "백엔드 정상 작동"
                    ))
                    print("   ✅ 백엔드 정상")
                    return True
                else:
                    TEST_RESULTS.append(TestResult(
                        "시스템", "백엔드 헬스 체크", "FAIL", 
                        f"상태 코드: {response.status}", "Critical"
                    ))
                    print("   ❌ 백엔드 오류")
                    return False
    except Exception as e:
        TEST_RESULTS.append(TestResult(
            "시스템", "백엔드 헬스 체크", "FAIL", str(e), "Critical"
        ))
        print(f"   ❌ 연결 실패: {e}")
        return False


async def test_conversation_creation():
    """새 대화 생성 테스트"""
    print("\n💬 [2/10] 새 대화 생성 테스트...")
    try:
        async with aiohttp.ClientSession() as session:
            # 새 대화 시작 (conversation_id 없이 요청)
            payload = {
                "message": "안녕하세요, 테스트 메시지입니다.",
                "top_k": 4
            }
            
            async with session.post(
                f"{BACKEND_URL}/api/chat/stream",
                json=payload,
                timeout=30
            ) as response:
                if response.status != 200:
                    TEST_RESULTS.append(TestResult(
                        "채팅 히스토리", "새 대화 생성", "FAIL",
                        f"상태 코드: {response.status}", "High"
                    ))
                    print(f"   ❌ 요청 실패: {response.status}")
                    return None
                
                conversation_id = None
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if data.get('type') == 'metadata':
                            conversation_id = data.get('conversation_id')
                            break
                
                if conversation_id:
                    TEST_RESULTS.append(TestResult(
                        "채팅 히스토리", "새 대화 생성", "PASS",
                        f"대화 ID: {conversation_id}"
                    ))
                    print(f"   ✅ 대화 생성 성공: {conversation_id}")
                    return conversation_id
                else:
                    TEST_RESULTS.append(TestResult(
                        "채팅 히스토리", "새 대화 생성", "FAIL",
                        "conversation_id를 받지 못함", "High"
                    ))
                    print("   ❌ conversation_id 누락")
                    return None
                    
    except Exception as e:
        TEST_RESULTS.append(TestResult(
            "채팅 히스토리", "새 대화 생성", "FAIL", str(e), "High"
        ))
        print(f"   ❌ 오류: {e}")
        return None


async def test_conversation_list():
    """대화 목록 조회 테스트"""
    print("\n📋 [3/10] 대화 목록 조회 테스트...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BACKEND_URL}/api/conversations",
                timeout=10
            ) as response:
                if response.status == 200:
                    conversations = await response.json()
                    TEST_RESULTS.append(TestResult(
                        "채팅 히스토리", "대화 목록 조회", "PASS",
                        f"총 {len(conversations)}개 대화 발견"
                    ))
                    print(f"   ✅ 대화 목록 조회 성공: {len(conversations)}개")
                    return conversations
                else:
                    TEST_RESULTS.append(TestResult(
                        "채팅 히스토리", "대화 목록 조회", "FAIL",
                        f"상태 코드: {response.status}", "Medium"
                    ))
                    print(f"   ❌ 조회 실패: {response.status}")
                    return []
    except Exception as e:
        TEST_RESULTS.append(TestResult(
            "채팅 히스토리", "대화 목록 조회", "FAIL", str(e), "Medium"
        ))
        print(f"   ❌ 오류: {e}")
        return []


async def test_streaming_response():
    """스트리밍 응답 테스트"""
    print("\n⚡ [4/10] 스트리밍 응답 테스트...")
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "message": "간단한 테스트 질문입니다.",
                "top_k": 4
            }
            
            start_time = datetime.now()
            first_chunk_time = None
            chunks_received = 0
            
            async with session.post(
                f"{BACKEND_URL}/api/chat/stream",
                json=payload,
                timeout=30
            ) as response:
                if response.status != 200:
                    TEST_RESULTS.append(TestResult(
                        "스트리밍 응답", "스트리밍 요청", "FAIL",
                        f"상태 코드: {response.status}", "High"
                    ))
                    print(f"   ❌ 요청 실패: {response.status}")
                    return False
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        
                        if first_chunk_time is None:
                            first_chunk_time = datetime.now()
                        
                        if data.get('type') == 'content':
                            chunks_received += 1
                        elif data.get('type') == 'done':
                            end_time = datetime.now()
                            first_response = (first_chunk_time - start_time).total_seconds()
                            total_time = (end_time - start_time).total_seconds()
                            
                            if first_response <= 2.0:
                                TEST_RESULTS.append(TestResult(
                                    "스트리밍 응답", "첫 응답 시간", "PASS",
                                    f"{first_response:.2f}초 (목표: ≤2초)"
                                ))
                                print(f"   ✅ 첫 응답 시간: {first_response:.2f}초")
                            else:
                                TEST_RESULTS.append(TestResult(
                                    "스트리밍 응답", "첫 응답 시간", "WARNING",
                                    f"{first_response:.2f}초 (목표: ≤2초)", "Medium"
                                ))
                                print(f"   ⚠️ 첫 응답 시간 느림: {first_response:.2f}초")
                            
                            TEST_RESULTS.append(TestResult(
                                "스트리밍 응답", "청크 수신", "PASS",
                                f"총 {chunks_received}개 청크, 총 시간: {total_time:.2f}초"
                            ))
                            print(f"   ✅ 청크 수신: {chunks_received}개")
                            return True
                
                TEST_RESULTS.append(TestResult(
                    "스트리밍 응답", "스트리밍 완료", "FAIL",
                    "done 신호를 받지 못함", "High"
                ))
                print("   ❌ 스트리밍 미완료")
                return False
                
    except Exception as e:
        TEST_RESULTS.append(TestResult(
            "스트리밍 응답", "스트리밍 테스트", "FAIL", str(e), "High"
        ))
        print(f"   ❌ 오류: {e}")
        return False


async def test_context_memory(conversation_id: str):
    """컨텍스트 메모리 테스트"""
    print("\n🧠 [5/10] 컨텍스트 메모리 테스트...")
    
    questions = [
        "3년차 직원 복지에 대해 알려주세요.",
        "그럼 경조사 관련 복지는 어떻게 되나요?",
        "연차는 몇일인가요?"
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            for i, question in enumerate(questions):
                print(f"   질문 {i+1}: {question}")
                
                payload = {
                    "message": question,
                    "conversation_id": conversation_id,
                    "top_k": 4
                }
                
                async with session.post(
                    f"{BACKEND_URL}/api/chat/stream",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        TEST_RESULTS.append(TestResult(
                            "컨텍스트 유지", f"질문 {i+1}", "FAIL",
                            f"상태 코드: {response.status}", "High"
                        ))
                        print(f"   ❌ 요청 실패")
                        return False
                    
                    answer = ""
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data = json.loads(line[6:])
                            if data.get('type') == 'content':
                                answer += data.get('content', '')
                            elif data.get('type') == 'done':
                                break
                    
                    print(f"   응답 받음 ({len(answer)}자)")
                    
                    # 2번째, 3번째 질문에서 컨텍스트 검증
                    if i > 0:
                        # "3년차" 언급 여부 확인
                        if "3년차" in answer or "3년" in answer or "해당" in answer:
                            TEST_RESULTS.append(TestResult(
                                "컨텍스트 유지", f"질문 {i+1} 컨텍스트 유지", "PASS",
                                "이전 대화 내용 반영됨"
                            ))
                            print(f"   ✅ 컨텍스트 유지 확인")
                        else:
                            TEST_RESULTS.append(TestResult(
                                "컨텍스트 유지", f"질문 {i+1} 컨텍스트 유지", "WARNING",
                                "이전 대화 내용이 명시적으로 반영되지 않음", "Medium"
                            ))
                            print(f"   ⚠️ 컨텍스트 유지 불확실")
                
                # 다음 질문 전 짧은 대기
                await asyncio.sleep(1)
        
        TEST_RESULTS.append(TestResult(
            "컨텍스트 유지", "연속 질문 테스트", "PASS",
            f"{len(questions)}개 질문 완료"
        ))
        print(f"   ✅ 연속 질문 테스트 완료")
        return True
        
    except Exception as e:
        TEST_RESULTS.append(TestResult(
            "컨텍스트 유지", "컨텍스트 메모리", "FAIL", str(e), "High"
        ))
        print(f"   ❌ 오류: {e}")
        return False


async def test_message_retrieval(conversation_id: str):
    """메시지 조회 테스트"""
    print("\n📨 [6/10] 메시지 조회 테스트...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BACKEND_URL}/api/conversations/{conversation_id}/messages",
                timeout=10
            ) as response:
                if response.status == 200:
                    messages = await response.json()
                    TEST_RESULTS.append(TestResult(
                        "채팅 히스토리", "메시지 조회", "PASS",
                        f"총 {len(messages)}개 메시지"
                    ))
                    print(f"   ✅ 메시지 조회 성공: {len(messages)}개")
                    
                    # 메시지 순서 확인
                    if len(messages) >= 2:
                        first = datetime.fromisoformat(messages[0]['created_at'].replace('Z', '+00:00'))
                        last = datetime.fromisoformat(messages[-1]['created_at'].replace('Z', '+00:00'))
                        if first <= last:
                            TEST_RESULTS.append(TestResult(
                                "채팅 히스토리", "메시지 순서", "PASS",
                                "시간순 정렬 확인"
                            ))
                            print(f"   ✅ 메시지 순서 정상")
                        else:
                            TEST_RESULTS.append(TestResult(
                                "채팅 히스토리", "메시지 순서", "FAIL",
                                "시간순 정렬 오류", "Low"
                            ))
                            print(f"   ❌ 메시지 순서 오류")
                    
                    return messages
                else:
                    TEST_RESULTS.append(TestResult(
                        "채팅 히스토리", "메시지 조회", "FAIL",
                        f"상태 코드: {response.status}", "Medium"
                    ))
                    print(f"   ❌ 조회 실패: {response.status}")
                    return []
    except Exception as e:
        TEST_RESULTS.append(TestResult(
            "채팅 히스토리", "메시지 조회", "FAIL", str(e), "Medium"
        ))
        print(f"   ❌ 오류: {e}")
        return []


async def test_conversation_title():
    """대화 제목 자동 생성 테스트"""
    print("\n📝 [7/10] 대화 제목 자동 생성 테스트...")
    try:
        async with aiohttp.ClientSession() as session:
            # 특징적인 메시지로 대화 시작
            payload = {
                "message": "인공지능 챗봇의 발전 과정에 대해 설명해주세요.",
                "top_k": 4
            }
            
            conversation_id = None
            async with session.post(
                f"{BACKEND_URL}/api/chat/stream",
                json=payload,
                timeout=30
            ) as response:
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if data.get('type') == 'metadata':
                            conversation_id = data.get('conversation_id')
                        elif data.get('type') == 'done':
                            break
            
            if conversation_id:
                # 대화 목록 조회하여 제목 확인
                async with session.get(
                    f"{BACKEND_URL}/api/conversations",
                    timeout=10
                ) as response:
                    if response.status == 200:
                        conversations = await response.json()
                        target_conv = next(
                            (c for c in conversations if c['session_id'] == conversation_id),
                            None
                        )
                        
                        if target_conv and target_conv.get('title'):
                            title = target_conv['title']
                            TEST_RESULTS.append(TestResult(
                                "채팅 히스토리", "대화 제목 생성", "PASS",
                                f"생성된 제목: '{title}'"
                            ))
                            print(f"   ✅ 제목 생성: {title}")
                            return True
                        else:
                            TEST_RESULTS.append(TestResult(
                                "채팅 히스토리", "대화 제목 생성", "FAIL",
                                "제목이 생성되지 않음", "Medium"
                            ))
                            print("   ❌ 제목 미생성")
                            return False
                    else:
                        TEST_RESULTS.append(TestResult(
                            "채팅 히스토리", "대화 제목 생성", "FAIL",
                            "대화 목록 조회 실패", "Medium"
                        ))
                        print("   ❌ 조회 실패")
                        return False
            else:
                TEST_RESULTS.append(TestResult(
                    "채팅 히스토리", "대화 제목 생성", "FAIL",
                    "conversation_id 없음", "Medium"
                ))
                print("   ❌ 대화 생성 실패")
                return False
                
    except Exception as e:
        TEST_RESULTS.append(TestResult(
            "채팅 히스토리", "대화 제목 생성", "FAIL", str(e), "Medium"
        ))
        print(f"   ❌ 오류: {e}")
        return False


async def test_conversation_deletion():
    """대화 삭제 테스트"""
    print("\n🗑️ [8/10] 대화 삭제 테스트...")
    try:
        async with aiohttp.ClientSession() as session:
            # 삭제할 테스트 대화 생성
            payload = {
                "message": "삭제 테스트용 메시지입니다.",
                "top_k": 4
            }
            
            conversation_id = None
            async with session.post(
                f"{BACKEND_URL}/api/chat/stream",
                json=payload,
                timeout=30
            ) as response:
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if data.get('type') == 'metadata':
                            conversation_id = data.get('conversation_id')
                        elif data.get('type') == 'done':
                            break
            
            if not conversation_id:
                TEST_RESULTS.append(TestResult(
                    "채팅 히스토리", "대화 삭제", "FAIL",
                    "테스트 대화 생성 실패", "Medium"
                ))
                print("   ❌ 테스트 대화 생성 실패")
                return False
            
            # 대화 삭제
            async with session.delete(
                f"{BACKEND_URL}/api/conversations/{conversation_id}",
                timeout=10
            ) as response:
                if response.status == 200:
                    # 삭제 확인
                    async with session.get(
                        f"{BACKEND_URL}/api/conversations/{conversation_id}/messages",
                        timeout=10
                    ) as check_response:
                        if check_response.status == 404:
                            TEST_RESULTS.append(TestResult(
                                "채팅 히스토리", "대화 삭제", "PASS",
                                "대화 삭제 및 확인 완료"
                            ))
                            print("   ✅ 대화 삭제 성공")
                            return True
                        else:
                            TEST_RESULTS.append(TestResult(
                                "채팅 히스토리", "대화 삭제", "FAIL",
                                "삭제 후에도 대화가 남아있음", "High"
                            ))
                            print("   ❌ 삭제 실패 (데이터 남음)")
                            return False
                else:
                    TEST_RESULTS.append(TestResult(
                        "채팅 히스토리", "대화 삭제", "FAIL",
                        f"상태 코드: {response.status}", "Medium"
                    ))
                    print(f"   ❌ 삭제 실패: {response.status}")
                    return False
                    
    except Exception as e:
        TEST_RESULTS.append(TestResult(
            "채팅 히스토리", "대화 삭제", "FAIL", str(e), "Medium"
        ))
        print(f"   ❌ 오류: {e}")
        return False


async def test_feedback_submission():
    """피드백 제출 테스트"""
    print("\n👍 [9/10] 피드백 제출 테스트...")
    try:
        async with aiohttp.ClientSession() as session:
            # 테스트용 메시지 생성
            payload = {
                "message": "피드백 테스트용 질문입니다.",
                "top_k": 4
            }
            
            message_id = None
            async with session.post(
                f"{BACKEND_URL}/api/chat",
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # 대화에서 마지막 assistant 메시지 ID 조회
                    conv_id = result.get('conversation_id')
                    if conv_id:
                        async with session.get(
                            f"{BACKEND_URL}/api/conversations/{conv_id}/messages",
                            timeout=10
                        ) as msg_response:
                            if msg_response.status == 200:
                                messages = await msg_response.json()
                                assistant_msgs = [m for m in messages if m['role'] == 'assistant']
                                if assistant_msgs:
                                    message_id = assistant_msgs[-1]['id']
            
            if not message_id:
                TEST_RESULTS.append(TestResult(
                    "피드백", "피드백 제출", "FAIL",
                    "테스트 메시지 생성 실패", "Low"
                ))
                print("   ❌ 테스트 메시지 생성 실패")
                return False
            
            # 긍정 피드백 제출
            feedback_payload = {
                "message_id": message_id,
                "feedback": "positive"
            }
            
            async with session.post(
                f"{BACKEND_URL}/api/conversations/feedback",
                json=feedback_payload,
                timeout=10
            ) as response:
                if response.status == 200:
                    TEST_RESULTS.append(TestResult(
                        "피드백", "피드백 제출", "PASS",
                        "긍정 피드백 제출 성공"
                    ))
                    print("   ✅ 피드백 제출 성공")
                    return True
                else:
                    TEST_RESULTS.append(TestResult(
                        "피드백", "피드백 제출", "FAIL",
                        f"상태 코드: {response.status}", "Low"
                    ))
                    print(f"   ❌ 제출 실패: {response.status}")
                    return False
                    
    except Exception as e:
        TEST_RESULTS.append(TestResult(
            "피드백", "피드백 제출", "FAIL", str(e), "Low"
        ))
        print(f"   ❌ 오류: {e}")
        return False


async def test_new_conversation_context_reset():
    """새 대화 시작 시 컨텍스트 초기화 테스트"""
    print("\n🔄 [10/10] 컨텍스트 초기화 테스트...")
    try:
        async with aiohttp.ClientSession() as session:
            # 첫 번째 대화: "5년차"에 대해 질문
            payload1 = {
                "message": "5년차 직원의 연봉은 얼마인가요?",
                "top_k": 4
            }
            
            async with session.post(
                f"{BACKEND_URL}/api/chat/stream",
                json=payload1,
                timeout=30
            ) as response:
                conversation_id1 = None
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if data.get('type') == 'metadata':
                            conversation_id1 = data.get('conversation_id')
                        elif data.get('type') == 'done':
                            break
            
            if not conversation_id1:
                TEST_RESULTS.append(TestResult(
                    "컨텍스트 유지", "컨텍스트 초기화", "FAIL",
                    "첫 번째 대화 생성 실패", "Medium"
                ))
                print("   ❌ 첫 번째 대화 생성 실패")
                return False
            
            # 두 번째 대화: 새 대화에서 "복지"에 대해 질문 (5년차 언급 없이)
            payload2 = {
                "message": "그럼 복지는 어떻게 되나요?",
                "top_k": 4
            }
            
            answer2 = ""
            async with session.post(
                f"{BACKEND_URL}/api/chat/stream",
                json=payload2,
                timeout=30
            ) as response:
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if data.get('type') == 'content':
                            answer2 += data.get('content', '')
                        elif data.get('type') == 'done':
                            break
            
            # 새 대화이므로 "5년차"에 대한 언급이 없어야 함
            if "5년차" not in answer2 and "5년" not in answer2:
                TEST_RESULTS.append(TestResult(
                    "컨텍스트 유지", "컨텍스트 초기화", "PASS",
                    "새 대화에서 이전 컨텍스트 미반영 확인"
                ))
                print("   ✅ 컨텍스트 초기화 확인")
                return True
            else:
                TEST_RESULTS.append(TestResult(
                    "컨텍스트 유지", "컨텍스트 초기화", "WARNING",
                    "새 대화에서 이전 컨텍스트가 반영됨", "Medium"
                ))
                print("   ⚠️ 컨텍스트 초기화 불확실")
                return False
                
    except Exception as e:
        TEST_RESULTS.append(TestResult(
            "컨텍스트 유지", "컨텍스트 초기화", "FAIL", str(e), "Medium"
        ))
        print(f"   ❌ 오류: {e}")
        return False


def generate_report():
    """테스트 결과 리포트 생성"""
    print("\n" + "="*80)
    print("📊 통합 테스트 결과 리포트")
    print("="*80)
    
    passed = [r for r in TEST_RESULTS if r.status == "PASS"]
    failed = [r for r in TEST_RESULTS if r.status == "FAIL"]
    warnings = [r for r in TEST_RESULTS if r.status == "WARNING"]
    
    print(f"\n총 테스트: {len(TEST_RESULTS)}개")
    print(f"✅ 통과: {len(passed)}개")
    print(f"❌ 실패: {len(failed)}개")
    print(f"⚠️ 경고: {len(warnings)}개")
    
    # 실패한 테스트 상세
    if failed:
        print("\n" + "="*80)
        print("❌ 실패한 테스트")
        print("="*80)
        
        critical = [r for r in failed if r.severity == "Critical"]
        high = [r for r in failed if r.severity == "High"]
        medium = [r for r in failed if r.severity == "Medium"]
        low = [r for r in failed if r.severity == "Low"]
        
        for severity_name, severity_list in [
            ("Critical", critical),
            ("High", high),
            ("Medium", medium),
            ("Low", low)
        ]:
            if severity_list:
                print(f"\n🔴 {severity_name} 심각도:")
                for result in severity_list:
                    print(f"\n**버그**: [{result.category}] {result.test_name}")
                    print(f"  - 심각도: {result.severity}")
                    print(f"  - 상세: {result.details}")
    
    # 경고 표시
    if warnings:
        print("\n" + "="*80)
        print("⚠️ 경고")
        print("="*80)
        for result in warnings:
            print(f"\n[{result.category}] {result.test_name}")
            print(f"  - 상세: {result.details}")
    
    # 성공 기준 판정
    print("\n" + "="*80)
    print("📋 성공 기준 검증")
    print("="*80)
    
    critical_high_bugs = len([r for r in failed if r.severity in ["Critical", "High"]])
    medium_bugs = len([r for r in failed if r.severity == "Medium"])
    
    criteria = [
        ("모든 핵심 시나리오 통과", len(failed) == 0, "PASS" if len(failed) == 0 else "FAIL"),
        ("Critical/High 버그 0개", critical_high_bugs == 0, "PASS" if critical_high_bugs == 0 else "FAIL"),
        ("Medium 버그 3개 이하", medium_bugs <= 3, "PASS" if medium_bugs <= 3 else "FAIL"),
    ]
    
    all_passed = all(c[2] == "PASS" for c in criteria)
    
    for criterion, result, status in criteria:
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} {criterion}: {status}")
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 최종 판정: 통과 (PASS)")
        print("모든 테스트를 성공적으로 완료했습니다!")
    else:
        print("❌ 최종 판정: 불통과 (FAIL)")
        print("일부 테스트가 실패했습니다. 버그를 수정해주세요.")
    print("="*80)
    
    # 결과를 파일로 저장
    with open("INTEGRATION_TEST_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# 통합 테스트 결과 리포트\n\n")
        f.write(f"**테스트 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 요약\n\n")
        f.write(f"- 총 테스트: {len(TEST_RESULTS)}개\n")
        f.write(f"- ✅ 통과: {len(passed)}개\n")
        f.write(f"- ❌ 실패: {len(failed)}개\n")
        f.write(f"- ⚠️ 경고: {len(warnings)}개\n\n")
        
        if failed:
            f.write("## 발견된 버그\n\n")
            for i, result in enumerate(failed, 1):
                f.write(f"### 버그 #{i}: [{result.category}] {result.test_name}\n\n")
                f.write(f"- **심각도**: {result.severity}\n")
                f.write(f"- **상세**: {result.details}\n")
                f.write(f"- **발생 시간**: {result.timestamp}\n\n")
        
        if warnings:
            f.write("## 경고\n\n")
            for result in warnings:
                f.write(f"### [{result.category}] {result.test_name}\n\n")
                f.write(f"- **상세**: {result.details}\n")
                f.write(f"- **발생 시간**: {result.timestamp}\n\n")
        
        f.write("## 성공 기준 검증\n\n")
        for criterion, result, status in criteria:
            icon = "✅" if status == "PASS" else "❌"
            f.write(f"{icon} {criterion}: **{status}**\n\n")
        
        f.write("\n## 최종 판정\n\n")
        if all_passed:
            f.write("🎉 **통과 (PASS)**\n\n")
            f.write("모든 테스트를 성공적으로 완료했습니다!\n")
        else:
            f.write("❌ **불통과 (FAIL)**\n\n")
            f.write("일부 테스트가 실패했습니다. 버그를 수정해주세요.\n")
        
        f.write("\n## 상세 테스트 결과\n\n")
        for result in TEST_RESULTS:
            icon = "✅" if result.status == "PASS" else ("⚠️" if result.status == "WARNING" else "❌")
            f.write(f"{icon} [{result.category}] {result.test_name}\n")
            if result.details:
                f.write(f"  - {result.details}\n")
            f.write("\n")
    
    print(f"\n📄 상세 리포트가 'INTEGRATION_TEST_REPORT.md' 파일로 저장되었습니다.")
    
    return all_passed


async def main():
    """메인 테스트 실행"""
    print("="*80)
    print("🚀 AI 챗봇 통합 테스트 시작")
    print("="*80)
    print(f"백엔드 URL: {BACKEND_URL}")
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 백엔드 헬스 체크
    if not await test_backend_health():
        print("\n❌ 백엔드가 실행되지 않았습니다. 테스트를 중단합니다.")
        return False
    
    # 2. 새 대화 생성
    conversation_id = await test_conversation_creation()
    
    # 3. 대화 목록 조회
    await test_conversation_list()
    
    # 4. 스트리밍 응답 테스트
    await test_streaming_response()
    
    # 5. 컨텍스트 메모리 테스트 (기존 대화 사용)
    if conversation_id:
        await test_context_memory(conversation_id)
        await test_message_retrieval(conversation_id)
    
    # 6. 대화 제목 자동 생성
    await test_conversation_title()
    
    # 7. 대화 삭제
    await test_conversation_deletion()
    
    # 8. 피드백 제출
    await test_feedback_submission()
    
    # 9. 컨텍스트 초기화
    await test_new_conversation_context_reset()
    
    # 결과 리포트 생성
    print("\n테스트 완료! 결과를 생성하는 중...")
    success = generate_report()
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 테스트가 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
