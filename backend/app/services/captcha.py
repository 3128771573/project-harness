"""图形验证码：Pillow 生成 PNG + 内存单次存储（有效期可配置，验证后立即失效）"""
import io
import secrets
import threading
import time

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# 排除易混淆字符 0/O/I/L
_CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_CODE_LEN = 4

_store: dict[str, tuple[float, str]] = {}  # captcha_id -> (expire_ts, code)
_lock = threading.Lock()


def _rand(a: int, b: int) -> int:
    """[a, b) 区间随机整数（secrets 无 randrange，用 randbelow 实现）"""
    return a + secrets.randbelow(b - a)


def _generate_code() -> str:
    return "".join(secrets.choice(_CHARSET) for _ in range(_CODE_LEN))


def create_captcha(ttl: int = 120) -> tuple[str, bytes]:
    """生成验证码：返回 (captcha_id, png_bytes)"""
    code = _generate_code()
    captcha_id = secrets.token_urlsafe(16)
    now = time.time()
    with _lock:
        _store[captcha_id] = (now + ttl, code)
        # 顺手清理过期条目，防止无限增长
        expired = [k for k, v in _store.items() if v[0] < now]
        for k in expired:
            _store.pop(k, None)
    return captcha_id, _render_png(code)


def verify_captcha(captcha_id: str | None, code: str | None) -> bool:
    """验证并立即失效（无论成功失败，防重用）"""
    if not captcha_id or not code:
        return False
    with _lock:
        entry = _store.pop(captcha_id, None)
    if entry is None:
        return False
    expire_ts, expected = entry
    if time.time() > expire_ts:
        return False
    return code.strip().upper() == expected


def _render_png(code: str) -> bytes:
    W, H = 130, 44
    bg = (_rand(205, 248), _rand(205, 248), _rand(205, 248))
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    # 干扰线
    for _ in range(4):
        x1 = _rand(0, W)
        y1 = _rand(0, H)
        x2 = _rand(0, W)
        y2 = _rand(0, H)
        draw.line(
            [(x1, y1), (x2, y2)],
            fill=(_rand(80, 200), _rand(80, 200), _rand(80, 200)),
            width=1,
        )

    # 噪点
    for _ in range(70):
        draw.point(
            (_rand(0, W), _rand(0, H)),
            fill=(_rand(0, 256), _rand(0, 256), _rand(0, 256)),
        )

    # 字符：随机旋转 + 上下偏移（Pillow 10.1+ 内置可缩放字体，无需系统字体）
    font = ImageFont.load_default(size=30)
    char_w = W // _CODE_LEN
    for i, ch in enumerate(code):
        char_img = Image.new("RGBA", (34, 42), (0, 0, 0, 0))
        cd = ImageDraw.Draw(char_img)
        color = (_rand(25, 150), _rand(25, 150), _rand(25, 150))
        cd.text((2, 3), ch, font=font, fill=color)
        angle = _rand(-28, 28)
        char_img = char_img.rotate(angle, expand=True, resample=Image.BICUBIC)
        y_off = _rand(-4, 5)
        img.paste(char_img, (i * char_w + 6, 2 + y_off), char_img)

    # 轻微模糊，适度增加机器识别难度
    img = img.filter(ImageFilter.GaussianBlur(radius=0.4))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
