import uuid
import hashlib
import re
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def validate_password_policy(password: str) -> str | None:
    """密码策略校验，返回错误信息或 None"""
    if len(password) < 8:
        return "密码至少 8 位"
    if len(password) > 128:
        return "密码过长"
    checks = 0
    if re.search(r"[a-z]", password):
        checks += 1
    if re.search(r"[A-Z]", password):
        checks += 1
    if re.search(r"\d", password):
        checks += 1
    if re.search(r"[^a-zA-Z0-9]", password):
        checks += 1
    if checks < 3:
        return "密码需包含大小写字母、数字、特殊字符中的至少 3 类"
    return None


def _encode(payload: dict, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {**payload, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(uid: str) -> str:
    return _encode(
        {"sub": uid, "type": "access"},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(uid: str) -> tuple[str, str, datetime]:
    """返回 (token, jti, expires_at)"""
    jti = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token = _encode({"sub": uid, "type": "refresh", "jti": jti}, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    return token, jti, expires_at


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


# 角色常量
ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_SUPER_ADMIN = "super_admin"


def generate_reset_token() -> tuple[str, str]:
    """生成密码重置令牌，返回 (明文 token, sha256 hash)"""
    token = uuid.uuid4().hex + uuid.uuid4().hex
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
