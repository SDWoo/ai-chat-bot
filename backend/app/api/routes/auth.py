from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user, create_access_token
from app.services.auth_service import (
    get_authorization_url,
    exchange_code_for_tokens,
    get_user_info_from_token,
    get_or_create_user,
    create_jwt_for_user,
)
from app.models.user import User

router = APIRouter()


@router.get("/login")
async def login():
    """Microsoft OAuth 로그인 URL로 리다이렉트"""
    if not settings.MS_CLIENT_ID:
        # MS 미설정 시 프론트엔드 로그인 페이지로 리다이렉트 (개발용 로그인 안내)
        redirect_url = f"{settings.FRONTEND_URL}/login?error=ms_not_configured"
        return RedirectResponse(url=redirect_url)
    auth_url = get_authorization_url()
    return RedirectResponse(url=auth_url)


@router.post("/dev-login")
async def dev_login(db: Session = Depends(get_db)):
    """
    개발용 로그인 (MS_CLIENT_ID 미설정 시만 사용).
    테스트 사용자 생성 후 JWT 반환.
    """
    if settings.MS_CLIENT_ID:
        raise HTTPException(status_code=400, detail="Use Microsoft login in production.")
    # 개발용 테스트 사용자
    user = db.query(User).filter(User.ms_oid == "dev-test-user").first()
    if not user:
        user = User(
            email="dev@localhost",
            name="개발 사용자",
            ms_oid="dev-test-user",
            ms_tenant_id="dev",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    token = create_jwt_for_user(user)
    return {"token": token, "user": {"id": user.id, "email": user.email, "name": user.name}}


@router.get("/callback")
async def auth_callback(
    code: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Microsoft OAuth callback.
    code 처리 후 User 생성/조회, JWT 반환, frontend로 redirect with token
    """
    if error:
        redirect_url = f"{settings.FRONTEND_URL}/login?error={error}"
        return RedirectResponse(url=redirect_url)

    if not code:
        redirect_url = f"{settings.FRONTEND_URL}/login?error=no_code"
        return RedirectResponse(url=redirect_url)

    token_result = exchange_code_for_tokens(code)
    if not token_result:
        redirect_url = f"{settings.FRONTEND_URL}/login?error=token_exchange_failed"
        return RedirectResponse(url=redirect_url)

    user_info = get_user_info_from_token(token_result)
    if not user_info or not user_info.get("oid"):
        redirect_url = f"{settings.FRONTEND_URL}/login?error=invalid_user_info"
        return RedirectResponse(url=redirect_url)

    user = get_or_create_user(
        db=db,
        ms_oid=user_info["oid"],
        email=user_info.get("email") or "",
        name=user_info.get("name"),
        ms_tenant_id=user_info.get("tid"),
    )
    token = create_jwt_for_user(user)
    redirect_url = f"{settings.FRONTEND_URL}/auth/callback?token={token}"
    return RedirectResponse(url=redirect_url)


@router.get("/me")
async def get_me(current_user: dict | None = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 (JWT 필요)"""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": current_user.get("user_id"),
        "user_id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "sub": current_user.get("sub"),
    }


@router.post("/logout")
async def logout():
    """
    로그아웃 (클라이언트에서 token 삭제).
    서버 측 세션 없음 - 클라이언트가 Bearer 토큰을 제거하면 됨.
    """
    return {"message": "Logged out successfully"}
