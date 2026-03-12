# Sindoh AI - RAG 기반 문서 질의응답 시스템

Sindoh(신도리코) 회사용 문서 업로드, 벡터DB 분석, 질의응답, 대화 학습 기능을 갖춘 지식 기반 AI 챗봇 시스템입니다.

## 주요 기능

1. **문서 업로드 및 처리**: PDF, DOCX, TXT, Markdown, CSV 파일 지원
2. **고급 벡터 검색**: ChromaDB 기반 의미적 유사도 검색
3. **RAG 기반 질의응답**: OpenAI GPT 모델을 활용한 정확한 답변 생성
4. **실시간 스트리밍 답변**: SSE 기반 실시간 답변 생성 (체감 대기 시간 80% 단축)
5. **대화 학습**: 사용자 피드백 기반 지속적 성능 개선
6. **🌐 웹 검색 통합**: DuckDuckGo API를 통한 외부 웹 검색 (API 키 불필요) ⚡ NEW

## 기술 스택

### 백엔드
- FastAPI (Python 3.11)
- LangChain (문서 처리 및 RAG)
- ChromaDB (벡터 데이터베이스)
- OpenAI GPT-4 / GPT-3.5
- PostgreSQL (대화 이력 저장)
- Redis (캐싱 및 세션 관리)

### 프론트엔드
- React 18 + TypeScript
- TailwindCSS
- TanStack Query
- React Router

### 인프라
- Docker & Docker Compose
- Poetry (Python 패키지 관리)

## 시작하기

### 사전 요구사항

- Docker 및 Docker Compose
- OpenAI API Key

### 설치 및 실행

1. 저장소 클론 및 환경 변수 설정:

```bash
cd ai-chat-bot
cp .env.example .env
```

2. `.env` 파일에 OpenAI API Key 설정:

```env
OPENAI_API_KEY=your-actual-api-key-here
```

3. Docker Compose로 모든 서비스 실행:

```bash
docker-compose up -d
```

4. 애플리케이션 접속:
   - 프론트엔드: http://localhost:3000
   - 백엔드 API: http://localhost:8000
   - API 문서: http://localhost:8000/docs

### 프로덕션 배포

```bash
# 1. 환경 변수 설정
cp .env.prod.example .env
# .env 파일에 OPENAI_API_KEY, POSTGRES_PASSWORD, JWT_SECRET_KEY 필수 설정

# 2. 배포 실행 (Windows)
deploy.bat

# 또는 (Linux/Mac)
chmod +x deploy.sh && ./deploy.sh
```

배포 후 http://localhost:80 에서 앱에 접속합니다.

### 로컬 개발 환경

#### 빠른 시작 (Windows)

**백엔드:**
```bash
# 옵션 1: 스크립트 사용
start_backend.bat

# 옵션 2: 수동 실행
cd backend
poetry install  # 새로운 의존성(duckduckgo-search) 포함
poetry run uvicorn app.main:app --reload
```

> 💡 **웹 검색 기능**: 새로 추가된 `duckduckgo-search` 패키지가 자동으로 설치됩니다. API 키가 필요하지 않습니다!

**프론트엔드:**
```bash
# 옵션 1: 스크립트 사용
start_frontend.bat

# 옵션 2: 수동 실행
cd frontend
npm install
npm run dev
```

#### 스트리밍 테스트

```bash
# 백엔드 스트리밍 직접 테스트
python test_streaming.py
```

📖 자세한 내용은 [STREAMING_TEST_GUIDE.md](./STREAMING_TEST_GUIDE.md) 참조

## 프로젝트 구조

```
ai-chat-bot/
├── backend/
│   ├── app/
│   │   ├── api/          # API 라우터
│   │   ├── core/         # 설정, 보안
│   │   ├── services/     # 비즈니스 로직
│   │   ├── models/       # 데이터 모델
│   │   └── main.py       # FastAPI 애플리케이션
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## API 엔드포인트

### 문서 관리
- `POST /api/documents/upload` - 문서 업로드
- `GET /api/documents` - 문서 목록 조회
- `DELETE /api/documents/{id}` - 문서 삭제

### 채팅
- `POST /api/chat` - 질의응답 (비스트리밍)
- `POST /api/chat/stream` - 질의응답 (스트리밍, SSE) ⚡ NEW
- `GET /api/conversations` - 대화 이력 조회
- `POST /api/feedback` - 답변 피드백 제공

### 시스템
- `GET /api/health` - 헬스 체크

## 개발 로드맵

- [x] Phase 1: 프로젝트 초기 설정
- [x] Phase 2: 문서 처리 시스템
- [x] Phase 3: RAG 엔진
- [x] Phase 4: 대화 학습 시스템
- [x] Phase 5: 백엔드 API 구현
- [x] Phase 6: 프론트엔드 구현
- [x] Phase 7: 통합 및 테스트
- [x] Phase 8: 실시간 스트리밍 답변 (SSE) ⚡ NEW
- [x] Phase 9: 웹 검색 통합 (DuckDuckGo API) 🌐 NEW

## 최신 업데이트

### 🌐 웹 검색 통합 기능 (2026-03-11)

**외부 웹 검색 결과를 AI 답변에 통합!**

- ✅ DuckDuckGo API 기반 웹 검색 (무료, API 키 불필요)
- ✅ 문서, 지식베이스, 웹 검색을 통합 검색 엔진으로 통합
- ✅ 검색 소스 선택 UI (체크박스로 손쉽게 선택)
- ✅ 소스별 가중치 조정 및 결과 재정렬
- ✅ 에러 처리 및 자동 재시도

**사용 방법:**
1. 채팅 입력창 위에 있는 검색 소스 체크박스에서 원하는 소스 선택
2. "📄 문서", "💡 지식베이스", "🌐 웹 검색" 중 선택 가능
3. 여러 소스를 동시에 선택하여 통합 검색 가능

### 🎉 스트리밍 답변 기능 구현 (2026-03-11)

**체감 대기 시간 80% 감소!** (10초 → 1-2초)

- ✅ SSE 기반 실시간 답변 스트리밍
- ✅ 타이핑 애니메이션 효과
- ✅ 자동 재시도 및 에러 처리
- ✅ ChatGPT 수준의 UX

📊 자세한 내용: [STREAMING_IMPLEMENTATION_REPORT.md](./STREAMING_IMPLEMENTATION_REPORT.md)

## 라이선스

MIT License

## 기여

기여를 환영합니다! 이슈나 PR을 자유롭게 제출해주세요.
