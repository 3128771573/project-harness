"""全局异常处理：把 Pydantic 校验错误转成友好中文消息"""
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# 字段 → 友好名称映射
_FIELD_NAMES = {
    "username": "用户名",
    "email": "邮箱",
    "password": "密码",
    "code": "验证码",
    "token": "验证码",
    "new_password": "新密码",
    "old_password": "旧密码",
    "question": "问题内容",
    "refresh_token": "刷新凭证",
    "nickname": "昵称",
    "bio": "简介",
}

# 错误类型 → 友好提示模板
_MESSAGE_MAP = {
    "string_pattern_mismatch": "{field}格式不正确",
    "string_too_short": "{field}长度不足（最少 {min} 位）",
    "string_too_long": "{field}长度超出限制（最多 {max} 位）",
    "value_error": "{field}格式不正确",
    "missing": "缺少必填字段：{field}",
    "string_type": "{field}类型错误",
    "int_type": "{field}必须为数字",
    "bool_type": "{field}必须为布尔值",
    "greater_than_equal": "{field}数值过小",
    "less_than_equal": "{field}数值过大",
    "email": "邮箱格式不正确",
    "url_parsing": "链接格式不正确",
}


def _friendly_message(detail: dict) -> str:
    loc = detail.get("loc", [])
    # loc 形如 ['body', 'username'] 或 ['query', 'page']
    field_raw = loc[-1] if loc else "参数"
    field = _FIELD_NAMES.get(str(field_raw), str(field_raw))
    err_type = detail.get("type", "")
    ctx = detail.get("ctx", {})

    if err_type == "email":
        return "邮箱格式不正确"

    template = _MESSAGE_MAP.get(err_type)
    if template:
        msg = template.format(
            field=field,
            min=ctx.get("min_length", ""),
            max=ctx.get("max_length", ""),
            gt=ctx.get("gt", ""),
            le=ctx.get("le", ""),
        )
        # 清理空白占位
        import re

        msg = re.sub(r"\s+（[^）]*）(?=\s|$)", "", msg) if False else msg
        return msg

    return f"{field}格式不正确"


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    if errors:
        # 取第一条错误（优先展示最关键的）
        first = errors[0]
        message = _friendly_message(first)
        # 收集全部错误用于调试
        details = [_friendly_message(e) for e in errors[:5]]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": message, "errors": details},
        )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": "请求参数错误"})
