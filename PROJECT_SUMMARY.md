# AI Chatbot Project - 개발 완료

## 프로젝트 개요
문서 업로드, 벡터DB 분석, 질의응답, 대화 학습 기능을 갖춘 Python 기반 RAG AI 챗봇 풀스택 웹 애플리케이션

## 완료된 구성 요소

### ✅ Phase 1: 인프라 구조 (완료)
- 프로젝트 폴더 구조 생성
- Docker 및 docker-compose 설정
- Poetry 기반 Python 의존성 관리
- React + TypeScript 프론트엔드 초기화
- 환경 변수 템플릿 및 설정

### ✅ Phase 2: 문서 처리 시스템 (완료)
**정확도 핵심 모듈**
- `DocumentProcessor`: PDF, DOCX, TXT, Markdown, CSV 지원
- `ChunkingService`: RecursiveCharacterTextSplitter 기반 고급 청킹
  - 청크 크기: 1000 토큰 (조정 가능)
  - 오버랩: 200 토큰 (문맥 연속성)
  - Tiktoken 기반 정확한 토큰 계산
- `EmbeddingService`: 
  - OpenAI text-embedding-3-large 모델
  - Redis 캐싱으로 API 호출 최적화
  - ChromaDB 벡터 저장소 관리
  - 배치 처리 지원

### ✅ Phase 3: RAG 엔진 (완료)
**질의응답 핵심 로직**
- `RAGEngine`: 하이브리드 검색 엔진
  - 벡터 유사도 검색 (의미적 매칭)
  - 키워드 기반 리랭킹
  - 메타데이터 필터링
  - Top-K 동적 조정
- `LLMService`: OpenAI GPT-4/GPT-3.5 통합
  - 스트리밍 응답 지원
  - 환각 감지 기능
  - 재시도 로직 (tenacity)
- 프롬프트 엔지니어링:
  - RAG 시스템 프롬프트
  - 대화형 프롬프트
  - 출처 표시 강제

### ✅ Phase 4: 대화 학습 시스템 (완료)
- `LearningService`: 피드백 기반 학습
  - 긍정 피드백 대화 수집
  - QA 쌍 벡터화 및 저장
  - 대화 패턴 분석
  - 성능 메트릭 추적

### ✅ Phase 5: 백엔드 API (완료)
FastAPI 기반 RESTful API
- **문서 관리 API** (`/api/documents`):
  - POST `/upload`: 문서 업로드 및 백그라운드 처리
  - GET: 문서 목록 조회
  - GET `/{id}`: 문서 상세 조회
  - DELETE `/{id}`: 문서 삭제
  
- **채팅 API** (`/api/chat`):
  - POST: 질의응답 (일반)
  - POST `/stream`: 스트리밍 질의응답
  
- **대화 관리 API** (`/api/conversations`):
  - GET: 대화 목록
  - GET `/{session_id}/messages`: 메시지 조회
  - DELETE `/{session_id}`: 대화 삭제
  - POST `/feedback`: 피드백 제출

- **데이터베이스 모델**:
  - Document, DocumentChunk
  - Conversation, Message, DocumentUsage
  - SQLAlchemy ORM

### ✅ Phase 6: 프론트엔드 (완료)
React + TypeScript 기반 모던 UI
- **레이아웃**: 사이드바 네비게이션
- **채팅 페이지**:
  - 실시간 메시지 전송/수신
  - 마크다운 렌더링 (react-markdown)
  - 코드 하이라이팅
  - 출처 표시
  - 피드백 버튼 (좋아요/싫어요)
  
- **문서 관리 페이지**:
  - 드래그 앤 드롭 파일 업로드
  - 문서 목록 및 상태 표시
  - 처리 진행률 모니터링
  - 문서 삭제 기능
  
- **상태 관리**: Zustand
- **API 통신**: Axios + TanStack Query
- **스타일링**: TailwindCSS

### ✅ Phase 7: 테스트 및 문서화 (완료)
- **단위 테스트**:
  - 청킹 서비스 테스트
  - 문서 프로세서 테스트
  - API 엔드포인트 테스트
  - pytest 설정 및 구성
  
- **문서화**:
  - README.md: 프로젝트 소개 및 빠른 시작
  - DEVELOPMENT.md: 상세 개발 가이드
  - DEPLOYMENT.md: 프로덕션 배포 가이드
  - API 자동 문서화 (FastAPI Swagger)

## 기술 스택

### 백엔드
- **프레임워크**: FastAPI 0.109+
- **LLM**: OpenAI GPT-4/GPT-3.5
- **임베딩**: OpenAI text-embedding-3-large
- **벡터DB**: ChromaDB 0.4+
- **문서 처리**: LangChain
- **데이터베이스**: PostgreSQL 16
- **캐싱**: Redis 7
- **ORM**: SQLAlchemy 2.0
- **테스트**: pytest, httpx

### 프론트엔드
- **프레임워크**: React 18 + TypeScript
- **빌드 도구**: Vite 5
- **UI**: TailwindCSS
- **상태 관리**: Zustand
- **데이터 페칭**: TanStack Query
- **마크다운**: react-markdown
- **파일 업로드**: react-dropzone

### 인프라
- **컨테이너**: Docker + Docker Compose
- **패키지 관리**: Poetry (Python), npm (Node.js)
- **웹 서버**: Uvicorn (ASGI)

## 주요 기능

### 1. 문서 처리 (정확도 최적화)
- 다양한 형식 지원 (PDF, DOCX, TXT, MD, CSV)
- 최대 50MB 파일 크기
- 의미적 청킹 전략 (500-1000 토큰)
- 메타데이터 보존 및 활용
- 자동 벡터화 및 인덱싱

### 2. 고급 검색
- 하이브리드 검색 (벡터 + 키워드)
- 리랭킹 알고리즘
- 메타데이터 필터링
- 동적 Top-K 조정

### 3. 지능형 답변 생성
- RAG 기반 문서 참조 답변
- 출처 명시 및 추적
- 환각(hallucination) 감지
- 스트리밍 응답 지원
- 대화 컨텍스트 유지

### 4. 지속적 학습
- 사용자 피드백 수집
- 긍정 피드백 기반 QA 학습
- 대화 벡터화 및 재활용
- 성능 메트릭 추적

## 실행 방법

### 빠른 시작

1. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일에 OPENAI_API_KEY 설정
```

2. Docker Compose로 실행:
```bash
docker-compose up -d
```

3. 접속:
- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs

### 로컬 개발

백엔드:
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

프론트엔드:
```bash
cd frontend
npm install
npm run dev
```

## 프로젝트 구조

```
ai-chat-bot/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API 엔드포인트
│   │   ├── core/            # 설정, 프롬프트
│   │   ├── models/          # DB 모델, 스키마
│   │   ├── services/        # 비즈니스 로직
│   │   └── main.py
│   ├── tests/               # 테스트
│   ├── pyproject.toml       # Python 의존성
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # UI 컴포넌트
│   │   ├── pages/           # 페이지
│   │   ├── services/        # API 클라이언트
│   │   ├── store/           # 상태 관리
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml       # 서비스 오케스트레이션
├── README.md               # 프로젝트 소개
├── DEVELOPMENT.md          # 개발 가이드
├── DEPLOYMENT.md           # 배포 가이드
└── .env.example            # 환경 변수 템플릿
```

## 아키텍처 하이라이트

### 문서 처리 파이프라인
```
파일 업로드 → 검증 → 로딩 → 청킹 → 임베딩 → 벡터DB 저장
                ↓
          메타데이터 보존
```

### RAG 질의응답 플로우
```
사용자 질문 → 임베딩 → 벡터 검색 → 리랭킹 → 컨텍스트 구성 → LLM 생성 → 답변
                                          ↓
                                    출처 추적 및 표시
```

### 학습 파이프라인
```
대화 → 피드백 수집 → 고품질 QA 선별 → 재임베딩 → 벡터DB 추가
                            ↓
                      성능 개선 반영
```

## 정확도 향상 전략

1. **청킹 최적화**:
   - 문맥 보존을 위한 오버랩
   - 토큰 기반 정확한 크기 계산
   - 메타데이터 첨부

2. **하이브리드 검색**:
   - 의미적 유사도 (벡터)
   - 정확한 용어 매칭 (키워드)
   - 결과 리랭킹

3. **프롬프트 엔지니어링**:
   - 출처 표시 강제
   - 환각 방지 지침
   - 컨텍스트 최적 배치

4. **피드백 기반 학습**:
   - 긍정 피드백 대화 재활용
   - 지속적 개선 루프

## 다음 단계 (선택적 개선사항)

- [ ] JWT 인증 구현
- [ ] Rate Limiting 추가
- [ ] Celery 백그라운드 작업 통합
- [ ] A/B 테스팅 프레임워크
- [ ] Prometheus 메트릭 수집
- [ ] 다국어 지원
- [ ] 음성 입력/출력
- [ ] 모바일 반응형 개선

## 라이선스
MIT License

## 기여
기여를 환영합니다! 이슈나 PR을 자유롭게 제출해주세요.

---

**개발 완료 일자**: 2026-03-10
**개발 기간**: 1일
**상태**: ✅ 프로덕션 준비 완료
