# Railway 백엔드 배포 가이드

지금 쓰시는 DB·Redis 설정과 맞추려면 **Railway에서 PostgreSQL·Redis를 새로 만들고**, 그쪽 주소를 쓰면 됩니다.  
로컬 DB/Redis를 그대로 쓰는 건 Railway 서버에서 접속할 수 없으므로 **Railway가 주는 URL을 쓰는 방식**으로 가야 합니다.

---

## 1. 현재 설정과의 관계

| 항목 | 로컬 (지금) | Railway |
|------|-------------|--------|
| **PostgreSQL** | `POSTGRES_HOST=localhost` 등 개별 변수 | Railway PostgreSQL 추가 → **`DATABASE_URL`** 한 개만 설정 |
| **Redis** | `REDIS_HOST=localhost` 등 | Railway Redis 추가 → **`REDIS_URL`** 한 개만 설정 |
| **ChromaDB** | `./data/chromadb` (로컬 폴더) | **Volume** 하나 잡아서 `/data/chromadb` 에 마운트 (아래 참고) |
| **기타** | `.env` 그대로 | Railway 환경 변수에 같은 이름으로 입력 |

백엔드 코드는 **이미 Railway 쪽 방식을 지원**하도록 되어 있습니다.

- `DATABASE_URL` 이 있으면 → 그걸 사용 (Railway PostgreSQL)
- 없으면 → 기존처럼 `POSTGRES_*` 로 연결 (로컬)
- `REDIS_URL` 이 있으면 → 그걸 사용 (Railway Redis)
- 없으면 → 기존처럼 `REDIS_HOST` 등으로 연결 (로컬)

그래서 **로컬 설정이랑 충돌 나지 않고**, Railway에서는 Railway DB/Redis를 쓰면 됩니다.

---

## 2. Railway에서 할 일 (순서)

### 2-1. 프로젝트 생성

1. [Railway](https://railway.app) 로그인 (GitHub 연동 권장).
2. **New Project** → **Deploy from GitHub repo** 선택.
3. 저장소 `ai-chat-bot` 선택 후, **배포할 서비스**는 **백엔드만** 추가합니다.  
   - “Add a service” → **GitHub Repo** → 같은 repo 선택 후, **Root Directory**를 **`backend`** 로 지정합니다.  
   - 그러면 Railway가 `backend/` 안의 `Dockerfile` 로 빌드합니다.

### 2-2. PostgreSQL 추가

1. 같은 Project 안에서 **New** → **Database** → **PostgreSQL** 선택.
2. 생성되면 해당 PostgreSQL 서비스 클릭 → **Variables** 탭에서 **`DATABASE_URL`** (또는 `DATABASE_PRIVATE_URL`) 확인.
3. 백엔드 서비스 → **Variables** → **Add Variable** →  
   - **Variable:** `DATABASE_URL`  
   - **Value:** Railway가 보여주는 값 그대로 (다른 서비스 참조면 `${{Postgres.DATABASE_URL}}` 형태로 넣음).

로컬의 `POSTGRES_USER`, `POSTGRES_PASSWORD` 등은 **Railway에서는 넣지 않아도 됩니다.**  
Railway DB 주소는 `DATABASE_URL` 한 개로 이미 다 포함되어 있습니다.

### 2-3. Redis 추가

1. 같은 Project에서 **New** → **Database** → **Redis** 선택.
2. Redis 서비스의 **Variables**에서 **`REDIS_URL`** 확인.
3. 백엔드 서비스 **Variables**에 추가:  
   - **Variable:** `REDIS_URL`  
   - **Value:** `${{Redis.REDIS_URL}}` (또는 표시된 URL 복사).

로컬의 `REDIS_HOST`, `REDIS_PORT` 등은 Railway에서는 안 넣어도 됩니다.

### 2-4. ChromaDB용 볼륨 (문서 벡터 저장)

1. 백엔드 서비스 → **Settings** → **Volumes**.
2. **Add Volume** → Mount Path: **`/data`** (또는 `/data/chromadb` 등 원하는 경로).
3. 백엔드 **Variables**에 추가:  
   - **Variable:** `CHROMA_PERSIST_DIR`  
   - **Value:** `/data/chromadb` (볼륨 마운트 경로에 맞게).

이렇게 하면 재배포해도 문서 벡터 DB가 유지됩니다.

### 2-5. 나머지 환경 변수 (로컬이랑 동일하게)

아래는 **로컬 `.env` / docker 쓸 때랑 같은 의미**로 Railway **Variables**에 넣으면 됩니다.

| Variable | 설명 | 예시 |
|----------|------|------|
| `OPENAI_API_KEY` | (필수) OpenAI 키 | 로컬과 동일 |
| `JWT_SECRET_KEY` | (필수) JWT 서명용 시크릿 | 로컬과 동일 (프로덕션용으로 새로 만들어도 됨) |
| `ENVIRONMENT` | 환경 | `production` |
| `DEBUG` | 디버그 | `false` |
| `FRONTEND_URL` | 프론트 주소 | `https://saichat.vercel.app` |
| `CORS_ORIGINS` | CORS 허용 출처 | `["https://saichat.vercel.app","http://localhost:80","http://localhost"]` |
| (선택) `MS_CLIENT_ID` 등 | OAuth | 로컬과 동일 |

- **OAuth 리다이렉트:**  
  `MS_REDIRECT_URI` 는 **백엔드 공개 URL** 기준으로 설정합니다.  
  예: `https://당신백엔드.up.railway.app/api/auth/callback`  
  (배포 후 생성되는 도메인으로 바꾸면 됨.)

---

## 3. 빌드/시작 설정 (Railway)

- **Build:** Root Directory = `backend`, Dockerfile 사용 (기본).
- **Start Command:**  
  Dockerfile에 이미 `uvicorn` 이 있으면 그대로 둬도 됩니다.  
  프로덕션에서는 `--reload` 빼는 게 좋으므로, Railway에서 **Custom Start Command**를 쓰면:  
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
  (Railway는 `PORT` 환경 변수로 포트를 줍니다.)

Dockerfile에 `--reload` 가 있다면, Railway **Variables**에 `PORT=8000` 넣고, Start Command를 위처럼 바꿔도 됩니다.

---

## 4. 공개 URL 받기

1. 백엔드 서비스 → **Settings** → **Networking** → **Generate Domain**.
2. 나온 URL이 곧 **백엔드 공개 URL** (예: `https://ai-chat-bot-backend.up.railway.app`).

이 URL을 Vercel의 `VITE_API_URL` 에 넣고 재배포하면, [saichat.vercel.app](https://saichat.vercel.app) 이 이 백엔드를 쓰게 됩니다.

---

## 5. 요약: “내 DB/설정이랑 맞나?”

- **맞습니다.**  
  - 로컬: 기존처럼 `POSTGRES_*`, `REDIS_*`, `CHROMA_PERSIST_DIR` 사용.  
  - Railway: **같은 코드**에서 `DATABASE_URL`, `REDIS_URL`만 넣어주고, ChromaDB는 Volume + `CHROMA_PERSIST_DIR` 로 맞춰주면 됩니다.
- **로컬 DB/Redis를 Railway에서 직접 접속하는 건 불가**하므로, Railway용 PostgreSQL·Redis를 새로 두고, 그 URL을 쓰는 방식이 맞습니다.
- **설정이 바뀌는 부분**은 “연결 주소를 개별 호스트/포트가 아니라 URL 한 개로 바꾼다”는 것뿐이고, 앱 동작 방식은 동일합니다.

이 순서대로 하시면 Railway에서 백엔드를 공개 URL로 돌리면서, 지금 쓰시는 DB/설정 구조와 맞춰서 운영할 수 있습니다.
