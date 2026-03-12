# AI Chatbot Development Guide

## 개발 환경 설정

### 필수 요구사항
- Docker & Docker Compose
- OpenAI API Key
- Python 3.11+ (로컬 개발 시)
- Node.js 20+ (로컬 개발 시)

### 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

## 프로젝트 실행

### Docker로 전체 시스템 실행

```bash
docker-compose up -d
```

이 명령어는 다음 서비스를 시작합니다:
- PostgreSQL (포트 5432)
- Redis (포트 6379)
- Backend API (포트 8000)
- Frontend (포트 3000)

### 로그 확인

```bash
docker-compose logs -f
```

### 서비스 중지

```bash
docker-compose down
```

### 볼륨 포함 완전 삭제

```bash
docker-compose down -v
```

## 로컬 개발

### 백엔드 개발

```bash
cd backend

poetry install

poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 문서: http://localhost:8000/docs

### 프론트엔드 개발

```bash
cd frontend

npm install

npm run dev
```

애플리케이션: http://localhost:3000

## 테스트

### 백엔드 테스트

```bash
cd backend
poetry run pytest
```

### 특정 테스트 실행

```bash
poetry run pytest tests/test_chunking.py -v
```

### 커버리지 포함 테스트

```bash
poetry run pytest --cov=app --cov-report=html
```

## 주요 기능

### 1. 문서 업로드
- 지원 형식: PDF, DOCX, TXT, Markdown, CSV
- 최대 파일 크기: 50MB
- 자동 처리 및 벡터화

### 2. 질의응답
- RAG 기반 답변 생성
- 하이브리드 검색 (벡터 + 키워드)
- 출처 표시
- 실시간 스트리밍 응답

### 3. 대화 학습
- 사용자 피드백 수집
- 긍정 피드백 기반 학습
- 지속적 성능 개선

## API 엔드포인트

### 문서 관리
- `POST /api/documents/upload` - 문서 업로드
- `GET /api/documents` - 문서 목록
- `GET /api/documents/{id}` - 문서 상세
- `DELETE /api/documents/{id}` - 문서 삭제

### 채팅
- `POST /api/chat` - 질의응답
- `POST /api/chat/stream` - 스트리밍 질의응답

### 대화 관리
- `GET /api/conversations` - 대화 목록
- `GET /api/conversations/{session_id}/messages` - 메시지 조회
- `DELETE /api/conversations/{session_id}` - 대화 삭제
- `POST /api/conversations/feedback` - 피드백 제출

## 아키텍처

### 백엔드 구조
```
backend/app/
├── api/routes/          # API 엔드포인트
│   ├── documents.py
│   ├── chat.py
│   └── conversations.py
├── services/            # 비즈니스 로직
│   ├── document_processor.py
│   ├── chunking.py
│   ├── embedding_service.py
│   ├── rag_engine.py
│   ├── llm_service.py
│   └── learning_service.py
├── models/              # 데이터 모델
│   ├── document.py
│   ├── conversation.py
│   └── schemas.py
├── core/                # 핵심 설정
│   ├── config.py
│   ├── database.py
│   └── prompts.py
└── main.py             # 애플리케이션 진입점
```

### 프론트엔드 구조
```
frontend/src/
├── components/         # 재사용 가능한 컴포넌트
│   └── Layout.tsx
├── pages/              # 페이지 컴포넌트
│   ├── ChatPage.tsx
│   └── DocumentsPage.tsx
├── services/           # API 통신
│   └── api.ts
├── store/              # 상태 관리
│   └── chatStore.ts
└── App.tsx             # 앱 루트
```

## 문제 해결

### 컨테이너가 시작되지 않을 때

```bash
docker-compose down
docker-compose up --build
```

### 데이터베이스 초기화

```bash
docker-compose down -v
docker-compose up -d
```

### 백엔드 로그 확인

```bash
docker-compose logs -f backend
```

### 프론트엔드 빌드 오류

```bash
cd frontend
rm -rf node_modules
npm install
```

## 성능 최적화

### 청킹 파라미터 조정
`backend/app/core/config.py`에서 다음 값을 조정:
- `CHUNK_SIZE`: 청크 크기 (기본: 1000)
- `CHUNK_OVERLAP`: 청크 오버랩 (기본: 200)

### 검색 결과 수 조정
채팅 요청 시 `top_k` 파라미터 조정 (기본: 4)

### 캐싱
Redis를 통해 임베딩 결과를 자동으로 캐싱합니다.

## 보안 고려사항

1. `.env` 파일을 절대 커밋하지 마세요
2. 프로덕션에서는 강력한 `JWT_SECRET_KEY` 사용
3. CORS 설정을 프로덕션 도메인으로 제한
4. API Rate Limiting 구현
5. 파일 업로드 크기 제한 확인

## 기여하기

1. 새 기능 추가 전 이슈 생성
2. Feature 브랜치에서 개발
3. 테스트 작성
4. PR 제출

## 라이선스

MIT License
