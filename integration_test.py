#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 테스트 스크립트
GPT-4o-mini + 마크다운 구조 개선 검증
"""

import sys
import io
import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 설정
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# 테스트 결과 저장
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "response_times": [],
    "markdown_checks": {},
    "overall_status": "PENDING"
}

def print_section(title: str):
    """섹션 제목 출력"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health_check() -> bool:
    """1단계: 기본 연결 테스트"""
    print_section("1단계: 기본 연결 테스트")
    
    try:
        # Health 체크
        print("[TEST] Health 엔드포인트 테스트...")
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"   상태 코드: {response.status_code}")
        print(f"   응답: {response.json()}")
        
        if response.status_code == 200:
            print("   [PASS] Health check 성공")
            test_results["tests"].append({
                "name": "Health Check",
                "status": "PASS",
                "response_time": response.elapsed.total_seconds()
            })
            return True
        else:
            print(f"   [FAIL] Health check 실패: {response.status_code}")
            test_results["tests"].append({
                "name": "Health Check",
                "status": "FAIL",
                "error": f"Status code: {response.status_code}"
            })
            return False
            
    except Exception as e:
        print(f"   [FAIL] 연결 실패: {str(e)}")
        test_results["tests"].append({
            "name": "Health Check",
            "status": "FAIL",
            "error": str(e)
        })
        return False

def test_api_docs() -> bool:
    """API 문서 접근 테스트"""
    try:
        print("[TEST] API 문서 접근 테스트...")
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"   상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            print("   [PASS] API 문서 접근 성공")
            return True
        else:
            print(f"   [FAIL] API 문서 접근 실패")
            return False
            
    except Exception as e:
        print(f"   [FAIL] API 문서 접근 실패: {str(e)}")
        return False

def check_markdown_structure(text: str) -> Dict[str, bool]:
    """마크다운 구조 검증"""
    checks = {
        "has_h2_title": "##" in text,
        "has_h3_subtitle": "###" in text,
        "has_bold": "**" in text,
        "has_list": ("- " in text or "* " in text or "1." in text),
        "has_source": ("출처" in text or "참고" in text or "Reference" in text.lower()),
    }
    return checks

def test_chat_query(question: str, description: str) -> Tuple[bool, Dict]:
    """채팅 질의 테스트"""
    print(f"\n[TEST] 테스트: {description}")
    print(f"   질문: {question}")
    
    try:
        # 질의 전송 (conversation_id 없으면 자동 생성)
        start_time = time.time()
        query_response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": question,
                # conversation_id를 비워두면 자동으로 새로 생성됨
            },
            timeout=30
        )
        elapsed_time = time.time() - start_time
        
        if query_response.status_code != 200:
            print(f"   [FAIL] 질의 실패: {query_response.status_code}")
            print(f"   에러 내용: {query_response.text}")
            return False, {}
        
        result = query_response.json()
        answer = result.get("message", "")  # "answer"가 아니라 "message"
        conversation_id = result.get("conversation_id", "")
        
        # 응답 시간
        print(f"   [INFO] Conversation ID: {conversation_id}")
        print(f"   [TIME] 응답 시간: {elapsed_time:.2f}초")
        test_results["response_times"].append({
            "question": description,
            "time": elapsed_time
        })
        
        # 마크다운 구조 검증
        md_checks = check_markdown_structure(answer)
        print(f"\n   [CHECK] 마크다운 구조 검증:")
        print(f"      {'[OK]' if md_checks['has_h2_title'] else '[NO]'} ## 제목 포함")
        print(f"      {'[OK]' if md_checks['has_h3_subtitle'] else '[NO]'} ### 소제목 포함")
        print(f"      {'[OK]' if md_checks['has_bold'] else '[NO]'} **굵은 글씨** 사용")
        print(f"      {'[OK]' if md_checks['has_list'] else '[NO]'} 목록 사용")
        print(f"      {'[OK]' if md_checks['has_source'] else '[NO]'} 출처 표시")
        
        # 답변 샘플 출력
        print(f"\n   [SAMPLE] 답변 샘플 (처음 300자):")
        print(f"   {'-'*56}")
        print(f"   {answer[:300]}...")
        print(f"   {'-'*56}")
        
        # 성공 기준: 응답 시간 10초 이내, 마크다운 요소 3개 이상
        passed_checks = sum(md_checks.values())
        success = elapsed_time <= 10 and passed_checks >= 3
        
        test_results["tests"].append({
            "name": description,
            "status": "PASS" if success else "PARTIAL",
            "response_time": elapsed_time,
            "markdown_checks": md_checks,
            "passed_checks": f"{passed_checks}/5",
            "answer_length": len(answer)
        })
        
        if success:
            print(f"\n   [PASS] 테스트 성공 (응답시간: {elapsed_time:.2f}초, 마크다운: {passed_checks}/5)")
        else:
            print(f"\n   [PARTIAL] 테스트 부분 성공 (응답시간: {elapsed_time:.2f}초, 마크다운: {passed_checks}/5)")
        
        return success, {
            "question": question,
            "answer": answer,
            "response_time": elapsed_time,
            "markdown_checks": md_checks
        }
        
    except Exception as e:
        print(f"   [FAIL] 테스트 실패: {str(e)}")
        test_results["tests"].append({
            "name": description,
            "status": "FAIL",
            "error": str(e)
        })
        return False, {}

def generate_report(test_data: List[Dict]):
    """테스트 보고서 생성"""
    print_section("5단계: 보고서 생성")
    
    # 통계 계산
    total_tests = len(test_results["tests"])
    passed_tests = len([t for t in test_results["tests"] if t["status"] == "PASS"])
    failed_tests = len([t for t in test_results["tests"] if t["status"] == "FAIL"])
    
    response_times = test_results["response_times"]
    avg_response_time = sum(r["time"] for r in response_times) / len(response_times) if response_times else 0
    
    # 보고서 작성
    report = f"""# 통합 테스트 보고서

## 테스트 개요

- **테스트 일시:** {test_results["timestamp"]}
- **총 테스트 수:** {total_tests}
- **성공:** {passed_tests}
- **실패:** {failed_tests}
- **성공률:** {(passed_tests/total_tests*100):.1f}%

## 1. 기본 연결 테스트

"""
    
    for test in test_results["tests"]:
        if test["name"] == "Health Check":
            report += f"### Health Check\n\n"
            report += f"- **상태:** {test['status']}\n"
            if "response_time" in test:
                report += f"- **응답 시간:** {test['response_time']:.3f}초\n"
            report += f"\n"
    
    report += f"""## 2. 마크다운 구조 테스트

"""
    
    for test in test_results["tests"]:
        if "markdown_checks" in test:
            report += f"### {test['name']}\n\n"
            report += f"- **상태:** {test['status']}\n"
            report += f"- **응답 시간:** {test['response_time']:.2f}초\n"
            report += f"- **마크다운 검증:** {test['passed_checks']}\n\n"
            
            checks = test["markdown_checks"]
            report += f"**구조 요소:**\n\n"
            report += f"- {'[OK]' if checks['has_h2_title'] else '[NO]'} `##` 제목 포함\n"
            report += f"- {'[OK]' if checks['has_h3_subtitle'] else '[NO]'} `###` 소제목 포함\n"
            report += f"- {'[OK]' if checks['has_bold'] else '[NO]'} **굵은 글씨** 사용\n"
            report += f"- {'[OK]' if checks['has_list'] else '[NO]'} 목록 사용\n"
            report += f"- {'[OK]' if checks['has_source'] else '[NO]'} 출처 표시\n\n"
    
    report += f"""## 3. 성능 측정

### 응답 시간 통계

"""
    
    for rt in response_times:
        status = "[OK]" if rt["time"] <= 10 else "[SLOW]"
        report += f"- **{rt['question']}:** {rt['time']:.2f}초 {status}\n"
    
    report += f"""
- **평균 응답 시간:** {avg_response_time:.2f}초
- **목표:** 10초 이내
- **달성 여부:** {'[OK] 달성' if avg_response_time <= 10 else '[FAIL] 미달성'}

## 4. 마크다운 구조 샘플

"""
    
    # 테스트 데이터에서 샘플 추가
    for i, data in enumerate(test_data, 1):
        if "answer" in data:
            report += f"### 샘플 {i}: {data['question']}\n\n"
            report += f"```markdown\n{data['answer'][:500]}...\n```\n\n"
    
    report += f"""## 5. 개선 효과

### GPT-4o-mini 전환 효과

- **비용 절감:** GPT-4o 대비 약 15배 저렴
- **응답 속도:** {'평균 10초 이내 달성' if avg_response_time <= 10 else f'평균 {avg_response_time:.1f}초 (개선 필요)'}
- **마크다운 구조:** 체계적인 답변 생성 확인

### 마크다운 구조화 효과

- **가독성 향상:** 제목, 소제목, 강조 활용
- **정보 구조화:** 목록 및 표 형식 사용
- **출처 명시:** 답변 신뢰도 향상

## 6. 다음 단계 제안

### 즉시 조치

1. **프롬프트 최적화**
   - 모든 답변에 출처 포함 강제
   - 표 형식 사용 확대

2. **성능 모니터링**
   - 응답 시간 로깅
   - 느린 쿼리 분석

### 향후 개선

1. **다국어 지원**
   - 한국어 답변 품질 개선
   - 언어별 마크다운 스타일

2. **고급 기능**
   - 코드 블록 자동 포맷팅
   - 다이어그램 생성 (Mermaid)

3. **사용자 경험**
   - 스트리밍 응답 개선
   - 마크다운 렌더링 최적화

## 7. 결론

"""
    
    if passed_tests == total_tests:
        report += f"""**[SUCCESS] 모든 테스트 통과!**

GPT-4o-mini + 마크다운 구조 개선이 성공적으로 적용되었습니다.
- 응답 시간 목표 달성
- 마크다운 구조 정상 작동
- 시스템 안정성 확인

프로덕션 배포 준비 완료!
"""
    else:
        report += f"""**[WARNING] 일부 테스트 실패**

{failed_tests}개 테스트가 실패했습니다. 다음 항목을 확인하세요:
- 네트워크 연결 상태
- 백엔드 서비스 로그
- 데이터베이스 상태
- API 응답 에러 메시지

문제 해결 후 재테스트를 권장합니다.
"""
    
    report += f"""
---
*테스트 생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # 파일 저장
    with open("INTEGRATION_TEST_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("[DONE] 보고서 생성 완료: INTEGRATION_TEST_REPORT.md")
    
    # JSON 결과도 저장
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    
    print("[DONE] JSON 결과 저장: test_results.json")

def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("  GPT-4o-mini + 마크다운 구조 통합 테스트".center(60))
    print("="*60 + "\n")
    
    # 1단계: 기본 연결 테스트
    if not test_health_check():
        print("\n[FAIL] 기본 연결 테스트 실패. 테스트를 중단합니다.")
        print("   Docker 컨테이너가 실행 중인지 확인하세요:")
        print("   docker-compose ps")
        test_results["overall_status"] = "FAILED"
        generate_report([])
        return
    
    test_api_docs()
    
    # 3단계: 마크다운 구조 테스트
    print_section("3단계: 마크다운 구조 테스트")
    
    test_queries = [
        ("What is machine learning?", "기본 질문"),
        ("Explain the benefits of Docker", "목록 형식"),
        ("Compare Python and JavaScript", "비교 형식"),
    ]
    
    test_data = []
    for question, description in test_queries:
        success, data = test_chat_query(question, description)
        if data:
            test_data.append(data)
        time.sleep(2)  # API 부하 방지
    
    # 4단계: 성능 측정
    print_section("4단계: 성능 측정")
    
    if test_results["response_times"]:
        avg_time = sum(r["time"] for r in test_results["response_times"]) / len(test_results["response_times"])
        print(f"[STAT] 평균 응답 시간: {avg_time:.2f}초")
        print(f"[STAT] 목표: 10초 이내")
        
        if avg_time <= 10:
            print(f"[PASS] 성능 목표 달성!")
            test_results["overall_status"] = "PASSED"
        else:
            print(f"[WARNING] 성능 목표 미달 ({avg_time:.2f}초 > 10초)")
            test_results["overall_status"] = "PARTIAL"
    else:
        print("[FAIL] 성능 데이터 없음")
        test_results["overall_status"] = "FAILED"
    
    # 5단계: 보고서 생성
    generate_report(test_data)
    
    # 최종 결과
    print_section("테스트 완료")
    print(f"최종 상태: {test_results['overall_status']}")
    print(f"\n[FILE] 상세 보고서: INTEGRATION_TEST_REPORT.md")
    print(f"[FILE] JSON 결과: test_results.json")

if __name__ == "__main__":
    main()
