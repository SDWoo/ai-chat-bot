from typing import Optional

import msal
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User


def get_msal_app():
    """MSAL ConfidentialClientApplication 인스턴스 생성"""
    return msal.ConfidentialClientApplication(
        settings.MS_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{settings.MS_TENANT_ID}",
        client_credential=settings.MS_CLIENT_SECRET,
    )


def get_authorization_url() -> str:
    """Microsoft OAuth 로그인 URL 생성"""
    app = get_msal_app()
    scopes = ["User.Read", "openid", "email", "profile"]
    auth_url = app.get_authorization_request_url(
        scopes=scopes,
        redirect_uri=settings.MS_REDIRECT_URI,
        response_type="code",
    )
    return auth_url


def exchange_code_for_tokens(code: str) -> Optional[dict]:
    """OAuth authorization code를 액세스 토큰으로 교환"""
    app = get_msal_app()
    result = app.acquire_token_by_authorization_code(
        code=code,
        scopes=["User.Read", "openid", "email", "profile"],
        redirect_uri=settings.MS_REDIRECT_URI,
    )
    return result if "access_token" in result else None


def get_user_info_from_token(token_result: dict) -> Optional[dict]:
    """MSAL 토큰 결과에서 사용자 정보 추출 (id_token_claims)"""
    claims = token_result.get("id_token_claims") or {}
    oid = claims.get("oid")
    if not oid:
        return None
    return {
        "oid": oid,
        "email": claims.get("preferred_username") or claims.get("email") or "",
        "name": claims.get("name"),
        "tid": claims.get("tid"),  # tenant id
    }


def get_or_create_user(db: Session, ms_oid: str, email: str, name: Optional[str], ms_tenant_id: Optional[str]) -> User:
    """ms_oid 기준으로 User 조회 또는 생성"""
    user = db.query(User).filter(User.ms_oid == ms_oid).first()
    if user:
        user.email = email
        user.name = name
        user.ms_tenant_id = ms_tenant_id
        db.commit()
        db.refresh(user)
        return user

    user = User(
        email=email,
        name=name,
        ms_oid=ms_oid,
        ms_tenant_id=ms_tenant_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_jwt_for_user(user: User) -> str:
    """User 정보로 JWT 생성"""
    return create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "user_id": user.id,
        }
    )
