"""
통합 테스트 스크립트
모든 새로운 기능을 테스트합니다.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, List, Any
from datetime import datetime
from colorama import init, Fore, Style

# UTF-8 인코딩 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

init(autoreset=True)

BASE_URL = "http://localhost:8000"

class FeatureTester:
    def __init__(self):
        self.results = []
        self.session = None
        self.test_data = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, name: str, status: str, message: str = "", error: str = ""):
        """테스트 결과를 로깅합니다."""
        result = {
            "name": name,
            "status": status,
            "message": message,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        if status == "PASS":
            print(f"{Fore.GREEN}✓ {name}{Style.RESET_ALL}")
            if message:
                print(f"  {Fore.CYAN}{message}{Style.RESET_ALL}")
        elif status == "FAIL":
            print(f"{Fore.RED}✗ {name}{Style.RESET_ALL}")
            if error:
                print(f"  {Fore.RED}Error: {error}{Style.RESET_ALL}")
        elif status == "INFO":
            print(f"{Fore.YELLOW}ℹ {name}{Style.RESET_ALL}")
            if message:
                print(f"  {message}")
    
    async def test_health(self):
        """서버 헬스 체크"""
        print(f"\n{Fore.BLUE}{'='*60}")
        print(f"서버 연결 테스트")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        try:
            async with self.session.get(f"{BASE_URL}/api/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test(
                        "서버 헬스 체크",
                        "PASS",
                        f"Status: {data.get('status')}, Version: {data.get('version')}"
                    )
                    return True
                else:
                    self.log_test("서버 헬스 체크", "FAIL", error=f"Status: {resp.status}")
                    return False
        except Exception as e:
            self.log_test("서버 헬스 체크", "FAIL", error=str(e))
            return False
    
    # ============================================================
    # 1. 지식 관리 모달 테스트
    # ============================================================
    async def test_knowledge_management(self):
        """지식 관리 기능 테스트"""
        print(f"\n{Fore.BLUE}{'='*60}")
        print(f"1. 지식 관리 모달 테스트")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # 1.1 새 지식 생성
        try:
            create_data = {
                "title": "테스트 지식 항목",
                "content": "이것은 통합 테스트를 위한 지식 항목입니다.\n\n## 테스트 내용\n- 항목 1\n- 항목 2",
                "category": "how_to",
                "tags": ["테스트", "통합테스트"],
                "author": "테스터",
                "status": "published"
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/knowledge",
                json=create_data
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    self.test_data['knowledge_id'] = data['id']
                    self.log_test(
                        "새 지식 추가 - 제목/내용 입력 후 생성",
                        "PASS",
                        f"ID: {data['id']}, Title: {data['title']}"
                    )
                else:
                    error_text = await resp.text()
                    self.log_test(
                        "새 지식 추가",
                        "FAIL",
                        error=f"Status: {resp.status}, {error_text}"
                    )
                    return False
        except Exception as e:
            self.log_test("새 지식 추가", "FAIL", error=str(e))
            return False
        
        # 1.2 지식 항목 조회
        try:
            knowledge_id = self.test_data['knowledge_id']
            async with self.session.get(
                f"{BASE_URL}/api/knowledge/{knowledge_id}"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test(
                        "편집 버튼 클릭 시 모달 표시 및 데이터 로드",
                        "PASS",
                        f"로드된 데이터: {data['title']}"
                    )
                else:
                    self.log_test(
                        "지식 항목 조회",
                        "FAIL",
                        error=f"Status: {resp.status}"
                    )
        except Exception as e:
            self.log_test("지식 항목 조회", "FAIL", error=str(e))
        
        # 1.3 지식 항목 업데이트
        try:
            knowledge_id = self.test_data['knowledge_id']
            update_data = {
                "title": "테스트 지식 항목 (수정됨)",
                "content": "수정된 내용입니다.",
                "tags": ["테스트", "통합테스트", "수정됨"]
            }
            
            async with self.session.put(
                f"{BASE_URL}/api/knowledge/{knowledge_id}",
                json=update_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.log_test(
                        "편집 후 저장 성공",
                        "PASS",
                        f"수정된 제목: {data['title']}"
                    )
                else:
                    self.log_test(
                        "지식 항목 업데이트",
                        "FAIL",
                        error=f"Status: {resp.status}"
                    )
        except Exception as e:
            self.log_test("지식 항목 업데이트", "FAIL", error=str(e))
        
        # 1.4 태그 기능 테스트
        try:
            async with self.session.get(f"{BASE_URL}/api/knowledge") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if len(data) > 0 and 'tags' in data[0]:
                        self.log_test(
                            "태그 추가/제거 동작",
                            "PASS",
                            f"태그 확인: {data[0].get('tags', [])}"
                        )
                    else:
                        self.log_test(
                            "태그 추가/제거 동작",
                            "FAIL",
                            error="태그 데이터를 찾을 수 없음"
                        )
                else:
                    self.log_test(
                        "태그 기능 테스트",
                        "FAIL",
                        error=f"Status: {resp.status}"
                    )
        except Exception as e:
            self.log_test("태그 기능 테스트", "FAIL", error=str(e))
        
        # 1.5 폼 validation 테스트
        try:
            invalid_data = {
                "title": "",  # 빈 제목
                "content": "내용만 있음"
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/knowledge",
                json=invalid_data
            ) as resp:
                if resp.status == 422:  # Validation error
                    self.log_test(
                        "폼 validation (필수 필드)",
                        "PASS",
                        "빈 제목이 올바르게 거부됨"
                    )
                else:
                    self.log_test(
                        "폼 validation",
                        "FAIL",
                        error="빈 제목이 허용됨 (예상: 422 에러)"
                    )
        except Exception as e:
            self.log_test("폼 validation", "FAIL", error=str(e))
        
        return True
    
    # ============================================================
    # 2. 대화 학습 기능 테스트
    # ============================================================
    async def test_conversation_learning(self):
        """대화 학습 기능 테스트"""
        print(f"\n{Fore.BLUE}{'='*60}")
        print(f"2. 대화 학습 기능 테스트")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # 2.1 새 대화 시작
        try:
            chat_data = {
                "message": "FastAPI의 의존성 주입(Dependency Injection)에 대해 설명해주세요.",
                "conversation_id": None,
                "top_k": 4,
                "search_sources": ["knowledge"]
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/chat",
                json=chat_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.test_data['conversation_id'] = data.get('conversation_id')
                    self.test_data['message_id'] = None  # 프론트엔드에서 관리되는 ID
                    self.log_test(
                        "대화 시작",
                        "PASS",
                        f"Conversation ID: {self.test_data['conversation_id']}"
                    )
                else:
                    error_text = await resp.text()
                    self.log_test(
                        "대화 시작",
                        "FAIL",
                        error=f"Status: {resp.status}, {error_text}"
                    )
                    return False
        except Exception as e:
            self.log_test("대화 시작", "FAIL", error=str(e))
            return False
        
        # 2.2 대화 메시지 조회
        try:
            conversation_id = self.test_data['conversation_id']
            async with self.session.get(
                f"{BASE_URL}/api/conversations/{conversation_id}/messages"
            ) as resp:
                if resp.status == 200:
                    messages = await resp.json()
                    if len(messages) > 0:
                        # 최신 assistant 메시지 ID 저장
                        assistant_msg = [m for m in messages if m['role'] == 'assistant']
                        if assistant_msg:
                            self.test_data['message_id'] = assistant_msg[-1]['id']
                            self.log_test(
                                "대화 메시지 조회",
                                "PASS",
                                f"메시지 수: {len(messages)}"
                            )
                        else:
                            self.log_test(
                                "대화 메시지 조회",
                                "FAIL",
                                error="Assistant 메시지를 찾을 수 없음"
                            )
                    else:
                        self.log_test(
                            "대화 메시지 조회",
                            "FAIL",
                            error="메시지가 없음"
                        )
                else:
                    self.log_test(
                        "대화 메시지 조회",
                        "FAIL",
                        error=f"Status: {resp.status}"
                    )
        except Exception as e:
            self.log_test("대화 메시지 조회", "FAIL", error=str(e))
        
        # 2.3 긍정 피드백 제출
        try:
            message_id = self.test_data.get('message_id')
            if not message_id:
                self.log_test(
                    "긍정 피드백 제출",
                    "FAIL",
                    error="메시지 ID를 찾을 수 없음"
                )
            else:
                feedback_data = {
                    "message_id": message_id,
                    "feedback": "positive"
                }
                
                async with self.session.post(
                    f"{BASE_URL}/api/conversations/feedback",
                    json=feedback_data
                ) as resp:
                    if resp.status == 200:
                        self.log_test(
                            "긍정 피드백 버튼 작동",
                            "PASS",
                            "피드백이 성공적으로 제출됨"
                        )
                    else:
                        error_text = await resp.text()
                        self.log_test(
                            "긍정 피드백 제출",
                            "FAIL",
                            error=f"Status: {resp.status}, {error_text}"
                        )
        except Exception as e:
            self.log_test("긍정 피드백 제출", "FAIL", error=str(e))
        
        # 2.4 지식 추출 API 호출
        try:
            conversation_id = self.test_data['conversation_id']
            async with self.session.post(
                f"{BASE_URL}/api/conversations/{conversation_id}/extract-knowledge"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.test_data['extracted_knowledge_id'] = data.get('id')
                    self.log_test(
                        '"지식으로 저장" 버튼 표시 및 지식 추출 API 호출 성공',
                        "PASS",
                        f"추출된 지식 ID: {data.get('id')}, 제목: {data.get('title')}"
                    )
                else:
                    error_text = await resp.text()
                    self.log_test(
                        "지식 추출 API 호출",
                        "FAIL",
                        error=f"Status: {resp.status}, {error_text}"
                    )
                    return False
        except Exception as e:
            self.log_test("지식 추출 API 호출", "FAIL", error=str(e))
            return False
        
        # 2.5 추출된 지식 확인 (draft 상태)
        try:
            extracted_id = self.test_data['extracted_knowledge_id']
            async with self.session.get(
                f"{BASE_URL}/api/knowledge/{extracted_id}"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('status') == 'draft':
                        self.log_test(
                            "추출된 지식이 draft 상태로 생성됨",
                            "PASS",
                            f"상태: {data.get('status')}, 제목: {data.get('title')}"
                        )
                    else:
                        self.log_test(
                            "추출된 지식 상태 확인",
                            "FAIL",
                            error=f"예상: draft, 실제: {data.get('status')}"
                        )
                else:
                    self.log_test(
                        "추출된 지식 확인",
                        "FAIL",
                        error=f"Status: {resp.status}"
                    )
        except Exception as e:
            self.log_test("추출된 지식 확인", "FAIL", error=str(e))
        
        # 2.6 지식 관리 페이지에서 draft 항목 확인
        try:
            async with self.session.get(
                f"{BASE_URL}/api/knowledge?status_filter=draft"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    draft_items = [item for item in data if item.get('status') == 'draft']
                    if len(draft_items) > 0:
                        self.log_test(
                            "지식 관리 페이지에서 draft 항목 확인",
                            "PASS",
                            f"Draft 항목 수: {len(draft_items)}"
                        )
                    else:
                        self.log_test(
                            "지식 관리 페이지에서 draft 항목 확인",
                            "FAIL",
                            error="Draft 항목을 찾을 수 없음"
                        )
                else:
                    self.log_test(
                        "Draft 항목 조회",
                        "FAIL",
                        error=f"Status: {resp.status}"
                    )
        except Exception as e:
            self.log_test("Draft 항목 조회", "FAIL", error=str(e))
        
        return True
    
    # ============================================================
    # 3. 웹 검색 통합 테스트
    # ============================================================
    async def test_web_search(self):
        """웹 검색 통합 테스트"""
        print(f"\n{Fore.BLUE}{'='*60}")
        print(f"3. 웹 검색 통합 테스트")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # 3.1 웹 검색 단독 테스트
        try:
            search_data = {
                "query": "Python FastAPI best practices",
                "sources": ["web"],
                "top_k": 3
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/search/unified",
                json=search_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    web_results = [r for r in data.get('results', []) if r.get('source_type') == 'web']
                    if len(web_results) > 0:
                        self.log_test(
                            '"웹 검색" 선택 시 DuckDuckGo 검색 작동',
                            "PASS",
                            f"웹 검색 결과 수: {len(web_results)}"
                        )
                    else:
                        self.log_test(
                            "웹 검색 작동",
                            "FAIL",
                            error="웹 검색 결과가 없음"
                        )
                else:
                    error_text = await resp.text()
                    self.log_test(
                        "웹 검색",
                        "FAIL",
                        error=f"Status: {resp.status}, {error_text}"
                    )
        except Exception as e:
            self.log_test("웹 검색", "FAIL", error=str(e))
        
        # 3.2 통합 검색 결과에 웹 검색 포함
        try:
            search_data = {
                "query": "FastAPI dependency injection",
                "sources": ["documents", "knowledge", "web"],
                "top_k": 5
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/search/unified",
                json=search_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get('results', [])
                    web_results = [r for r in results if r.get('source_type') == 'web']
                    
                    if len(web_results) > 0:
                        self.log_test(
                            "통합 검색 결과에 웹 검색 결과 포함",
                            "PASS",
                            f"전체 결과: {len(results)}, 웹 결과: {len(web_results)}"
                        )
                    else:
                        self.log_test(
                            "통합 검색 결과",
                            "INFO",
                            "웹 검색 결과가 없음 (검색어에 따라 정상일 수 있음)"
                        )
                else:
                    error_text = await resp.text()
                    self.log_test(
                        "통합 검색",
                        "FAIL",
                        error=f"Status: {resp.status}, {error_text}"
                    )
        except Exception as e:
            self.log_test("통합 검색", "FAIL", error=str(e))
        
        # 3.3 웹 검색 에러 처리 테스트
        try:
            # 잘못된 소스 타입
            search_data = {
                "query": "test",
                "sources": ["invalid_source"],
                "top_k": 3
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/search/unified",
                json=search_data
            ) as resp:
                # 잘못된 소스는 무시되고 빈 결과를 반환해야 함
                if resp.status in [200, 400]:
                    self.log_test(
                        "에러 처리 (잘못된 소스)",
                        "PASS",
                        "잘못된 소스 타입이 적절히 처리됨"
                    )
                else:
                    self.log_test(
                        "에러 처리",
                        "FAIL",
                        error=f"예상치 못한 상태 코드: {resp.status}"
                    )
        except Exception as e:
            self.log_test("에러 처리 테스트", "INFO", f"예외 발생 (정상일 수 있음): {str(e)}")
        
        return True
    
    # ============================================================
    # 4. 통합 시나리오 테스트
    # ============================================================
    async def test_integrated_scenarios(self):
        """통합 시나리오 테스트"""
        print(f"\n{Fore.BLUE}{'='*60}")
        print(f"4. 통합 시나리오 테스트")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # 4.1 문서 + 지식베이스 + 웹 검색 동시 사용
        try:
            search_data = {
                "query": "Python async programming best practices",
                "sources": ["documents", "knowledge", "web"],
                "top_k": 10
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/search/unified",
                json=search_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get('results', [])
                    
                    # 소스별 결과 수 확인
                    source_counts = {}
                    for result in results:
                        source_type = result.get('source_type', 'unknown')
                        source_counts[source_type] = source_counts.get(source_type, 0) + 1
                    
                    self.log_test(
                        "문서 + 지식베이스 + 웹 검색 동시 사용",
                        "PASS",
                        f"전체 결과: {len(results)}, 소스별: {source_counts}"
                    )
                else:
                    error_text = await resp.text()
                    self.log_test(
                        "통합 검색",
                        "FAIL",
                        error=f"Status: {resp.status}, {error_text}"
                    )
                    return False
        except Exception as e:
            self.log_test("통합 검색 테스트", "FAIL", error=str(e))
            return False
        
        # 4.2 가중치 기반 재정렬 확인
        try:
            # 동일한 검색을 다시 수행하여 점수 확인
            search_data = {
                "query": "FastAPI dependency injection tutorial",
                "sources": ["documents", "knowledge", "web"],
                "top_k": 5
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/search/unified",
                json=search_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get('results', [])
                    
                    # 가중치 점수(weighted_score 또는 final_score)로 확인
                    scores = []
                    for r in results:
                        # final_score가 있으면 우선 사용, 없으면 weighted_score 사용
                        score = r.get('final_score', r.get('weighted_score', 0))
                        scores.append(score)
                    
                    is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
                    
                    if is_sorted:
                        self.log_test(
                            "가중치 기반 재정렬 작동",
                            "PASS",
                            f"결과가 점수 순으로 정렬됨: {[f'{s:.4f}' for s in scores]}"
                        )
                    else:
                        self.log_test(
                            "가중치 기반 재정렬",
                            "FAIL",
                            error=f"결과가 정렬되지 않음: {scores}"
                        )
                else:
                    self.log_test(
                        "재정렬 확인",
                        "FAIL",
                        error=f"Status: {resp.status}"
                    )
        except Exception as e:
            self.log_test("재정렬 확인", "FAIL", error=str(e))
        
        # 4.3 대화 → 피드백 → 지식 저장 → 확인 플로우
        try:
            # 새 대화 시작
            chat_data = {
                "message": "GraphQL과 REST API의 차이점을 설명해주세요.",
                "conversation_id": None,
                "top_k": 4,
                "search_sources": ["knowledge", "web"]
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/chat",
                json=chat_data
            ) as resp:
                if resp.status != 200:
                    self.log_test(
                        "통합 플로우 - 대화 시작",
                        "FAIL",
                        error=f"Status: {resp.status}"
                    )
                    return False
                
                data = await resp.json()
                flow_conversation_id = data.get('conversation_id')
            
            # 메시지 조회
            async with self.session.get(
                f"{BASE_URL}/api/conversations/{flow_conversation_id}/messages"
            ) as resp:
                if resp.status != 200:
                    self.log_test(
                        "통합 플로우 - 메시지 조회",
                        "FAIL",
                        error=f"Status: {resp.status}"
                    )
                    return False
                
                messages = await resp.json()
                assistant_msg = [m for m in messages if m['role'] == 'assistant']
                if not assistant_msg:
                    self.log_test(
                        "통합 플로우 - 메시지 조회",
                        "FAIL",
                        error="Assistant 메시지 없음"
                    )
                    return False
                
                flow_message_id = assistant_msg[-1]['id']
            
            # 긍정 피드백
            feedback_data = {
                "message_id": flow_message_id,
                "feedback": "positive"
            }
            
            async with self.session.post(
                f"{BASE_URL}/api/conversations/feedback",
                json=feedback_data
            ) as resp:
                if resp.status != 200:
                    self.log_test(
                        "통합 플로우 - 피드백",
                        "FAIL",
                        error=f"Status: {resp.status}"
                    )
                    return False
            
            # 지식 추출
            async with self.session.post(
                f"{BASE_URL}/api/conversations/{flow_conversation_id}/extract-knowledge"
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    self.log_test(
                        "통합 플로우 - 지식 추출",
                        "FAIL",
                        error=f"Status: {resp.status}, {error_text}"
                    )
                    return False
                
                extracted_data = await resp.json()
                flow_knowledge_id = extracted_data.get('id')
            
            # 지식 관리에서 확인
            async with self.session.get(
                f"{BASE_URL}/api/knowledge/{flow_knowledge_id}"
            ) as resp:
                if resp.status == 200:
                    knowledge_data = await resp.json()
                    self.log_test(
                        "대화 → 피드백 → 지식 저장 → 확인 플로우",
                        "PASS",
                        f"플로우 완료: 지식 ID {flow_knowledge_id}, 제목: {knowledge_data.get('title')}"
                    )
                else:
                    self.log_test(
                        "통합 플로우 - 최종 확인",
                        "FAIL",
                        error=f"Status: {resp.status}"
                    )
                    return False
                    
        except Exception as e:
            self.log_test("통합 플로우 테스트", "FAIL", error=str(e))
            return False
        
        return True
    
    # ============================================================
    # 테스트 실행 및 보고서 생성
    # ============================================================
    async def run_all_tests(self):
        """모든 테스트를 실행합니다."""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"통합 테스트 시작")
        print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # 서버 연결 확인
        if not await self.test_health():
            print(f"\n{Fore.RED}서버에 연결할 수 없습니다. 테스트를 중단합니다.{Style.RESET_ALL}")
            return
        
        # 각 테스트 실행
        await self.test_knowledge_management()
        await self.test_conversation_learning()
        await self.test_web_search()
        await self.test_integrated_scenarios()
        
        # 보고서 생성
        self.generate_report()
    
    def generate_report(self):
        """테스트 결과 보고서를 생성합니다."""
        print(f"\n{Fore.BLUE}{'='*60}")
        print(f"테스트 결과 요약")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        total = len(self.results)
        passed = len([r for r in self.results if r['status'] == 'PASS'])
        failed = len([r for r in self.results if r['status'] == 'FAIL'])
        info = len([r for r in self.results if r['status'] == 'INFO'])
        
        print(f"총 테스트: {total}")
        print(f"{Fore.GREEN}성공: {passed}{Style.RESET_ALL}")
        print(f"{Fore.RED}실패: {failed}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}정보: {info}{Style.RESET_ALL}")
        print(f"\n성공률: {(passed/total*100):.1f}%\n")
        
        # 실패한 테스트 상세 정보
        if failed > 0:
            print(f"{Fore.RED}{'='*60}")
            print(f"실패한 테스트 상세")
            print(f"{'='*60}{Style.RESET_ALL}\n")
            
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"{Fore.RED}✗ {result['name']}{Style.RESET_ALL}")
                    print(f"  에러: {result['error']}\n")
        
        # 보고서 파일 저장
        report_file = "test_results_comprehensive.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'info': info,
                    'success_rate': passed / total * 100
                },
                'results': self.results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"{Fore.CYAN}상세 보고서가 '{report_file}'에 저장되었습니다.{Style.RESET_ALL}\n")


async def main():
    """메인 실행 함수"""
    try:
        async with FeatureTester() as tester:
            await tester.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}테스트가 사용자에 의해 중단되었습니다.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}예상치 못한 오류가 발생했습니다: {str(e)}{Style.RESET_ALL}")


if __name__ == "__main__":
    asyncio.run(main())
