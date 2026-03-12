# 웹 검색 통합 기능 설정 가이드

## 📋 개요

이 가이드는 AI 챗봇에 새로 추가된 **웹 검색 통합 기능**의 설정 방법을 안내합니다.

## ✨ 주요 기능

- **DuckDuckGo API 기반 웹 검색**: 무료로 사용 가능하며 API 키가 필요하지 않습니다
- **통합 검색 엔진**: 문서, 지식베이스, 웹 검색을 하나의 인터페이스로 통합
- **소스별 가중치 조정**: 지식베이스 > 문서 > 웹 검색 순으로 우선순위 적용
- **자동 재시도**: 네트워크 오류 시 자동으로 재시도
- **검색 소스 선택 UI**: 사용자가 원하는 검색 소스를 선택 가능

## 🚀 설치 방법

### 1. 백엔드 의존성 설치

```bash
cd backend
poetry install
```

새로 추가된 `duckduckgo-search` 패키지가 자동으로 설치됩니다.

### 2. 수동 설치 (필요한 경우)

Poetry가 제대로 작동하지 않는 경우:

```bash
cd backend
poetry add duckduckgo-search
```

또는 pip를 사용하는 경우:

```bash
pip install duckduckgo-search
```

### 3. 백엔드 서버 재시작

```bash
# Windows
start_backend.bat

# Linux/Mac
cd backend
poetry run uvicorn app.main:app --reload
```

### 4. 프론트엔드 (변경사항 자동 반영)

프론트엔드는 이미 업데이트되었으며, 개발 서버가 실행 중이라면 자동으로 반영됩니다.

```bash
# 실행 중이 아닌 경우
cd frontend
npm run dev
```

## 📖 사용 방법

### 1. 검색 소스 선택

채팅 입력창 위에 있는 체크박스에서 원하는 검색 소스를 선택합니다:

- **📄 문서**: 업로드한 문서에서 검색
- **💡 지식베이스**: 저장된 지식베이스 항목에서 검색
- **🌐 웹 검색**: DuckDuckGo를 통한 외부 웹 검색

### 2. 통합 검색

여러 소스를 동시에 선택할 수 있습니다. 예:
- 문서 + 지식베이스
- 문서 + 웹 검색
- 문서 + 지식베이스 + 웹 검색

### 3. 질문하기

선택한 검색 소스에 따라 AI가 적절한 답변을 생성합니다.

## 🏗️ 아키텍처

```
사용자 질문
    ↓
ChatPage (검색 소스 선택)
    ↓
UnifiedSearchEngine
    ↓
┌─────────────┬──────────────────┬──────────────┐
│   문서      │   지식베이스      │   웹 검색    │
│  (RAG)      │ (Knowledge DB)   │ (DuckDuckGo) │
└─────────────┴──────────────────┴──────────────┘
    ↓
결과 통합 및 재정렬 (가중치 기반)
    ↓
LLM 답변 생성
    ↓
사용자에게 답변 반환
```

## 🔧 고급 설정

### 소스별 가중치 조정

`backend/app/services/unified_search.py`에서 가중치를 조정할 수 있습니다:

```python
self.source_weights = {
    "knowledge_base": 1.2,  # 지식베이스 우선순위 높음
    "documents": 1.0,       # 문서는 기본
    "web": 0.8,            # 웹 검색은 낮음
}
```

### 웹 검색 결과 개수 조정

`backend/app/services/web_search.py`에서 기본 결과 개수를 변경할 수 있습니다:

```python
async def search(
    self,
    query: str,
    max_results: int = 10,  # 기본 10개, 필요에 따라 조정
    ...
)
```

### 지역 설정

한국어 검색 결과를 우선적으로 받으려면 `region` 파라미터를 조정합니다:

```python
results = self.ddgs.text(
    keywords=query,
    region="kr-kr",  # 한국
    ...
)
```

다른 지역:
- `us-en`: 미국
- `uk-en`: 영국
- `jp-jp`: 일본
- `wt-wt`: 전세계

## ⚠️ 주의사항

### 1. API 키 불필요

DuckDuckGo API는 **무료**이며 **API 키가 필요하지 않습니다**. 환경 변수 설정이 필요 없습니다.

### 2. Rate Limiting

DuckDuckGo는 과도한 요청에 대해 일시적으로 차단할 수 있습니다. 
- 일반적인 사용에는 문제 없음
- 대량의 자동화된 요청 시 주의 필요

### 3. 검색 품질

- 최신 정보: ✅ 좋음
- 한국어 검색: ✅ 양호
- 전문 정보: ⚠️ 제한적 (내부 문서 검색 권장)

## 🧪 테스트

### 백엔드 단위 테스트

```bash
cd backend
poetry run pytest tests/test_web_search.py -v
```

### 통합 테스트

1. 백엔드와 프론트엔드 실행
2. 채팅 페이지 접속
3. "🌐 웹 검색" 체크박스 선택
4. "2026년 최신 AI 트렌드는?" 같은 최신 정보 질문
5. 웹에서 가져온 출처가 표시되는지 확인

### API 직접 테스트

```python
import requests
import json

url = "http://localhost:8000/api/chat"
data = {
    "message": "인공지능 최신 뉴스",
    "search_sources": ["web"],
    "top_k": 5
}

response = requests.post(url, json=data)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

## 🐛 문제 해결

### 문제 1: "Web search is disabled" 로그

**원인**: `duckduckgo-search` 패키지가 설치되지 않음

**해결**:
```bash
cd backend
poetry add duckduckgo-search
# 또는
pip install duckduckgo-search
```

### 문제 2: 검색 결과가 없음

**원인**: 
- 네트워크 연결 문제
- DuckDuckGo API 일시적 제한

**해결**:
- 인터넷 연결 확인
- 잠시 후 다시 시도
- 로그 확인: `backend/logs/`

### 문제 3: 프론트엔드에 체크박스가 보이지 않음

**원인**: 
- 프론트엔드 빌드가 최신이 아님
- 브라우저 캐시

**해결**:
```bash
# 프론트엔드 재시작
cd frontend
npm run dev

# 브라우저에서 Ctrl+F5 (강력 새로고침)
```

## 📚 추가 리소스

- [DuckDuckGo Search API](https://github.com/deedy5/duckduckgo_search)
- [프로젝트 README](./README.md)
- [API 문서](http://localhost:8000/docs)

## 💡 팁

### 최적의 검색 소스 조합

| 질문 유형 | 권장 소스 |
|---------|---------|
| 회사 내부 정책, 절차 | 📄 문서 + 💡 지식베이스 |
| 기술 문서, 매뉴얼 | 📄 문서 |
| 최신 뉴스, 트렌드 | 🌐 웹 검색 |
| 일반 지식, 개념 | 💡 지식베이스 + 🌐 웹 검색 |
| 복합 질문 | 📄 문서 + 💡 지식베이스 + 🌐 웹 검색 |

### 성능 최적화

- 웹 검색은 다른 소스보다 느릴 수 있습니다 (네트워크 지연)
- 빠른 응답이 필요한 경우 문서/지식베이스만 사용
- 캐싱은 자동으로 적용됩니다

## 🎉 완료!

웹 검색 통합 기능이 성공적으로 설정되었습니다. 
이제 AI 챗봇이 내부 문서뿐만 아니라 최신 웹 정보도 활용하여 답변할 수 있습니다!
