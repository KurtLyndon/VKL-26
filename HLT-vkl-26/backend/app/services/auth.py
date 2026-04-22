from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import AccountGroupPermission, AppPermission, UserAccount

security = HTTPBearer(auto_error=False)


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def hash_password(password: str, *, iterations: int = 120000) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${base64.b64encode(digest).decode('ascii')}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iteration_text, salt, digest = stored_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iteration_text))
    return hmac.compare_digest(base64.b64encode(computed).decode("ascii"), digest)


def _sign_token(payload: dict) -> str:
    settings = get_settings()
    encoded_payload = _b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{encoded_payload}.{_b64_encode(signature)}"


def _verify_token(token: str) -> dict:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format") from exc

    settings = get_settings()
    expected_signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(_b64_encode(expected_signature), encoded_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")

    payload = json.loads(_b64_decode(encoded_payload))
    expires_at = datetime.fromisoformat(payload["exp"])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    return payload


def get_user_permissions(db: Session, user: UserAccount) -> list[str]:
    if user.group_id is None:
        return []
    rows = db.execute(
        select(AppPermission.code)
        .join(AccountGroupPermission, AccountGroupPermission.permission_id == AppPermission.id)
        .where(AccountGroupPermission.group_id == user.group_id)
        .where(AccountGroupPermission.is_enabled.is_(True))
        .order_by(AppPermission.code.asc())
    ).scalars()
    return list(rows)


def authenticate_user(db: Session, username: str, password: str) -> tuple[UserAccount, list[str], datetime]:
    user = db.scalar(select(UserAccount).where(UserAccount.username == username))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    permissions = get_user_permissions(db, user)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=get_settings().auth_token_ttl_hours)
    return user, permissions, expires_at


def create_access_token(user: UserAccount, permissions: list[str], expires_at: datetime) -> str:
    payload = {
        "sub": user.id,
        "username": user.username,
        "permissions": permissions,
        "exp": expires_at.isoformat(),
    }
    return _sign_token(payload)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> UserAccount:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    payload = _verify_token(credentials.credentials)
    user = db.get(UserAccount, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not active")
    return user


def get_current_user_with_permissions(
    current_user: UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> tuple[UserAccount, list[str]]:
    return current_user, get_user_permissions(db, current_user)


def require_permissions(*required_permissions: str) -> Callable:
    def dependency(
        current: tuple[UserAccount, list[str]] = Depends(get_current_user_with_permissions),
    ) -> UserAccount:
        user, permissions = current
        if required_permissions and not all(permission in permissions for permission in required_permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return user

    return dependency
