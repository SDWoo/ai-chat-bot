# Context Memory Agent 사용 가이드

## 🎯 빠른 시작

### 1. 기본 사용법

Context Memory Agent는 자동으로 활성화됩니다. 같은 `conversation_id`를 사용하면 대화 맥락이 유지됩니다.

### 2. API 사용 예제

#### 첫 번째 질문 (새 대화 시작)
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "3년차 복지 알려줘",
    "conversation_id": null,
    "collection_name": "documents",
    "top_k": 4
  }'
```

**응답 예시:**
```json
{
  "conversation_id": "abc-123-def-456",
  "message": "## 3년차 복지 혜택\n\n### 핵심 내용\n- **연차**: 15일...",
  "sources": [...],
  "created_at": "2026-03-11T10:00:00"
}
```

#### 연속 질문 (컨텍스트 유지)
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "그럼 경조사는?",
    "conversation_id": "abc-123-def-456",
    "collection_name": "documents",
    "top_k": 4
  }'
```

**응답 예시:**
```json
{
  "conversation_id": "abc-123-def-456",
  "message": "## 3년차 경조사 혜택\n\n앞서 말씀드린 3년차 복지 중 경조사...",
  "sources": [...],
  "created_at": "2026-03-11T10:01:00"
}
```

**주목**: "3년차"가 자동으로 유지됩니다! 🎉

### 3. 프론트엔드 통합 예제 (JavaScript)

```javascript
// 대화 세션 클래스
class ChatSession {
  constructor() {
    this.conversationId = null;
  }

  async sendMessage(message) {
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        conversation_id: this.conversationId,
        collection_name: 'documents',
        top_k: 4,
      }),
    });

    const data = await response.json();
    
    // 첫 번째 응답인 경우 conversation_id 저장
    if (!this.conversationId) {
      this.conversationId = data.conversation_id;
    }

    return data;
  }

  // 새 대화 시작
  reset() {
    this.conversationId = null;
  }
}

// 사용 예제
const chat = new ChatSession();

// 첫 번째 질문
const response1 = await chat.sendMessage('3년차 복지 알려줘');
console.log(response1.message);

// 연속 질문 (컨텍스트 유지)
const response2 = await chat.sendMessage('그럼 경조사는?');
console.log(response2.message); // "3년차"가 유지됨

// 새 대화 시작
chat.reset();
const response3 = await chat.sendMessage('10년차 복지는?');
console.log(response3.message); // 새로운 컨텍스트
```

### 4. Python 클라이언트 예제

```python
import requests
import json

class ChatClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.conversation_id = None
    
    def send_message(self, message: str) -> dict:
        """메시지 전송 및 응답 받기"""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "message": message,
                "conversation_id": self.conversation_id,
                "collection_name": "documents",
                "top_k": 4,
            }
        )
        
        data = response.json()
        
        # conversation_id 저장
        if not self.conversation_id:
            self.conversation_id = data["conversation_id"]
        
        return data
    
    def reset(self):
        """새 대화 시작"""
        self.conversation_id = None

# 사용 예제
if __name__ == "__main__":
    client = ChatClient()
    
    # 연속 대화 테스트
    print("질문 1: 3년차 복지 알려줘")
    response1 = client.send_message("3년차 복지 알려줘")
    print(f"답변: {response1['message'][:200]}...\n")
    
    print("질문 2: 그럼 경조사는?")
    response2 = client.send_message("그럼 경조사는?")
    print(f"답변: {response2['message'][:200]}...\n")
    
    print("질문 3: 신청은 어떻게 해?")
    response3 = client.send_message("신청은 어떻게 해?")
    print(f"답변: {response3['message'][:200]}...\n")
```

## 💡 활용 시나리오

### 시나리오 1: 조건부 질문
```
사용자: "5년차 복지 알려줘"
AI: "5년차는 연차 15일, 경조금 50만원..."

사용자: "그럼 경조사 범위는?"
AI: "5년차 경조사 범위는..." ✅ "5년차" 유지

사용자: "신청 방법은?"
AI: "5년차 경조사 신청은..." ✅ "5년차 경조사" 유지
```

### 시나리오 2: 비교 질문
```
사용자: "3년차와 5년차 연차 차이 알려줘"
AI: "3년차는 15일, 5년차는 16일..."

사용자: "그럼 급여는?"
AI: "3년차와 5년차의 급여 차이는..." ✅ 비교 대상 유지
```

### 시나리오 3: 심화 질문
```
사용자: "재택근무 정책 알려줘"
AI: "재택근무는 주 2회..."

사용자: "신청 조건은?"
AI: "재택근무 신청 조건은..." ✅ 주제 유지

사용자: "승인 절차는?"
AI: "재택근무 승인 절차는..." ✅ 주제 유지
```

## 🔧 설정 조정

### 히스토리 길이 조정
`backend/app/services/rag_engine.py`:
```python
MAX_HISTORY_MESSAGES = 5  # 5 → 10으로 변경 가능
```

### 토큰 제한 조정
`backend/app/services/rag_engine.py`:
```python
MAX_CONTEXT_TOKENS = 4000  # 4000 → 8000으로 변경 가능
```

**주의**: 토큰 제한을 늘리면 응답 속도가 느려질 수 있습니다.

## 📊 모니터링

### 로그 확인
```bash
# 대화 히스토리 관련 로그 확인
tail -f logs/app.log | grep "Chat history"
```

**로그 예시:**
```
INFO: Chat history retrieved conversation_id=abc-123 history_length=4
INFO: Chat history formatted messages_count=4 total_tokens=856
INFO: Generating RAG answer query="그럼 경조사는?" has_chat_history=True
INFO: Using conversational prompt with history
```

### 메타데이터 확인
응답의 `metadata` 필드를 확인하세요:
```json
{
  "metadata": {
    "documents_found": 3,
    "filtered_sources": 2,
    "timestamp": "2026-03-11T10:00:00",
    "context_used": true  // ← 컨텍스트 사용 여부
  }
}
```

## 🐛 트러블슈팅

### 문제 1: 컨텍스트가 유지되지 않음
**원인**: `conversation_id`가 전달되지 않음
**해결**: 첫 응답에서 받은 `conversation_id`를 다음 요청에 포함

### 문제 2: 너무 오래된 정보가 유지됨
**원인**: 대화가 너무 길어짐
**해결**: 새 주제일 때는 `conversation_id=null`로 새 대화 시작

### 문제 3: 토큰 제한 에러
**원인**: 히스토리가 너무 길어서 토큰 초과
**해결**: 자동으로 처리됨 (오래된 메시지 자동 제거)

## 📈 성능 팁

### 1. 적절한 대화 길이 유지
- 3-5번의 연속 질문이 최적
- 주제가 바뀌면 새 대화 시작

### 2. 명확한 지시어 사용
- "그럼", "그거", "여기서" 등을 사용하면 컨텍스트 유지가 명확함
- 새 주제는 명시적으로 시작

### 3. 모니터링
- `context_used` 플래그로 컨텍스트 사용 확인
- 로그에서 토큰 사용량 모니터링

## 🎓 학습 자료

### 관련 개념
1. **Conversation Memory**: 대화 기억 관리
2. **Context Window**: LLM 컨텍스트 윈도우
3. **Token Counting**: 토큰 계산 방법

### 추가 읽을거리
- [OpenAI Chat Completions API](https://platform.openai.com/docs/guides/chat)
- [LangChain Memory Types](https://python.langchain.com/docs/modules/memory/)
- [Token Counting with tiktoken](https://github.com/openai/tiktoken)

---

**버전**: 1.0.0  
**최종 업데이트**: 2026-03-11
