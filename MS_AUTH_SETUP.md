# Microsoft 계정 로그인 설정 가이드

## 개요

Sindoh AI는 Microsoft(Microsoft Entra ID / Azure AD) 계정으로 로그인하며, 사용자별로 대화, 문서, 지식을 분리 관리합니다.

---

## 1. Azure Portal 앱 등록

### 1.1 앱 등록

1. [Azure Portal](https://portal.azure.com) 접속
2. **Microsoft Entra ID** (또는 Azure Active Directory) → **앱 등록** → **새 등록**
3. 설정:
   - **이름**: Sindoh AI (또는 원하는 이름)
   - **지원되는 계정 유형**: 
     - 단일 테넌트: 회사 내부만
     - 다중 테넌트: 여러 조직
     - 개인 Microsoft 계정 포함: 회사 + 개인 계정
   - **리디렉션 URI**: 
     - 플랫폼: **웹**
     - URI: `http://localhost:8000/api/auth/callback` (개발)
     - 프로덕션: `https://your-domain.com/api/auth/callback`

### 1.2 클라이언트 암호 생성

1. 앱 등록 → **인증서 및 암호**
2. **새 클라이언트 암호** 클릭
3. 설명 입력 후 만료 기간 선택
4. **값** 복사 (한 번만 표시됨)

### 1.3 API 권한

1. **API 권한** → **권한 추가**
2. **Microsoft Graph** 선택
3. **위임된 권한** 추가:
   - `User.Read`
   - `openid`
   - `email`
   - `profile`

---

## 2. 환경 변수 설정

### 2.1 Backend (.env 또는 docker-compose)

```env
# Microsoft OAuth
MS_CLIENT_ID=your-application-client-id
MS_CLIENT_SECRET=your-client-secret-value
MS_TENANT_ID=common
MS_REDIRECT_URI=http://localhost:8000/api/auth/callback
FRONTEND_URL=http://localhost:3000

# JWT (프로덕션에서 반드시 변경)
JWT_SECRET_KEY=your-secure-random-secret-key
```

### 2.2 Tenant ID

- **common**: 모든 Microsoft 계정 (개인 + 회사/학교)
- **organizations**: 회사/학교 계정만
- **consumers**: 개인 Microsoft 계정만
- **{tenant-id}**: 특정 조직만 (Azure Portal에서 확인)

---

## 3. 데이터베이스 마이그레이션

### 3.1 기존 DB가 있는 경우

```bash
cd backend
alembic upgrade head
```

### 3.2 새 DB인 경우

`init_db()`가 자동으로 모든 테이블을 생성합니다. 앱 시작 시 실행됩니다.

---

## 4. 개발용 로그인 (MS 미설정 시)

Microsoft 설정 없이 로컬 개발 시:

1. `MS_CLIENT_ID`를 비워두거나 설정하지 않음
2. 로그인 페이지에서 **개발용 로그인** 버튼 클릭
3. 테스트 사용자(`dev@localhost`)로 자동 로그인

**주의**: 프로덕션에서는 `MS_CLIENT_ID`를 반드시 설정하고, 개발용 로그인은 비활성화됩니다.

---

## 5. 사용자별 데이터 분리

| 데이터 | 분리 방식 |
|--------|-----------|
| **대화** | `conversations.user_id` |
| **문서** | `documents.user_id` |
| **지식** | `knowledge_entries.user_id` |
| **ChromaDB** | metadata에 `user_id` 필터 |

---

## 6. 로그인 플로우

```
1. 사용자 → "Microsoft로 로그인" 클릭
2. Backend /api/auth/login → Microsoft 로그인 페이지로 redirect
3. 사용자 Microsoft 로그인
4. Microsoft → Backend /api/auth/callback?code=...
5. Backend: code → token 교환, 사용자 정보 조회
6. Backend: User 생성/조회, JWT 발급
7. Backend → Frontend /auth/callback?token=... redirect
8. Frontend: token 저장, /api/auth/me로 사용자 정보 조회
9. Frontend → / (채팅 페이지) redirect
```

---

## 7. 문제 해결

### "MS_CLIENT_ID not configured"
- `.env` 또는 환경 변수에 `MS_CLIENT_ID` 설정
- 또는 개발용 로그인 사용

### "redirect_uri_mismatch"
- Azure Portal 앱 등록의 리디렉션 URI가 `MS_REDIRECT_URI`와 정확히 일치하는지 확인

### "Invalid client secret"
- 클라이언트 암호가 만료되었거나 잘못됨
- Azure Portal에서 새 암호 생성

### "401 Unauthorized"
- JWT 토큰 만료 또는 잘못됨
- 로그아웃 후 재로그인

---

## 8. 프로덕션 체크리스트

- [ ] `MS_CLIENT_ID`, `MS_CLIENT_SECRET` 설정
- [ ] `JWT_SECRET_KEY` 강력한 랜덤 값으로 변경
- [ ] `MS_REDIRECT_URI` 프로덕션 URL로 변경
- [ ] `FRONTEND_URL` 프로덕션 URL로 변경
- [ ] Azure 앱에 프로덕션 리디렉션 URI 추가
- [ ] HTTPS 적용
