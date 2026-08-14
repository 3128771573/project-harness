"""零宽字符文本水印：编码 / 解码（P0 文本溯源取证）

方案（前端/后端同构）：
- 载荷：uid:message_id:unix_ts:crc16hex
- base36 编码字节 → 每个 base36 字符（0-35，6bit）拆成 3 个 2bit，
  映射到零宽字符表 [U+200B, U+200C, U+200D, U+FEFF]
- 解码：扫描文本中连续零宽字符段（>= 12），从后往前尝试解码 + CRC 校验，
  取最后一个有效载荷（最新附加的水印）
"""
import re
import zlib

ZW_CHARS = ["\u200b", "\u200c", "\u200d", "\ufeff"]
_ZW_SET = frozenset(ZW_CHARS)
_ZW_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]+")
_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def _crc16(data: bytes) -> str:
    return format(zlib.crc32(data) & 0xFFFF, "04x")


def _bytes_to_b36(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    if n == 0:
        return "0"
    out = []
    while n:
        n, r = divmod(n, 36)
        out.append(_ALPHABET[r])
    return "".join(reversed(out))


def _b36_to_bytes(s: str) -> bytes:
    n = 0
    for ch in s:
        n = n * 36 + _ALPHABET.index(ch)
    if n == 0:
        return b"\x00"
    # 按实际位长还原字节数（原始载荷无前导零字节，勿按位数上限补零）
    return n.to_bytes((n.bit_length() + 7) // 8, "big")


def encode_text_watermark(uid: str, message_id: str, ts: int) -> str:
    """生成追加到消息文本末尾的零宽字符水印串"""
    payload = f"{uid}:{message_id}:{ts}:{_crc16(f'{uid}:{message_id}:{ts}'.encode())}"
    b36 = _bytes_to_b36(payload.encode("utf-8"))
    parts = []
    for ch in b36:
        v = int(ch, 36)
        parts.append(ZW_CHARS[(v >> 4) & 3])
        parts.append(ZW_CHARS[(v >> 2) & 3])
        parts.append(ZW_CHARS[v & 3])
    return "".join(parts)


def _decode_run(run: str):
    """解码一段零宽字符；失败返回 None"""
    if len(run) < 12 or len(run) % 3 != 0:
        return None
    digits = []
    for i in range(0, len(run), 3):
        a = ZW_CHARS.index(run[i]) if run[i] in _ZW_SET else -1
        b = ZW_CHARS.index(run[i + 1]) if run[i + 1] in _ZW_SET else -1
        c = ZW_CHARS.index(run[i + 2]) if run[i + 2] in _ZW_SET else -1
        if a < 0 or b < 0 or c < 0:
            return None
        digits.append(_ALPHABET[((a & 3) << 4) | ((b & 3) << 2) | (c & 3)])
    try:
        raw = _b36_to_bytes("".join(digits)).decode("utf-8")
    except Exception:
        return None
    parts = raw.split(":")
    if len(parts) != 4:
        return None
    uid, mid, ts, crc = parts
    if _crc16(f"{uid}:{mid}:{ts}".encode()) != crc.lower():
        return None
    if len(uid) < 8 or len(mid) < 8 or not ts.isdigit():
        return None
    return {"uid": uid, "message_id": mid, "ts": int(ts)}


def decode_text_watermark(text: str):
    """从（可能混有正文的）文本中提取最后一个有效水印；未命中返回 None"""
    runs = _ZW_RE.findall(text)
    for run in reversed(runs):
        if len(run) < 12:
            continue
        decoded = _decode_run(run)
        if decoded:
            return decoded
    return None
