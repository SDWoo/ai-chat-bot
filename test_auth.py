#!/usr/bin/env python3
"""MS 로그인 및 사용자별 데이터 분리 통합 테스트"""
import requests

API = "http://localhost:8000"

def test_dev_login():
    print("1. 개발용 로그인 테스트...")
    r = requests.post(f"{API}/api/auth/dev-login")
    assert r.status_code == 200, f"dev-login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data
    assert "user" in data
    print(f"   OK - token received, user: {data['user']['email']}")
    return data["token"]

def test_auth_me(token):
    print("2. /api/auth/me 테스트...")
    r = requests.get(f"{API}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"me failed: {r.status_code} {r.text}"
    data = r.json()
    print(f"   OK - user_id: {data.get('user_id')}, email: {data.get('email')}")
    return data.get("user_id")

def test_chat(token):
    print("3. 채팅 API (인증 필요) 테스트...")
    r = requests.post(
        f"{API}/api/chat",
        json={"message": "테스트 메시지"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, f"chat failed: {r.status_code} {r.text}"
    data = r.json()
    print(f"   OK - conversation_id: {data.get('conversation_id')}")

def test_conversations(token):
    print("4. 대화 목록 (사용자별) 테스트...")
    r = requests.get(
        f"{API}/api/conversations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, f"conversations failed: {r.status_code} {r.text}"
    print(f"   OK - conversations: {len(r.json())}")

def test_unauthorized():
    print("5. 비인증 401 테스트...")
    r = requests.get(f"{API}/api/auth/me")
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print("   OK - 401 as expected")

def test_knowledge_api(token):
    print("6. 지식 API (인증 필요) 테스트...")
    r = requests.get(
        f"{API}/api/knowledge",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, f"knowledge failed: {r.status_code} {r.text}"
    data = r.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    print(f"   OK - entries: {len(data)}")

def test_chat_stream_retry_no_duplicate(token):
    """재시도 시 동일 conversation_id 사용하여 중복 대화 생성 방지 테스트"""
    print("7. 채팅 스트림 재시도 시 중복 대화 방지 테스트...")
    import uuid
    conv_id = str(uuid.uuid4())
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"message": "재시도 테스트", "conversation_id": conv_id, "search_sources": ["documents", "knowledge"]}

    # 첫 요청
    r1 = requests.post(f"{API}/api/chat/stream", json=payload, headers=headers, stream=True, timeout=10)
    assert r1.status_code == 200, f"stream failed: {r1.status_code}"
    for line in r1.iter_lines():
        if line and b"metadata" in line:
            break

    # 동일 conversation_id로 재요청 (재시도 시뮬레이션)
    r2 = requests.post(f"{API}/api/chat/stream", json=payload, headers=headers, stream=True, timeout=10)
    assert r2.status_code == 200, f"retry stream failed: {r2.status_code}"

    # 대화 목록에서 해당 conversation이 1개만 있는지 확인
    convs = requests.get(f"{API}/api/conversations", headers=headers).json()
    matching = [c for c in convs if c.get("session_id") == conv_id]
    assert len(matching) == 1, f"Expected 1 conversation, got {len(matching)}"
    print(f"   OK - conversation_id 재사용 시 중복 없음")

def test_ms_login_redirect():
    print("8. MS 미설정 시 로그인 리다이렉트 테스트...")
    r = requests.get(f"{API}/api/auth/login", allow_redirects=True)
    # MS 미설정 시 프론트엔드 /login?error=ms_not_configured로 리다이렉트
    assert "login" in r.url and "ms_not_configured" in r.url, f"Expected redirect to login with error, got {r.url}"
    print("   OK - redirects to login with ms_not_configured")

if __name__ == "__main__":
    try:
        token = test_dev_login()
        test_auth_me(token)
        test_chat(token)
        test_conversations(token)
        test_chat_stream_retry_no_duplicate(token)
        test_knowledge_api(token)
        test_unauthorized()
        test_ms_login_redirect()
        print("\n[SUCCESS] All auth tests passed!")
    except Exception as e:
        print(f"\n[FAIL] {e}")
        raise
