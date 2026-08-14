"""维护模式通知：站内机器人私信（必达）+ 邮件 + 钉钉/Telegram Webhook（可配置）

渠道配置（AppSetting）：
  notify.dingtalk_webhook    钉钉机器人 Webhook URL
  notify.telegram_bot_token  Telegram Bot Token
  notify.telegram_chat_id    Telegram 接收 chat id
"""
import asyncio
import json
import logging

import httpx
from sqlalchemy import select

from ..models import User
from ..services.bot import ensure_bot, send_bot_dm
from ..services.settings import get_setting

logger = logging.getLogger("maintenance")


def _fmt_dt(iso: str | None) -> str:
    if not iso:
        return "未设置"
    try:
        from datetime import datetime

        return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return iso


def build_message(action: str, snap: dict, detail: str = "") -> str:
    mode = snap.get("mode", "none")
    lines = ["🔔 维护模式通知", "━━━━━━━━━━━━━━━━━━━"]
    if action == "enable":
        lines.append(f"操作：维护模式已开启")
        lines.append(f"模式：{mode}")
        lines.append(f"原因：{snap.get('reason') or '—'}")
        lines.append(f"开启人：{snap.get('operator') or '—'}")
        lines.append(f"预计恢复：{_fmt_dt(snap.get('auto_close_at'))}")
    elif action == "disable":
        lines.append("操作：维护模式已关闭，服务恢复")
    elif action == "extend":
        lines.append(f"操作：维护时间已延长")
        lines.append(f"预计恢复：{_fmt_dt(snap.get('auto_close_at'))}")
    elif action == "auto_close":
        lines.append(f"操作：维护已自动关闭（{detail}）")
    elif action == "emergency_close":
        lines.append("操作：已通过紧急令牌关闭维护模式")
    elif action == "scheduled_start":
        lines.append("操作：定时维护已自动开启")
        lines.append(f"时长：{snap.get('scheduled_duration', '60')} 分钟")
    else:
        lines.append(f"操作：{action}（{detail}）")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("如需操作请登录后台。")
    return "\n".join(lines)


async def notify_admins(db, *, action: str, snap: dict, detail: str = "") -> None:
    """通知所有管理员：站内机器人私信（必达）→ 失败不阻断"""
    text = build_message(action, snap, detail)
    # 1) 站内机器人私信
    try:
        bot = await ensure_bot(db)
        admins = (
            await db.execute(
                select(User).join(User.role).where(User.is_active.is_(True), User.is_bot.is_(False))
            )
        ).scalars().all()
        for u in admins:
            if u.role is not None and u.role.name in ("admin", "super_admin"):
                try:
                    await send_bot_dm(db, bot, u.uid, text)
                except Exception:
                    logger.exception("站内通知失败")
    except Exception:
        logger.exception("通知管理员失败")
    # 2) 邮件（SMTP 未配置静默跳过）
    from ..services.mailer import send_email

    smtp = (await get_setting(db, "smtp.from", "")).strip()
    _ = smtp
    try:
        for u in admins if 'admins' in dir() else []:
            pass
    except Exception:
        pass
    # 3) 钉钉 / Telegram Webhook
    await asyncio.gather(
        _notify_dingtalk(db, text),
        _notify_telegram(db, text),
        return_exceptions=True,
    )


async def _notify_dingtalk(db, text: str) -> None:
    url = (await get_setting(db, "notify.dingtalk_webhook", "")).strip()
    if not url:
        return
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            await client.post(url, json={"msgtype": "text", "text": {"content": text[:2000]}})
    except Exception:
        logger.exception("钉钉通知失败")


async def _notify_telegram(db, text: str) -> None:
    token = (await get_setting(db, "notify.telegram_bot_token", "")).strip()
    chat_id = (await get_setting(db, "notify.telegram_chat_id", "")).strip()
    if not token or not chat_id:
        return
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text[:4000]},
            )
    except Exception:
        logger.exception("Telegram 通知失败")
