"""邮箱验证码服务：生成、发送、校验、限流"""
import asyncio
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import EmailCode
from .mailer import build_code_email, send_email

PURPOSES = ("register", "login", "reset")


def generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"


async def send_verification_code(db: AsyncSession, email: str, purpose: str) -> dict:
    """发送验证码，返回 {sent: bool, message: str, cooldown: int}"""
    email = email.lower().strip()
    if purpose not in PURPOSES:
        raise ValueError("无效的验证码用途")

    now = datetime.now(timezone.utc)

    # 重发冷却检查
    recent = await db.execute(
        select(EmailCode)
        .where(EmailCode.email == email, EmailCode.purpose == purpose)
        .order_by(EmailCode.created_time.desc())
        .limit(1)
    )
    last = recent.scalar_one_or_none()
    if last is not None:
        elapsed = (now - last.created_time).total_seconds()
        if elapsed < settings.EMAIL_CODE_RESEND_SECONDS:
            wait = int(settings.EMAIL_CODE_RESEND_SECONDS - elapsed)
            return {"sent": False, "message": f"发送太频繁，请 {wait} 秒后重试", "cooldown": wait}

    # 生成新码并入库
    code = generate_code()
    expires_at = now + timedelta(minutes=settings.EMAIL_CODE_EXPIRE_MINUTES)
    db.add(EmailCode(email=email, code=code, purpose=purpose, expires_at=expires_at))
    await db.commit()

    # 发送邮件（同步 smtplib 放线程池，避免阻塞事件循环）
    sent = await asyncio.to_thread(send_email, email, f"【Harness】您的验证码：{code}", build_code_email(code, purpose))
    return {
        "sent": sent,
        "message": "验证码已发送到邮箱" if sent else "验证码已生成（邮件服务未配置，开发模式）",
        "cooldown": settings.EMAIL_CODE_RESEND_SECONDS,
        "dev_code": code if not settings.smtp_enabled else None,
    }


async def verify_code(db: AsyncSession, email: str, code: str, purpose: str) -> bool:
    """校验验证码（一次性 + 过期 + 尝试次数限制），成功则标记 used"""
    email = email.lower().strip()
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(EmailCode)
        .where(EmailCode.email == email, EmailCode.purpose == purpose, EmailCode.used.is_(False))
        .order_by(EmailCode.created_time.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if record is None:
        return False

    # 尝试次数限制（防爆破）
    if record.attempts >= settings.EMAIL_CODE_MAX_ATTEMPTS:
        return False
    if record.expires_at < now:
        return False
    if record.code != code:
        record.attempts += 1
        await db.commit()
        return False

    record.used = True
    await db.commit()
    return True


async def invalidate_codes(db: AsyncSession, email: str, purpose: str):
    """使该邮箱某用途的全部验证码失效"""
    email = email.lower().strip()
    result = await db.execute(
        select(EmailCode).where(EmailCode.email == email, EmailCode.purpose == purpose, EmailCode.used.is_(False))
    )
    for c in result.scalars().all():
        c.used = True
    await db.commit()
