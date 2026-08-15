"""HTTP 工具：可信客户端 IP 提取

部署在 nginx 之后：必须依赖 nginx 注入的 X-Real-IP（丢弃客户端可控的 X-Forwarded-For）
"""
from fastapi import Request


def client_ip(request: Request) -> str | None:
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return request.client.host if request.client else None
