#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프론트엔드 확인 스크립트
마크다운 렌더링 확인
"""

import sys
import io
import webbrowser
import time

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

FRONTEND_URL = "http://localhost:3000"

def main():
    print("\n" + "="*60)
    print("  프론트엔드 마크다운 렌더링 확인".center(60))
    print("="*60 + "\n")
    
    print("[INFO] 프론트엔드 URL:", FRONTEND_URL)
    print("[INFO] 브라우저를 열어 확인하세요...\n")
    
    print("확인 사항:")
    print("1. 제목 (##)이 큰 글씨로 표시되는지")
    print("2. 소제목 (###)이 중간 크기로 표시되는지")
    print("3. **굵은 글씨**가 진하게 표시되는지")
    print("4. 목록이 점이나 번호로 표시되는지")
    print("5. 표(Table)가 정렬되어 표시되는지")
    print("6. 출처가 하단에 표시되는지\n")
    
    print("테스트 질문 예시:")
    print('- "What is machine learning?"')
    print('- "Explain the benefits of Docker"')
    print('- "Compare Python and JavaScript"\n')
    
    print("[ACTION] 브라우저를 여는 중...")
    try:
        webbrowser.open(FRONTEND_URL)
        print("[SUCCESS] 브라우저가 열렸습니다!")
        print("[INFO] 위 질문들을 입력하고 마크다운 렌더링을 확인하세요.")
    except Exception as e:
        print(f"[ERROR] 브라우저 열기 실패: {e}")
        print(f"[INFO] 수동으로 {FRONTEND_URL}에 접속하세요.")

if __name__ == "__main__":
    main()
