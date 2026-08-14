// 零宽字符文本水印（与后端 app/services/watermark.py 完全同构）
const ZW = ['\u200b', '\u200c', '\u200d', '\ufeff']
const ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyz'

// CRC32（zlib 标准多项式）→ 低 16 位 hex，与 Python zlib.crc32 & 0xFFFF 一致
function crc16(data) {
  let crc = 0xffffffff
  for (let i = 0; i < data.length; i++) {
    crc ^= data[i]
    for (let k = 0; k < 8; k++) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1))
    }
  }
  return ((crc ^ 0xffffffff) >>> 0 & 0xffff).toString(16).padStart(4, '0')
}

function strToB36(s) {
  const bytes = new TextEncoder().encode(s)
  let n = 0n
  for (const b of bytes) n = (n << 8n) | BigInt(b)
  if (n === 0n) return '0'
  let out = ''
  while (n > 0n) {
    out = ALPHABET[Number(n % 36n)] + out
    n = n / 36n
  }
  return out
}

function b36ToBytes(s) {
  let n = 0n
  for (const ch of s) n = n * 36n + BigInt(ALPHABET.indexOf(ch))
  if (n === 0n) return new Uint8Array(1)
  let hex = n.toString(16)
  if (hex.length % 2) hex = '0' + hex
  const bytes = new Uint8Array(hex.length / 2)
  for (let i = 0; i < hex.length; i += 2) bytes[i / 2] = parseInt(hex.slice(i, i + 2), 16)
  return bytes
}

export function encodeTextWatermark(uid, messageId, ts) {
  const base = uid + ':' + messageId + ':' + ts
  const crc = crc16(new TextEncoder().encode(base))
  const payload = base + ':' + crc
  const b36 = strToB36(payload)
  let out = ''
  for (const ch of b36) {
    const v = parseInt(ch, 36)
    out += ZW[(v >> 4) & 3] + ZW[(v >> 2) & 3] + ZW[v & 3]
  }
  return out
}

const ZW_RE = /[\u200b\u200c\u200d\ufeff]+/g

export function decodeTextWatermark(text) {
  const runs = text.match(ZW_RE) || []
  for (let i = runs.length - 1; i >= 0; i--) {
    const run = runs[i]
    if (run.length < 12 || run.length % 3 !== 0) continue
    let digits = ''
    let ok = true
    for (let j = 0; j < run.length; j += 3) {
      const a = ZW.indexOf(run[j])
      const b = ZW.indexOf(run[j + 1])
      const c = ZW.indexOf(run[j + 2])
      if (a < 0 || b < 0 || c < 0) { ok = false; break }
      digits += ALPHABET[((a & 3) << 4) | ((b & 3) << 2) | (c & 3)]
    }
    if (!ok) continue
    try {
      const raw = new TextDecoder().decode(b36ToBytes(digits))
      const parts = raw.split(':')
      if (parts.length !== 4) continue
      const uid = parts[0]; const mid = parts[1]; const ts = parts[2]; const crc = parts[3]
      if (crc16(new TextEncoder().encode(uid + ':' + mid + ':' + ts)) !== crc.toLowerCase()) continue
      if (uid.length < 8 || mid.length < 8 || !/^\d+$/.test(ts)) continue
      return { uid, messageId: mid, ts: Number(ts) }
    } catch { /* continue */ }
  }
  return null
}
