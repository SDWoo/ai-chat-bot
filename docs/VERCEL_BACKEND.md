# Vercel( saichat.vercel.app )에서 백엔드 연동하기

## 왜 다른 기기/폰에서는 안 되나요?

- **내 PC**: 앱을 `localhost:80`(Docker)으로 쓰면 API 요청이 같은 PC의 nginx → 백엔드로 가서 동작합니다.
- **다른 기기**: `https://saichat.vercel.app` 로 접속하면, API 요청은 **빌드 시 설정한 API 주소**로만 갑니다.  
  그 주소가 비어 있거나 `localhost`면, 그 기기에는 백엔드가 없어서 실패합니다.

→ **백엔드를 인터넷에서 접근 가능한 URL에 두고**, Vercel 프론트가 그 URL을 쓰도록 설정해야 합니다.

## 해결 방법 (택 1)

### 1) 백엔드를 클라우드에 배포 (권장)

Railway, Render, Fly.io, AWS 등에 백엔드를 배포해 **공개 URL**을 받습니다.

- 예: `https://your-backend.railway.app`
- 해당 서비스에서 이 프로젝트의 **backend**만 배포하고, PostgreSQL/Redis는 해당 서비스가 제공하는 DB/캐시를 쓰거나, 같은 서비스의 add-on으로 연결합니다.

설정 후:

1. **Vercel**  
   - 프로젝트 → Settings → Environment Variables  
   - `VITE_API_URL` = `https://your-backend.railway.app` (끝에 슬래시 없이)  
   - 저장 후 **Redeploy** (중요: 변수 변경 후 재배포해야 빌드에 반영됨)

2. **백엔드**  
   - CORS에 `https://saichat.vercel.app` 포함 (이미 `docker-compose.prod.yml` 기본값에 포함됨)  
   - OAuth 사용 시 `FRONTEND_URL` / `MS_REDIRECT_URI` 등을 `https://saichat.vercel.app` 기준으로 설정

이후 **다른 컴퓨터·폰**에서도 `https://saichat.vercel.app` 로 접속하면 같은 백엔드로 요청이 갑니다.

### 2) 집 PC를 인터넷에 노출 (고급)

집에서 Docker로 백엔드를 돌리는 경우:

1. **공유기 포트포워딩**: 외부 8000 → 백엔드 돌리는 PC의 8000
2. **공인 IP 확인**: 예: `123.45.67.89`
3. (선택) **DDNS**: IP가 바뀌면 도메인으로 접근하도록 설정
4. **Vercel**  
   - `VITE_API_URL` = `http://123.45.67.89:8000` (또는 DDNS 도메인)  
   - HTTPS를 쓰려면 백엔드 앞단에 nginx + Let’s Encrypt 등으로 HTTPS 처리 필요

주의: 보안·방화벽·ISP 제한을 고려해야 하며, 운영용으로는 클라우드 배포가 더 안전합니다.

## 요약

| 구분 | 내용 |
|------|------|
| **다른 기기에서 안 되는 이유** | 백엔드가 내 PC에만 있어서, 다른 기기는 그 주소로 접근할 수 없음 |
| **해결** | 백엔드를 **공개 URL**에 두고, Vercel의 `VITE_API_URL`을 그 주소로 설정 후 재배포 |
| **CORS** | `https://saichat.vercel.app` 는 이미 기본 CORS에 포함됨 |
