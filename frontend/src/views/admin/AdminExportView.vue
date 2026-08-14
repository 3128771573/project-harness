<template>
  <div>
    <header class="page-head">
      <div>
        <h1>日志导出</h1>
        <p class="sub">企业级审计导出 · 六类数据源 · CSV(UTF-8 BOM)/JSON · SHA-256 完整性校验 · 导出行为全程审计（superadmin 专属）</p>
      </div>
    </header>

    <section class="panel" style="max-width: 860px">
      <div class="panel-title">导出配置</div>
      <div class="form-grid">
        <label class="field">
          <span>数据源</span>
          <select v-model="form.source">
            <option value="audit">操作审计（audit_logs）</option>
            <option value="login">登录日志（login_logs）</option>
            <option value="visit">访问记录（visit_logs）</option>
            <option value="watermark">水印取证（watermark_logs）</option>
            <option value="report">举报记录（reports）</option>
            <option value="bot">机器人消息（dm_messages）</option>
          </select>
        </label>
        <label class="field">
          <span>格式</span>
          <select v-model="form.format">
            <option value="csv">CSV（Excel 兼容，UTF-8 BOM）</option>
            <option value="json">JSON（结构化完整字段）</option>
          </select>
        </label>
        <label class="field">
          <span>开始时间（UTC）</span>
          <input v-model="form.start" type="datetime-local" required />
        </label>
        <label class="field">
          <span>结束时间（UTC）</span>
          <input v-model="form.end" type="datetime-local" required />
        </label>

        <template v-if="form.source === 'audit'">
          <label class="field"><span>动作（action 模糊）</span><input v-model="form.action" placeholder="如 user.delete / bot.broadcast" /></label>
          <label class="field"><span>操作者（用户名模糊）</span><input v-model="form.actor" /></label>
          <label class="field"><span>关键词（详情/资源/动作）</span><input v-model="form.keyword" /></label>
          <label class="field"><span>结果</span>
            <select v-model="form.success"><option :value="null">全部</option><option :value="true">成功</option><option :value="false">失败</option></select>
          </label>
        </template>
        <template v-else-if="form.source === 'login'">
          <label class="field"><span>邮箱（模糊）</span><input v-model="form.email" /></label>
          <label class="field"><span>登录方式</span>
            <select v-model="form.method"><option value="">全部</option><option value="password">密码</option><option value="code">邮箱验证码</option><option value="sso">SSO</option><option value="register">注册</option><option value="reset">密码重置</option></select>
          </label>
          <label class="field"><span>结果</span>
            <select v-model="form.success"><option :value="null">全部</option><option :value="true">成功</option><option :value="false">失败</option></select>
          </label>
        </template>
        <template v-else-if="form.source === 'visit'">
          <label class="field"><span>路径（模糊）</span><input v-model="form.path" placeholder="如 /ai" /></label>
          <label class="field"><span>用户名</span><input v-model="form.username" /></label>
          <label class="field"><span>状态码</span><input v-model.number="form.status_code" type="number" placeholder="如 200" /></label>
        </template>
        <template v-else-if="form.source === 'watermark'">
          <label class="field"><span>操作者 UID</span><input v-model="form.actor_uid" /></label>
          <label class="field"><span>类型</span>
            <select v-model="form.kind"><option value="">全部</option><option value="text">文本</option><option value="image">截图</option></select>
          </label>
        </template>
        <template v-else-if="form.source === 'report'">
          <label class="field"><span>状态</span>
            <select v-model="form.status"><option value="">全部</option><option value="pending">待处理</option><option value="handled">已处理</option><option value="ignored">已忽略</option></select>
          </label>
          <label class="field"><span>目标类型</span>
            <select v-model="form.target_type"><option value="">全部</option><option value="dm">私信</option><option value="group">群消息</option></select>
          </label>
        </template>
        <template v-else-if="form.source === 'bot'">
          <label class="field"><span>接收者（用户名模糊）</span><input v-model="form.to" /></label>
        </template>
      </div>

      <p class="muted small" style="margin:10px 0 0">
        约束：时间范围必填且跨度 ≤ 90 天；单次导出 ≤ 100,000 行（超限请缩小范围）；每人每分钟最多 6 次导出。
      </p>

      <div class="actions" style="margin-top:14px">
        <button class="btn" :disabled="counting" @click="countRows">{{ counting ? '统计中…' : '统计行数' }}</button>
        <button class="btn primary" :disabled="exporting" @click="runExport">{{ exporting ? '导出中…' : '导出文件' }}</button>
        <span v-if="countInfo" class="count-info" :class="{ warn: countInfo.capped }">
          约 {{ countInfo.count }} 行{{ countInfo.capped ? '（已达上限，结果可能不完整，请缩小范围）' : '' }}
        </span>
      </div>

      <div v-if="exportResult" class="export-result">
        <div class="er-ok">✅ 导出完成</div>
        <div class="er-grid">
          <div><span>文件</span><b>{{ exportResult.filename }}</b></div>
          <div><span>数据源</span><b>{{ exportResult.sourceLabel }}</b></div>
          <div><span>行数</span><b>{{ exportResult.rows }}</b></div>
          <div><span>SHA-256 校验和</span><b class="mono">{{ exportResult.sha256 }}</b></div>
        </div>
        <p class="muted small">校验和已随文件返回并写入审计日志；可用 <code>sha256sum 文件名</code> 验证文件完整性。</p>
      </div>
    </section>

    <section class="panel" style="max-width: 860px; margin-top:16px">
      <div class="panel-title">最近导出记录（审计留痕）</div>
      <div v-if="history.length === 0" class="muted" style="padding:8px 0">暂无导出记录</div>
      <div v-for="h in history" :key="h.id" class="hist-row">
        <span class="muted">{{ fmtTime(h.time_utc) }}</span>
        <b>{{ h.actor_name }}</b>
        <span class="mono">{{ h.source || '—' }}</span>
        <span>{{ h.fmt === 'csv' ? 'CSV' : 'JSON' }} · {{ h.rows }} 行</span>
        <span class="mono sha">{{ h.sha256 ? h.sha256.slice(0, 16) + '…' : '' }}</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from '../../api/client'

const form = reactive({
  source: 'audit',
  format: 'csv',
  start: '',
  end: '',
  action: '', actor: '', keyword: '', success: null,
  email: '', method: '',
  path: '', username: '', status_code: null,
  actor_uid: '', kind: '',
  status: '', target_type: '', to: '',
})

function defaultRange() {
  const end = new Date()
  const start = new Date(end.getTime() - 7 * 86400000)
  const pad = (n) => String(n).padStart(2, '0')
  const fmt = (d) => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + 'T' + pad(d.getHours()) + ':' + pad(d.getMinutes())
  return { start: fmt(start), end: fmt(end) }
}

const rng = defaultRange()
form.start = rng.start
form.end = rng.end

const counting = ref(false)
const exporting = ref(false)
const countInfo = ref(null)
const exportResult = ref(null)
const history = ref([])
let lastSha = ''

function payload() {
  return {
    source: form.source,
    format: form.format,
    start: new Date(form.start).toISOString(),
    end: new Date(form.end).toISOString(),
    action: form.action || null,
    actor: form.actor || null,
    keyword: form.keyword || null,
    success: form.success,
    email: form.email || null,
    method: form.method || null,
    path: form.path || null,
    username: form.username || null,
    status_code: form.status_code || null,
    actor_uid: form.actor_uid || null,
    kind: form.kind || null,
    status: form.status || null,
    target_type: form.target_type || null,
    to: form.to || null,
  }
}

async function countRows() {
  counting.value = true
  countInfo.value = null
  try {
    const { data } = await api.post('/admin/exports/count', payload())
    countInfo.value = data
  } catch (e) {
    alert(e.response?.data?.detail || '统计失败')
  } finally {
    counting.value = false
  }
}

async function runExport() {
  exporting.value = true
  exportResult.value = null
  try {
    const token = localStorage.getItem('harness_access') || ''
    const resp = await fetch('/api/v1/admin/exports/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + token },
      body: JSON.stringify(payload()),
    })
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}))
      throw new Error(body.detail || '导出失败')
    }
    lastSha = resp.headers.get('X-Export-SHA256') || ''
    const rows = resp.headers.get('X-Export-Rows') || '0'
    const sourceLabel = resp.headers.get('X-Export-Source') || form.source
    const cd = resp.headers.get('Content-Disposition') || ''
    const m = cd.match(/filename="([^"]+)"/)
    const filename = m ? m[1] : 'harness-export.csv'
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    exportResult.value = { filename, sourceLabel, rows, sha256: lastSha }
    await loadHistory()
  } catch (e) {
    alert(e.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

async function loadHistory() {
  try {
    const { data } = await api.get('/admin/exports/history?limit=20')
    history.value = data || []
  } catch {
    /* ignore */
  }
}

function fmtTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (x) => String(x).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

onMounted(loadHistory)
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field > span {
  font-size: 12px;
  font-weight: 600;
  color: var(--admin-text-muted);
}

.field input,
.field select {
  padding: 8px 12px;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  font-size: 13px;
  background: var(--admin-card);
  color: var(--admin-text);
}

.count-info {
  margin-left: 12px;
  font-size: 13px;
  color: var(--success);
}

.count-info.warn {
  color: #f5a524;
}

.export-result {
  margin-top: 16px;
  border-top: 1px solid var(--admin-border);
  padding-top: 14px;
}

.er-ok {
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 10px;
}

.er-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 8px;
}

.er-grid > div {
  background: var(--admin-bg);
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  padding: 8px 12px;
}

.er-grid span {
  display: block;
  font-size: 11px;
  color: var(--admin-text-muted);
}

.er-grid b {
  font-size: 12.5px;
  word-break: break-all;
}

.mono {
  font-family: var(--font-mono, ui-monospace, monospace);
}

.hist-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--admin-border);
  font-size: 12.5px;
}

.hist-row:last-child {
  border-bottom: none;
}

.sha {
  color: var(--admin-text-muted);
  margin-left: auto;
}
</style>
