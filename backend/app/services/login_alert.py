"""登录异常告警：新设备/新地点登录检测 + 邮件通知（SMTP 未配置时自动跳过）"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import LoginLog
from .geo import resolve_location
from .mailer import send_email

_TASKS: set[asyncio.Task] = set()
_LOOKBACK_DAYS = 30


def device_base(device: str | None) -> str:
    """设备类型基座：取「桌面端 · Windows · Edge 126」的第一段"""
    return (device or "").split("·")[0].strip()


async def is_known_login(
    db: AsyncSession, uid: str, ip: str | None, device: str | None, before: datetime | None = None
) -> bool:
    """该 IP 或设备类型在回看窗口内是否有成功登录（before 用于逐条判定历史记录）"""
    since = (before or datetime.now(timezone.utc)) - timedelta(days=_LOOKBACK_DAYS)
    stmt = select(LoginLog.id).where(
        LoginLog.uid == uid,
        LoginLog.success.is_(True),
        LoginLog.created_time >= since,
    )
    if before is not None:
        stmt = stmt.where(LoginLog.created_time < before)
    conds = []
    if ip:
        conds.append(LoginLog.ip == ip)
    base = device_base(device)
    if base:
        conds.append(LoginLog.device.like(base + "%"))
    if not conds:
        return True  # 无可比信息，视为已知，避免误报
    stmt = stmt.where(or_(*conds))
    row = await db.execute(stmt.limit(1))
    return row.scalar_one_or_none() is not None


def _build_alert_html(email: str, ip: str | None, location: str, device: str | None, ua: str | None) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""
    <div style="max-width:480px;margin:0 auto;font-family:-apple-system,'PingFang SC',sans-serif;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <div style="width:44px;height:44px;margin:0 auto 12px;border-radius:12px;background:linear-gradient(135deg,#6366F1,#8B5CF6);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:20px;">H</div>
        <div style="font-size:18px;font-weight:700;color:#0f172a;">安全提醒</div>
      </div>
      <div style="background:#fff;border-radius:12px;padding:28px;border:1px solid #e2e8f0;">
        <div style="font-size:15px;color:#0f172a;font-weight:700;margin-bottom:12px;">⚠️ 检测到新设备登录您的账号</div>
        <table style="width:100%;font-size:13px;color:#475569;line-height:2;">
          <tr><td style="color:#94a3b8;width:72px;">账号</td><td>{email}</td></tr>
          <tr><td style="color:#94a3b8;">时间</td><td>{now}</td></tr>
          <tr><td style="color:#94a3b8;">IP</td><td>{ip or '未知'}</td></tr>
          <tr><td style="color:#94a3b8;">属地</td><td>{location or '未知'}</td></tr>
          <tr><td style="color:#94a3b8;">设备</td><td>{device or '未知'}</td></tr>
        </table>
        <div style="margin-top:16px;padding:12px 14px;background:#fef2f2;border-radius:8px;font-size:12.5px;color:#b91c1c;">
          如果这不是您本人操作，请立即登录修改密码，并在「安全设置」中检查登录设备与登录记录。
        </div>
      </div>
      <div style="text-align:center;font-size:11px;color:#94a3b8;margin-top:20px;">此邮件由系统自动发送，请勿直接回复</div>
    </div>
    """


def schedule_login_alert(uid: str, email: str, ip: str | None, ua: str | None, device: str | None):
    """后台任务：等待属地解析后发送新设备登录告警邮件（SMTP 未配置则跳过）"""

    async def _run():
        await asyncio.sleep(2)  # 等属地补充任务完成
        location = await resolve_location(ip)
        if not settings.smtp_enabled:
            return
        html = _build_alert_html(email, ip, location, device, ua)
        send_email(email, "【Harness 安全提醒】检测到新设备登录", html)

    task = asyncio.create_task(_run())
    _TASKS.add(task)
    task.add_done_callback(_TASKS.discard)
