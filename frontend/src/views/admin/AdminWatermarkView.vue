<template>
  <div>
    <header class="page-head">
      <div>
        <h1>水印取证</h1>
        <p class="sub">粘贴从私信页「复制」按钮复制的消息文本，解码零宽溯源水印（superadmin 专属）</p>
      </div>
    </header>

    <section class="panel" style="max-width: 760px">
      <div class="panel-title">文本解码</div>
      <p class="muted" style="margin:0 0 10px">
        消息页每条消息的复制按钮会在文本尾部附加零宽字符水印（发送者 UID + 消息 ID + 时间戳 + CRC）。
        将复制内容粘贴到下方即可定位发送者。每次解码计入审计，接口限流 30 次/小时。
      </p>
      <textarea
        v-model="text"
        rows="7"
        class="wm-input"
        placeholder="在此粘贴复制的消息文本…"
      ></textarea>
      <div class="actions" style="margin-top:10px">
        <button class="btn primary" :disabled="!text.trim() || loading" @click="decode">
          {{ loading ? '解码中…' : '解码' }}
        </button>
        <button class="btn" @click="clear">清空</button>
      </div>

      <div v-if="error" class="wm-error">{{ error }}</div>

      <div v-if="result" class="wm-result">
        <template v-if="result.matched">
          <div class="wm-hit">✅ 水印命中：已定位发送者</div>
          <div class="wm-grid">
            <div class="wm-cell">
              <span>昵称</span>
              <b>{{ result.user?.nickname || result.user?.username || '—' }}</b>
            </div>
            <div class="wm-cell">
              <span>用户名</span>
              <b>@{{ result.user?.username }}</b>
            </div>
            <div class="wm-cell">
              <span>UID</span>
              <b class="mono">{{ result.user?.uid }}</b>
            </div>
            <div class="wm-cell">
              <span>消息 ID</span>
              <b class="mono">{{ result.message_id }}</b>
            </div>
            <div class="wm-cell">
              <span>水印时间戳</span>
              <b>{{ fmtTs(result.ts) }}</b>
            </div>
          </div>
          <button class="btn ghost sm" @click="copyUid">复制 UID</button>
        </template>
        <div v-else class="wm-miss">
          未识别到有效水印。<br />
          <span class="muted">可能原因：文本非来自消息「复制」按钮、零宽字符已被清理、或消息渲染被截断。</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../../api/client'

const text = ref('')
const loading = ref(false)
const result = ref(null)
const error = ref('')

async function decode() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const { data } = await api.post('/im/decode-text', { text: text.value })
    result.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '解码失败'
  } finally {
    loading.value = false
  }
}

function clear() {
  text.value = ''
  result.value = null
  error.value = ''
}

function fmtTs(ts) {
  if (!ts) return '—'
  const d = new Date(ts * 1000)
  const pad = (x) => String(x).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

async function copyUid() {
  try {
    await navigator.clipboard.writeText(result.value.user.uid)
    alert('UID 已复制')
  } catch {
    /* ignore */
  }
}
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.wm-input {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  border: 1px solid var(--admin-border);
  border-radius: 9px;
  font-size: 13.5px;
  background: var(--admin-card);
  color: var(--admin-text);
  font-family: inherit;
  resize: vertical;
  line-height: 1.6;
}

.wm-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.wm-error {
  margin-top: 10px;
  color: #e5484d;
  font-size: 13px;
}

.wm-result {
  margin-top: 16px;
  border-top: 1px solid var(--admin-border);
  padding-top: 14px;
}

.wm-hit {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}

.wm-miss {
  font-size: 13.5px;
  color: var(--admin-text-muted);
  line-height: 1.7;
}

.wm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.wm-cell {
  background: var(--admin-card);
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  padding: 8px 12px;
}

.wm-cell span {
  display: block;
  font-size: 11px;
  color: var(--admin-text-muted);
  margin-bottom: 3px;
}

.wm-cell b {
  font-size: 13px;
  word-break: break-all;
}

.mono {
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 12px;
}
</style>
