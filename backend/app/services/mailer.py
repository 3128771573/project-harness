"""邮件发送服务（SMTP）"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import settings


def send_email(to: str, subject: str, html: str) -> bool:
    """通过 SMTP 发送 HTML 邮件，成功返回 True"""
    if not settings.smtp_enabled:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15, context=context) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], [to], msg.as_string())
        return True
    except Exception:
        return False


def build_code_email(code: str, purpose: str, site_name: str = "Harness Platform") -> str:
    """生成验证码邮件 HTML"""
    purpose_text = {
        "register": "注册账号",
        "login": "登录平台",
        "reset": "重置密码",
    }.get(purpose, "验证")
    return f"""
    <div style="max-width:480px;margin:0 auto;font-family:-apple-system,'PingFang SC',sans-serif;background:#f8fafc;padding:32px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <div style="width:44px;height:44px;margin:0 auto 12px;border-radius:12px;background:linear-gradient(135deg,#6366F1,#8B5CF6);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:20px;">H</div>
        <div style="font-size:18px;font-weight:700;color:#0f172a;">{site_name}</div>
      </div>
      <div style="background:#fff;border-radius:12px;padding:28px;text-align:center;border:1px solid #e2e8f0;">
        <div style="font-size:14px;color:#475569;margin-bottom:8px;">您的{purpose_text}验证码</div>
        <div style="font-size:36px;font-weight:800;letter-spacing:8px;color:#6366F1;margin:16px 0;">{code}</div>
        <div style="font-size:12px;color:#94a3b8;">验证码 5 分钟内有效，请勿泄露给他人</div>
      </div>
      <div style="text-align:center;font-size:11px;color:#94a3b8;margin-top:20px;">此邮件由系统自动发送，请勿直接回复</div>
    </div>
    """
