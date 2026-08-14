<template>
  <div class="page">
    <SiteNav />
    <div class="page-inner">
      <header class="page-head">
        <span class="page-tag">IOT PLATFORM</span>
        <h1>IoT 设备平台</h1>
        <p>注册设备，通过 MQTT 或 HTTP 上报遥测，实时查看</p>
      </header>

      <!-- 新增设备 -->
      <form class="add-row" @submit.prevent="createDevice">
        <input v-model.trim="newName" maxlength="64" placeholder="新设备名称，如：客厅温湿度计" required />
        <button type="submit" class="add-btn" :disabled="creating">{{ creating ? '创建中…' : '＋ 注册设备' }}</button>
      </form>
      <p v-if="msg" :class="['msg', msgOk ? 'ok' : 'err']">{{ msg }}</p>

      <!-- 设备卡片 -->
      <div v-if="devices.length === 0" class="empty">
        <p class="empty-emoji">📡</p>
        <p class="empty-text">还没有设备，先注册一个吧</p>
      </div>
      <div class="dev-grid">
        <div class="dev-card" v-for="d in devices" :key="d.id" :class="{ offline: !isOnline(d) }">
          <div class="dev-card-head">
            <span class="dev-name">{{ d.name }}</span>
            <span class="dev-status" :class="isOnline(d) ? 'on' : 'off'">
              <span class="st-dot"></span>{{ isOnline(d) ? '在线' : '离线' }}
            </span>
          </div>
          <div class="dev-main">
            <template v-if="d.last_payload && Object.keys(d.last_payload).length">
              <div v-for="(v, k) in d.last_payload" :key="k" class="dev-metric">
                <span>{{ k }}</span>
                <b>{{ fmtValue(v) }}</b>
              </div>
            </template>
            <div v-else class="dev-no-data">暂无遥测数据</div>
          </div>
          <div class="dev-token" title="设备 Token（上报鉴权用）">
            <code>{{ d.token }}</code>
            <button class="copy-btn" @click="copyToken(d)" :title="'复制 Token'">⧉</button>
          </div>
          <div class="dev-foot">
            <span>ID: {{ shortId(d.id) }}</span>
            <span>{{ lastSeenText(d) }}</span>
          </div>
          <div class="dev-actions">
            <button class="dev-act" @click="selectDevice(d)">📈 查看曲线</button>
            <button class="dev-act" @click="renameDevice(d)">✎</button>
            <button class="dev-act" @click="regenToken(d)">⟳</button>
            <button class="dev-act danger" @click="removeDevice(d)">🗑</button>
          </div>
        </div>
      </div>

      <!-- 实时曲线 -->
      <section class="chart-panel" v-if="devices.length > 0">
        <div class="chart-head">
          <div>
            <b>实时数据曲线</b>
            <span class="muted">{{ chartTitle }}</span>
          </div>
          <div class="chart-controls">
            <select v-model="selectedDeviceId" class="chart-select" @change="onDeviceSelect">
              <option v-for="d in devices" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
            <select v-if="numericKeys.length > 1" v-model="chartMetric" class="chart-select" @change="loadHistory">
              <option v-for="k in numericKeys" :key="k" :value="k">{{ k }}</option>
            </select>
            <span class="live-tag">LIVE</span>
          </div>
        </div>
        <svg viewBox="0 0 600 160" class="chart" preserveAspectRatio="none">
          <polyline :points="linePoints" fill="none" stroke="url(#lg2)" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
          <defs>
            <linearGradient id="lg2" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stop-color="#2563EB"/>
              <stop offset="1" stop-color="#7C3AED"/>
            </linearGradient>
          </defs>
        </svg>
        <div class="chart-axis">
          <span>{{ history.length > 0 ? '最近 ' + history.length + ' 条' : '等待数据…' }}</span>
          <span>现在</span>
        </div>
      </section>

      <!-- 接入说明 -->
      <section class="howto">
        <b>如何接入</b>
        <p>MQTT：发布到主题 <code>harness/&lt;device_id&gt;/telemetry</code>，payload 为
          <code>{"token": "设备Token", "data": {"temp": 26.5, "humidity": 60}}</code>。</p>
        <p>HTTP：<code>POST /api/v1/iot/devices/&lt;device_id&gt;/telemetry</code>（同 payload）。</p>
        <p>遥测频率建议 ≤ 1 次/秒；最近 30 秒内有上报即为「在线」。</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import SiteNav from '../components/SiteNav.vue'
import api from '../api/client'

const devices = ref([])
const newName = ref('')
const creating = ref(false)
const msg = ref('')
const msgOk = ref(true)

const selectedDeviceId = ref('')
const chartMetric = ref('temp')
const history = ref([])
let ws = null
let wsRetry = null
let statusTicker = null
const now = ref(Date.now())

const selectedDevice = computed(() => devices.value.find((d) => d.id === selectedDeviceId.value) || null)

const numericKeys = computed(() => {
  const p = selectedDevice.value?.last_payload || {}
  return Object.keys(p).filter((k) => typeof p[k] === 'number')
})

const chartTitle = computed(() => {
  if (!selectedDevice.value) return '选择一个设备查看曲线'
  return `${selectedDevice.value.name} · ${chartMetric.value}`
})

function isOnline(d) {
  if (!d.last_seen) return false
  return now.value - new Date(d.last_seen).getTime() < 30000
}

function lastSeenText(d) {
  if (!d.last_seen) return '从未上报'
  const diff = Math.max(0, Math.floor((now.value - new Date(d.last_seen).getTime()) / 1000))
  if (diff < 60) return `${diff} 秒前`
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  return `${Math.floor(diff / 3600)} 小时前`
}

function shortId(id) {
  return id ? id.slice(0, 8) + '…' : ''
}

function fmtValue(v) {
  return typeof v === 'number' ? (Math.round(v * 100) / 100).toString() : String(v)
}

function copyToken(d) {
  navigator.clipboard?.writeText(d.token || '').catch(() => {})
  msgOk.value = true
  msg.value = `已复制 ${d.name} 的 Token`
}

async function loadDevices() {
  try {
    const { data } = await api.get('/iot/devices')
    devices.value = data.items || []
    if (!selectedDeviceId.value && devices.value.length > 0) {
      selectedDeviceId.value = devices.value[0].id
      applyMetricDefault()
      await loadHistory()
    }
  } catch { /* ignore */ }
}

async function createDevice() {
  if (!newName.value) return
  creating.value = true
  msg.value = ''
  try {
    const { data } = await api.post('/iot/devices', { name: newName.value })
    devices.value.unshift(data)
    selectedDeviceId.value = data.id
    newName.value = ''
    msgOk.value = true
    msg.value = `设备「${data.name}」已注册，Token 已生成`
    await loadHistory()
  } catch (e) {
    msgOk.value = false
    msg.value = e.response?.data?.detail || '创建失败'
  } finally {
    creating.value = false
  }
}

async function renameDevice(d) {
  const name = prompt('重命名设备', d.name)
  if (!name || name.trim() === d.name) return
  try {
    const { data } = await api.put(`/iot/devices/${d.id}`, { name: name.trim() })
    Object.assign(d, data)
  } catch (e) {
    alert(e.response?.data?.detail || '重命名失败')
  }
}

async function regenToken(d) {
  if (!confirm(`重新生成「${d.name}」的 Token？旧 Token 将立即失效`)) return
  try {
    const { data } = await api.post(`/iot/devices/${d.id}/token`)
    Object.assign(d, data)
    msgOk.value = true
    msg.value = 'Token 已重新生成'
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

async function removeDevice(d) {
  if (!confirm(`删除设备「${d.name}」？其全部遥测数据将被删除`)) return
  try {
    await api.delete(`/iot/devices/${d.id}`)
    devices.value = devices.value.filter((x) => x.id !== d.id)
    if (selectedDeviceId.value === d.id) {
      selectedDeviceId.value = devices.value[0]?.id || ''
      await loadHistory()
    }
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function selectDevice(d) {
  selectedDeviceId.value = d.id
  applyMetricDefault()
  loadHistory()
}

function applyMetricDefault() {
  const keys = numericKeys.value
  if (keys.length && !keys.includes(chartMetric.value)) chartMetric.value = keys[0]
}

async function onDeviceSelect() {
  applyMetricDefault()
  await loadHistory()
}

async function loadHistory() {
  if (!selectedDeviceId.value) {
    history.value = []
    return
  }
  try {
    const { data } = await api.get(`/iot/devices/${selectedDeviceId.value}/telemetry`, { params: { limit: 120 } })
    history.value = data.items.map((it) => ({ t: it.created_time, v: Number(it.payload?.[chartMetric.value]) })).filter((p) => Number.isFinite(p.v))
  } catch { /* ignore */ }
}

const linePoints = computed(() => {
  const pts = history.value.slice(-120)
  if (pts.length < 2) return ''
  const values = pts.map((p) => p.v)
  let min = Math.min(...values)
  let max = Math.max(...values)
  if (max - min < 0.01) {
    min -= 1
    max += 1
  }
  const W = 600
  const H = 160
  return pts
    .map((p, i) => {
      const x = (i / (pts.length - 1)) * W
      const y = H - 12 - ((p.v - min) / (max - min)) * (H - 24)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
})

// ===== WebSocket 实时推送 =====
function connectWs() {
  const token = localStorage.getItem('harness_access')
  if (!token) return
  const proto = location.protocol === 'https:' ? 'wss://' : 'ws://'
  ws = new WebSocket(`${proto}${location.host}/api/v1/iot/ws?token=${token}`)
  ws.onmessage = (ev) => {
    try {
      const evt = JSON.parse(ev.data)
      if (evt.type !== 'telemetry') return
      const d = devices.value.find((x) => x.id === evt.device_id)
      if (!d) return
      d.last_payload = evt.payload
      d.last_seen = evt.created_time
      if (evt.device_id === selectedDeviceId.value) {
        const v = Number(evt.payload?.[chartMetric.value])
        if (Number.isFinite(v)) {
          history.value.push({ t: evt.created_time, v })
          if (history.value.length > 120) history.value.shift()
        }
      }
    } catch { /* ignore */ }
  }
  ws.onclose = () => {
    ws = null
    if (localStorage.getItem('harness_access')) {
      wsRetry = setTimeout(connectWs, 3000)
    }
  }
}

onMounted(async () => {
  await loadDevices()
  connectWs()
  statusTicker = setInterval(() => {
    now.value = Date.now()
  }, 5000)
})

onBeforeUnmount(() => {
  if (ws) ws.close()
  if (wsRetry) clearTimeout(wsRetry)
  if (statusTicker) clearInterval(statusTicker)
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--bg-card);
}

.page-inner {
  max-width: 1000px;
  margin: 0 auto;
  padding: 72px 28px;
}

.page-head {
  text-align: center;
  margin-bottom: 40px;
}

.page-tag {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: var(--success);
}

.page-head h1 {
  font-size: 38px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 12px 0 10px;
}

.page-head p {
  color: var(--text-muted);
  font-size: 15px;
}

/* 新增设备 */
.add-row {
  display: flex;
  gap: 10px;
  max-width: 460px;
  margin: 0 auto 16px;
}

.add-row input {
  flex: 1;
  padding: 11px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 14px;
  background: var(--bg-input);
  color: var(--text-primary);
  font-family: inherit;
}

.add-row input:focus {
  outline: none;
  border-color: var(--primary);
}

.add-btn {
  padding: 11px 18px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}

.add-btn:disabled {
  opacity: 0.6;
}

.msg {
  text-align: center;
  font-size: 13px;
  margin-bottom: 14px;
}

.msg.ok { color: var(--success); }
.msg.err { color: var(--error); }

.empty {
  text-align: center;
  padding: 48px 0;
}

.empty-emoji {
  font-size: 40px;
  margin-bottom: 10px;
}

.empty-text {
  color: var(--text-muted);
  font-size: 14px;
}

/* 设备卡片 */
.dev-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 18px;
  margin-bottom: 28px;
}

.dev-card {
  background: var(--brand-block);
  border-radius: 18px;
  padding: 20px;
  color: #fff;
  transition: transform 0.2s, box-shadow 0.2s;
}

.dev-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 44px rgba(15, 23, 42, 0.28);
}

.dev-card.offline {
  opacity: 0.75;
}

.dev-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.dev-name {
  font-size: 14px;
  font-weight: 700;
}

.dev-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
}

.dev-status.on {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.dev-status.off {
  background: rgba(148, 163, 184, 0.15);
  color: var(--text-muted);
}

.st-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.dev-status.on .st-dot {
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.25);
}

.dev-main {
  text-align: center;
  padding: 6px 0 14px;
  display: flex;
  justify-content: center;
  gap: 22px;
}

.dev-metric span {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 2px;
}

.dev-metric b {
  font-size: 26px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.dev-no-data {
  font-size: 13px;
  color: var(--text-muted);
  padding: 14px 0;
}

.dev-token {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 6px 10px;
  margin-bottom: 12px;
}

.dev-token code {
  flex: 1;
  font-size: 11.5px;
  color: #cbd5e1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
}

.copy-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
  padding: 2px 4px;
  border-radius: 5px;
}

.copy-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.dev-foot {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-muted);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 12px;
  margin-bottom: 10px;
}

.dev-actions {
  display: flex;
  gap: 6px;
}

.dev-act {
  flex: 1;
  background: rgba(255, 255, 255, 0.07);
  border: none;
  color: #e2e8f0;
  font-size: 12px;
  padding: 6px 0;
  border-radius: 8px;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;
}

.dev-act:hover {
  background: rgba(255, 255, 255, 0.14);
}

.dev-act.danger:hover {
  background: rgba(239, 68, 68, 0.25);
}

/* 曲线 */
.chart-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
}

.chart-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.chart-head b {
  font-size: 15px;
  font-weight: 700;
  display: block;
}

.chart-head .muted {
  font-size: 12.5px;
  color: var(--text-muted);
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.chart-select {
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 12.5px;
  background: var(--bg-input);
  color: var(--text-primary);
  font-family: inherit;
}

.live-tag {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: #dc2626;
  color: #fff;
  padding: 3px 8px;
  border-radius: 5px;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.chart {
  width: 100%;
  height: 160px;
  background:
    linear-gradient(rgba(15, 23, 42, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(15, 23, 42, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  border-radius: 10px;
}

.chart-axis {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 8px;
}

/* 接入说明 */
.howto {
  margin-top: 28px;
  padding: 18px 22px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.9;
}

.howto b {
  font-size: 13.5px;
  color: var(--text-primary);
}

.howto code {
  background: color-mix(in srgb, var(--text-primary) 8%, transparent);
  padding: 1px 6px;
  border-radius: 5px;
  font-size: 12px;
  font-family: var(--font-mono);
  word-break: break-all;
}

@media (max-width: 700px) {
  .add-row {
    flex-direction: column;
  }
}
</style>
