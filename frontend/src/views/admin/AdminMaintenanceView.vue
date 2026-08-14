<template>
  <div>
    <header class="page-head">
      <div>
        <h1>维护模式管理</h1>
        <p class="sub">分级控制 · 倒计时自动恢复 · 超时兜底 · 定时维护 · 紧急逃生通道（superadmin）</p>
      </div>
    </header>

    <!-- 当前状态 -->
    <section class="panel" style="max-width: 860px">
      <div class="panel-title">当前状态</div>
      <div class="status-card" :class="{ active: isActive }">
        <div class="st-left">
          <div class="st-icon">{{ isActive ? '🔴' : '🟢' }}</div>
          <div>
            <b>{{ isActive ? '维护中' : '正常运行' }}</b>
            <span class="muted small">{{ status.mode === 'none' ? '所有用户均可正常访问' : modeLabel(status.mode) + '（' + status.mode + '）' }}</span>
          </div>
        </div>
        <div class="st-meta" v-if="isActive">
          <div><span>开启人</span><b>{{ status.operator || '—' }}</b></div>
          <div><span>开启时间</span><b>{{ fmtTime(status.start_at) }}</b></div>
          <div><span>原因</span><b>{{ status.reason || '—' }}</b></div>
          <div v-if="status.auto_close_at"><span>计划恢复</span><b>{{ fmtTime(status.auto_close_at) }}</b></div>
          <div v-if="status.remaining_seconds > 0"><span>倒计时</span><b class="mono">{{ fmtCountdown(status.remaining_seconds) }}</b></div>
        </div>
        <div class="st-actions" v-if="isActive">
          <button class="btn sm" @click="extend(15)">+15 分钟</button>
          <button class="btn sm" @click="extend(30)">+30 分钟</button>
          <button class="btn sm" @click="extend(60)">+60 分钟</button>
          <button class="btn primary danger" @click="disable">关闭维护模式</button>
        </div>
      </div>
      <p class="muted small" style="margin:10px 0 0">
        自动恢复保险：倒计时结束自动关闭（优先级 1）→ 超过最大时长 {{ status.max_duration_minutes }} 分钟自动关闭（优先级 2）→ 服务器重启检测遗留状态（优先级 3）。手动关闭优先级最高。
      </p>
    </section>

    <!-- 开启维护 -->
    <section class="panel" style="max-width: 860px; margin-top:16px">
      <div class="panel-title">开启维护模式</div>
      <div class="mode-grid">
        <label v-for="m in modes" :key="m.value" class="mode-card" :class="{ on: form.mode === m.value }">
          <input type="radio" :value="m.value" v-model="form.mode" />
          <b>{{ m.icon }} {{ m.label }}</b>
          <span class="muted small">{{ m.desc }}</span>
        </label>
      </div>
      <div class="form-grid">
        <label class="field wide">
          <span>维护原因（必填，≤200 字，将展示在维护页）</span>
          <input v-model.trim="form.reason" maxlength="200" placeholder="例如：数据库升级，预计 30 分钟" />
        </label>
        <label class="field">
          <span>预计时长（分钟，留空需手动关闭）</span>
          <input v-model.number="form.duration" type="number" min="1" max="1440" placeholder="留空 = 手动关闭" />
        </label>
      </div>
      <div class="actions" style="margin-top:12px">
        <button class="btn danger" :disabled="!form.reason || enabling" @click="enable">
          {{ enabling ? '开启中…' : '🔴 立即开启' }}
        </button>
      </div>
    </section>

    <!-- 定时维护计划 -->
    <section class="panel" style="max-width: 860px; margin-top:16px">
      <div class="panel-title">定时维护计划（夜间自动维护）</div>
      <div class="toggle-row">
        <div>
          <b>启用定时维护</b>
          <p class="small muted">到达计划时间自动进入 scheduled 模式，时长结束后自动恢复</p>
        </div>
        <label class="switch">
          <input type="checkbox" v-model="sched.enabled" />
          <span class="slider"></span>
        </label>
      </div>
      <div class="form-grid">
        <label class="field">
          <span>每天执行时间</span>
          <input v-model="sched.time" type="time" />
        </label>
        <label class="field">
          <span>维护时长（分钟）</span>
          <input v-model.number="sched.duration" type="number" min="1" max="1440" />
        </label>
      </div>
      <div class="day-row">
        <span class="muted small">每周执行日（不选 = 每天）：</span>
        <label v-for="(d, i) in dayNames" :key="i" class="day-chip">
          <input type="checkbox" :value="i" v-model="sched.days" />
          <span>{{ d }}</span>
        </label>
      </div>
      <div class="actions" style="margin-top:12px">
        <button class="btn" :disabled="savingSched" @click="saveSchedule">{{ savingSched ? '保存中…' : '📅 保存定时计划' }}</button>
      </div>
    </section>

    <!-- 紧急令牌 -->
    <section class="panel" style="max-width: 860px; margin-top:16px">
      <div class="panel-title">紧急逃生通道</div>
      <p class="muted small" style="margin:0 0 10px">
        紧急令牌可在无法登录后台时关闭维护：访问
        <code class="mono">/api/v1/admin/maintenance/emergency-close?token=令牌</code>。
        令牌以 SHA-256 哈希存储，明文仅在生成时显示一次，请妥善保存。
      </p>
      <div class="emergency-row">
        <span class="status-badge" :class="status.emergency_configured ? 'active' : 'disabled'">
          {{ status.emergency_configured ? '已配置' : '未配置' }}
        </span>
        <button class="btn sm" @click="regenerate">{{ regenerating ? '生成中…' : '重新生成令牌' }}</button>
      </div>
      <div v-if="newToken" class="token-box">
        <div class="token-line mono">{{ newToken }}</div>
        <p class="muted small">⚠️ 请立即复制保存（明文仅显示这一次）：</p>
        <button class="btn sm" @click="copyToken">复制令牌</button>
      </div>
    </section>

    <!-- 操作记录 -->
    <section class="panel" style="max-width: 860px; margin-top:16px">
      <div class="panel-title">操作记录（审计）</div>
      <div v-if="history.length === 0" class="muted" style="padding:8px 0">暂无维护操作记录</div>
      <div v-for="h in history" :key="h.id" class="hist-row">
        <span class="muted mono">{{ h.time_utc ? fmtTime(h.time_utc) : '' }}</span>
        <b>{{ h.operator }}</b>
        <span class="act-chip">{{ h.action.replace('maintenance.', '') }}</span>
        <span class="muted small">{{ h.detail }}</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import api from '../../api/client'

const status = ref({ mode: 'none', max_duration_minutes: 120, remaining_seconds: 0, emergency_configured: false, scheduled_enabled: false, scheduled_time: '03:00', scheduled_duration: 60, scheduled_days: '' })
const history = ref([])
const enabling = ref(false)
const regenerating = ref(false)
const savingSched = ref(false)
const newToken = ref('')
let timer = null

const isActive = computed(() => status.value.mode !== 'none')

const modes = [
  { value: 'full', label: '全站维护', icon: '🔧', desc: '拦截所有访客与普通用户（重大升级、数据库迁移）' },
  { value: 'block_new', label: '仅拦截新访客', icon: '🚪', desc: '已登录用户正常访问（灰度测试、邀请制内测）' },
  { value: 'scheduled', label: '定时维护', icon: '⏰', desc: '与全站维护相同，由定时计划驱动' },
  { value: 'admin_only', label: '仅管理员模式', icon: '🔒', desc: '仅管理员可访问（内部测试、环境验证）' },
]

const form = reactive({ mode: 'full', reason: '', duration: null })
const sched = reactive({ enabled: false, time: '03:00', duration: 60, days: [] })
const dayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

function modeLabel(m) {
  return ({ full: '全站维护', block_new: '仅拦截新访客', scheduled: '定时维护', admin_only: '仅管理员模式' })[m] || m
}

function fmtTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const pad = (x) => String(x).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds())
}

function fmtCountdown(sec) {
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  const pad = (x) => String(x).padStart(2, '0')
  return pad(h) + ':' + pad(m) + ':' + pad(s)
}

async function load() {
  try {
    const { data } = await api.get('/admin/maintenance/status')
    status.value = data
    sched.enabled = data.scheduled_enabled
    sched.time = data.scheduled_time || '03:00'
    sched.duration = data.scheduled_duration || 60
    sched.days = data.scheduled_days ? data.scheduled_days.split(',').map(Number) : []
  } catch { /* ignore */ }
  try {
    const { data } = await api.get('/admin/maintenance/history?limit=20')
    history.value = data || []
  } catch { /* ignore */ }
}

async function enable() {
  enabling.value = true
  try {
    await api.post('/admin/maintenance/enable', {
      mode: form.mode,
      reason: form.reason,
      duration_minutes: form.duration || null,
    })
    form.reason = ''
    form.duration = null
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '开启失败')
  } finally {
    enabling.value = false
  }
}

async function disable() {
  if (!confirm('确定关闭维护模式？服务将立即恢复。')) return
  try {
    await api.post('/admin/maintenance/disable')
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '关闭失败')
  }
}

async function extend(minutes) {
  try {
    await api.post('/admin/maintenance/extend', { minutes })
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '延长失败')
  }
}

async function saveSchedule() {
  savingSched.value = true
  try {
    await api.post('/admin/maintenance/schedule', {
      enabled: sched.enabled,
      time: sched.time || '03:00',
      duration: sched.duration || 60,
      days: sched.days,
    })
    await load()
    alert('定时计划已保存')
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    savingSched.value = false
  }
}

async function regenerate() {
  if (!confirm('重新生成后旧令牌立即失效，确定？')) return
  regenerating.value = true
  newToken.value = ''
  try {
    const { data } = await api.post('/admin/maintenance/regenerate-token')
    newToken.value = data.token
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '生成失败')
  } finally {
    regenerating.value = false
  }
}

async function copyToken() {
  try {
    await navigator.clipboard.writeText(newToken.value)
    alert('令牌已复制')
  } catch { /* ignore */ }
}

onMounted(() => {
  load()
  timer = setInterval(() => {
    if (status.value.remaining_seconds > 0) status.value.remaining_seconds -= 1
  }, 1000)
})

onUnmounted(() => clearInterval(timer))
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.status-card {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  border: 1px solid var(--admin-border);
  border-radius: 12px;
  padding: 14px 16px;
  background: var(--admin-bg);
}

.status-card.active {
  border-color: rgba(229, 72, 77, 0.4);
  background: rgba(229, 72, 77, 0.05);
}

.st-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.st-icon {
  font-size: 28px;
}

.st-left b {
  display: block;
  font-size: 16px;
}

.st-meta {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  flex: 1;
}

.st-meta span {
  display: block;
  font-size: 11px;
  color: var(--admin-text-muted);
}

.st-meta b {
  font-size: 12.5px;
}

.st-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.mode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px;
  margin: 12px 0;
}

.mode-card {
  border: 1px solid var(--admin-border);
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mode-card.on {
  border-color: #2563eb;
  background: rgba(37, 99, 235, 0.06);
}

.mode-card input {
  display: none;
}

.mode-card b {
  font-size: 13px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field.wide {
  grid-column: 1 / -1;
}

.field > span {
  font-size: 12px;
  font-weight: 600;
  color: var(--admin-text-muted);
}

.field input {
  padding: 8px 12px;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  font-size: 13px;
  background: var(--admin-card);
  color: var(--admin-text);
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.toggle-row b {
  font-size: 13.5px;
}

.switch {
  position: relative;
  width: 42px;
  height: 24px;
  flex: none;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  inset: 0;
  background: var(--admin-border);
  border-radius: 24px;
  cursor: pointer;
  transition: 0.2s;
}

.slider::before {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  left: 3px;
  top: 3px;
  background: #fff;
  border-radius: 50%;
  transition: 0.2s;
}

.switch input:checked + .slider {
  background: #2563eb;
}

.switch input:checked + .slider::before {
  transform: translateX(18px);
}

.day-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.day-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  cursor: pointer;
}

.btn.danger {
  background: var(--error, #e5484d);
  color: #fff;
  border-color: transparent;
}

.emergency-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.token-box {
  margin-top: 12px;
  border: 1px dashed var(--admin-border);
  border-radius: 10px;
  padding: 12px;
}

.token-line {
  word-break: break-all;
  font-size: 12.5px;
  color: #2563eb;
  margin-bottom: 6px;
}

.hist-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 7px 0;
  border-bottom: 1px solid var(--admin-border);
  font-size: 12.5px;
}

.hist-row:last-child {
  border-bottom: none;
}

.act-chip {
  background: var(--admin-bg);
  border: 1px solid var(--admin-border);
  border-radius: 10px;
  padding: 1px 8px;
  font-size: 11px;
  flex: none;
}

.mono {
  font-family: var(--font-mono, ui-monospace, monospace);
}
</style>
