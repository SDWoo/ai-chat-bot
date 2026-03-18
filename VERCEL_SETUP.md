# Vercel 배포 설정 (saichat.vercel.app)

## 1. Vercel 환경 변수 설정

Vercel 대시보드 → 프로젝트 → **Settings** → **Environment Variables**에서 추가:

| Name | Value | Environment |
|------|-------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Production, Preview, Development |

> ⚠️ `localhost:8000`은 **본인 PC에서만** 동작합니다. Docker 백엔드가 같은 PC에서 실행 중일 때만 사용하세요.
>
> 다른 PC나 외부에서 접속하려면 백엔드 공개 URL(예: `https://api.your-domain.com`)로 변경하세요.

## 2. 저장 후 Redeploy

환경 변수 추가/수정 후 **Deployments** → 최신 배포 → ⋮ → **Redeploy** 실행

## 3. 백엔드 CORS (이미 설정됨)

`.env`에 `https://saichat.vercel.app`가 CORS_ORIGINS에 포함되어 있습니다.
