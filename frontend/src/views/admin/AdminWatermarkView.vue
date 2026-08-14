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

    <section class="panel" style="max-width: 760px; margin-top: 16px">
      <div class="panel-title">取证授权管理</div>
      <p class="muted" style="margin:0 0 10px">
        可授予任意用户水印取证权限（一次性 / 按次 / 长期）。未授权用户调用一律 403；仅成功识别消耗额度，失败不扣。
      </p>
      <form @submit.prevent="grantUser" class="grant-form">
        <div class="grant-search">
          <input v-model="grantQ" placeholder="搜索要授权的用户…" @input="onGrantSearch" />
          <div v-if="grantResults.length" class="grant-results">
            <div v-for="u in grantResults" :key="u.uid" class="grant-item" @mousedown.prevent="pickGrantUser(u)">
              <span>{{ u.nickname || u.username }}</span>
              <span class="muted">@{{ u.username }}</span>
            </div>
          </div>
        </div>
        <select v-model="grantType">
          <option value="one_time">一次性</option>
          <option value="times">按次</option>
          <option value="permanent">长期（不限次）</option>
        </select>
        <input v-if="grantType === 'times'" v-model.number="grantUses" type="number" min="1" max="10000" placeholder="次数" />
        <input v-model="grantExpires" type="datetime-local" placeholder="过期时间（可选）" />
        <button class="btn primary" type="submit" :disabled="!grantTarget || granting">{{ granting ? '授权中…' : '授予' }}</button>
      </form>

      <div class="grant-list">
        <div v-if="grants.length === 0" class="muted" style="padding: 10px 0">暂无授权记录</div>
        <div v-for="g in grants" :key="g.id" class="grant-row">
          <img v-if="g.user.avatar" :src="g.user.avatar" class="gr-avatar" alt="" />
          <span v-else class="gr-avatar">{{ (g.user.nickname || g.user.username)[0] }}</span>
          <div class="gr-info">
            <b>{{ g.user.nickname || g.user.username }} <span class="muted">@{{ g.user.username }}</span></b>
            <span class="muted">
              {{ quotaLabel(g) }} · 已用 {{ g.used_count }}{{ g.quota_type === 'times' ? '/' + g.max_uses : '' }}
              <template v-if="g.expires_at"> · 过期 {{ formatTime(g.expires_at) }}</template>
              · {{ formatTime(g.created_time) }} 授予
            </span>
          </div>
          <span :class="['status-badge', g.revoked ? 'disabled' : 'active']">{{ g.revoked ? '已吊销' : '有效' }}</span>
          <button v-if="!g.revoked" class="action-btn danger" @click="revokeGrant(g)">吊销</button>
        </div>
      </div>
    </section>

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

// ===== 授权管理 =====
import { onMounted } from 'vue'

const grants = ref([])
const grantQ = ref('')
const grantResults = ref([])
const grantTarget = ref(null)
const grantType = ref('one_time')
const grantUses = ref(10)
const grantExpires = ref('')
const granting = ref(false)
let grantTimer = null

function onGrantSearch() {
  clearTimeout(grantTimer)
  const q = grantQ.value.trim()
  if (!q) {
    grantResults.value = []
    return
  }
  grantTimer = setTimeout(async () => {
    try {
      const { data } = await api.get('/im/users?q=' + encodeURIComponent(q))
      grantResults.value = data.items || []
    } catch {
      grantResults.value = []
    }
  }, 300)
}

function pickGrantUser(u) {
  grantTarget.value = u
  grantQ.value = u.nickname || u.username
  grantResults.value = []
}

async function grantUser() {
  if (!grantTarget.value) return
  granting.value = true
  try {
    const payload = {
      user_id: grantTarget.value.uid,
      quota_type: grantType.value,
    }
    if (grantType.value === 'times') payload.max_uses = grantUses.value || 1
    if (grantExpires.value) payload.expires_at = new Date(grantExpires.value).toISOString()
    const { data } = await api.post('/admin/im/watermark/grants', payload)
    grants.value = [data].concat(grants.value)
    grantTarget.value = null
    grantQ.value = ''
    grantExpires.value = ''
    alert('已授予 ' + (data.user.nickname || data.user.username))
  } catch (e) {
    alert(e.response?.data?.detail || '授权失败')
  } finally {
    granting.value = false
  }
}

async function revokeGrant(g) {
  if (!confirm('吊销 ' + (g.user.nickname || g.user.username) + ' 的取证授权？')) return
  try {
    await api.post('/admin/im/watermark/grants/' + g.id + '/revoke')
    g.revoked = true
    alert('已吊销')
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

function quotaLabel(g) {
  if (g.quota_type === 'one_time') return '一次性'
  if (g.quota_type === 'times') return '按次（' + g.max_uses + ' 次）'
  return '长期不限次'
}

function formatTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (x) => String(x).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
}

async function loadGrants() {
  try {
    const { data } = await api.get('/admin/im/watermark/grants')
    grants.value = data || []
  } catch {
    /* ignore */
  }
}

onMounted(loadGrants)
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

.grant-form {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: flex-start;
}

.grant-search {
  position: relative;
  flex: 1;
  min-width: 200px;
}

.grant-search input,
.grant-form select,
.grant-form > input {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 12px;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  font-size: 13px;
  background: var(--admin-card);
  color: var(--admin-text);
}

.grant-form select,
.grant-form > input {
  width: auto;
}

.grant-results {
  position: absolute;
  top: 40px;
  left: 0;
  right: 0;
  background: var(--admin-card);
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  z-index: 60;
  overflow: hidden;
}

.grant-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  font-size: 13px;
  cursor: pointer;
}

.grant-item:hover {
  background: var(--admin-bg);
}

.grant-list {
  margin-top: 14px;
  border-top: 1px solid var(--admin-border);
  padding-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.grant-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.gr-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #2563eb;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 13px;
  object-fit: cover;
  flex: none;
}

.gr-info {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
