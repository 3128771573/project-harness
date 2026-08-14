<template>
  <div>
    <header class="page-head">
      <div>
        <h1>留言管理</h1>
        <p class="sub">访客匿名留言 · 档案号追踪 · 多轮往来回复 · 回复后访客可凭查询码查看</p>
      </div>
      <div class="actions">
        <button class="btn" @click="load()">刷新</button>
      </div>
    </header>

    <!-- 统计 -->
    <section class="stat-grid" v-if="stats">
      <div class="stat-card">
        <div class="stat-info"><div class="stat-label">总留言</div><div class="stat-value">{{ stats.total }}</div></div>
        <div class="stat-icon blue">📋</div>
      </div>
      <div class="stat-card">
        <div class="stat-info"><div class="stat-label">今日留言</div><div class="stat-value">{{ stats.today }}</div></div>
        <div class="stat-icon green">📥</div>
      </div>
      <div class="stat-card">
        <div class="stat-info"><div class="stat-label">待回复</div><div class="stat-value">{{ stats.pending }}</div></div>
        <div class="stat-icon amber">✉️</div>
      </div>
    </section>

    <!-- 配置 -->
    <section class="panel" style="max-width: 640px">
      <div class="panel-title">留言板配置</div>
      <form @submit.prevent="saveConfig" class="config-form">
        <label class="field">
          <span>每日提交上限（次/24h/IP）</span>
          <input v-model.number="config.daily_limit" type="number" min="1" max="100" />
        </label>
        <label class="field">
          <span>验证码有效期（秒）</span>
          <input v-model.number="config.captcha_ttl" type="number" min="30" max="3600" />
        </label>
        <label class="field">
          <span>查询限速（次/分钟/IP）</span>
          <input v-model.number="config.query_rate" type="number" min="1" max="60" />
        </label>
        <button type="submit" class="btn" :disabled="configSaving">{{ configSaving ? '保存中…' : '保存配置' }}</button>
      </form>
    </section>

    <div v-if="error" class="error-text" style="padding:12px 18px">{{ error }}</div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <select v-model="statusFilter" @change="load(1)">
        <option value="">全部状态</option>
        <option value="pending">待回复</option>
        <option value="replied">已回复</option>
        <option value="closed">已关闭</option>
      </select>
      <input v-model="keyword" class="kw-input" placeholder="搜索内容 / 昵称 / 档案号 / 查询码…" @keydown.enter="load(1)" />
      <button class="btn sm" @click="load(1)">搜索</button>
    </div>

    <!-- 列表 -->
    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>时间</th>
            <th>档案号</th>
            <th>昵称</th>
            <th>内容</th>
            <th>IP</th>
            <th>状态</th>
            <th style="text-align:right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in items" :key="m.id">
            <td class="muted" style="white-space:nowrap">{{ fmtTime(m.created_time) }}</td>
            <td>
              <b class="archive-no" :title="'点击复制'" @click="copyArchive(m)">{{ m.archive_no || '—' }}</b>
            </td>
            <td>{{ m.nickname || '匿名' }}</td>
            <td class="msg-cell" :title="m.content">{{ m.content }}</td>
            <td class="uid-cell">{{ m.ip || '—' }}</td>
            <td>
              <span :class="['status-badge', statusClass(m.status)]">{{ statusLabel(m.status) }}</span>
              <span v-if="!m.is_read" class="status-badge disabled">未读</span>
              <span v-if="m.email" class="status-badge" title="留有邮箱，回复后自动邮件通知">✉</span>
            </td>
            <td style="text-align:right; white-space:nowrap">
              <button class="action-btn" @click="toggleRead(m)">{{ m.is_read ? '标未读' : '标已读' }}</button>
              <button class="action-btn" @click="openReply(m)">处理</button>
              <button class="action-btn danger" @click="removeMessage(m)">删除</button>
            </td>
          </tr>
          <tr v-if="items.length === 0">
            <td colspan="7" style="text-align:center; padding:36px 0" class="muted">暂无留言</td>
          </tr>
        </tbody>
      </table>
      <div class="table-footer">
        <span>共 {{ total }} 条</span>
        <div class="pager">
          <button class="page-btn" :disabled="page <= 1" @click="load(page - 1)">‹</button>
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <button class="page-btn" :disabled="page >= totalPages" @click="load(page + 1)">›</button>
        </div>
      </div>
    </div>

    <!-- 处理弹窗：档案 + 往来时间线 + 回复 + 模板 -->
    <div v-if="replying" class="modal-mask" @click.self="replying = null">
      <div class="modal wide">
        <h3>
          处理留言
          <button class="modal-x" @click="replying = null">✕</button>
        </h3>
        <div class="m-archive">
          <b class="archive-no">{{ replying.archive_no || '—' }}</b>
          <span class="muted small">查询码 {{ replying.query_code }}</span>
          <span :class="['status-badge', statusClass(replying.status)]">{{ statusLabel(replying.status) }}</span>
          <span v-if="replying.email" class="muted small">✉ {{ replying.email }}</span>
        </div>
        <p class="modal-content">{{ replying.content }}</p>
        <p class="muted small">{{ replying.nickname || '匿名' }} · 提交于 {{ fmtTime(replying.created_time) }} · IP {{ replying.ip || '—' }}</p>

        <div class="timeline">
          <div v-for="r in timeline" :key="r.id" class="tl-item" :class="'tl-' + r.sender_type">
            <div class="tl-head">
              <b>{{ r.sender_type === 'admin' ? '管理员' : (r.sender_name || '访客') }}</b>
              <span class="muted small">{{ fmtTime(r.created_time) }}</span>
            </div>
            <p class="tl-content">{{ r.content }}</p>
          </div>
          <div v-if="timeline.length === 0" class="muted small" style="padding:6px 0">暂无往来记录</div>
        </div>

        <div class="tpl-row" v-if="templates.length">
          <select v-model="tplPick" @change="applyTemplate">
            <option value="">使用快捷回复模板…</option>
            <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
          <button class="action-btn" @click="tplOpen = true">管理模板</button>
        </div>
        <textarea v-model.trim="replyText" rows="3" maxlength="2000" placeholder="输入回复内容（≤2000 字）"></textarea>

        <div class="modal-actions">
          <button class="action-btn" @click="replying = null">取消</button>
          <button v-if="replying.status !== 'closed'" class="action-btn" @click="closeMessage">关闭留言</button>
          <button v-else class="action-btn" @click="reopenMessage">重新打开</button>
          <button class="btn primary" :disabled="!replyText || replySaving" @click="saveReply">
            {{ replySaving ? '保存中…' : '发送回复' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 模板管理 -->
    <div v-if="tplOpen" class="modal-mask" @click.self="tplOpen = false">
      <div class="modal">
        <h3>快捷回复模板
          <button class="modal-x" @click="tplOpen = false">✕</button>
        </h3>
        <div class="tpl-add">
          <input v-model="tplName" placeholder="模板名称" maxlength="64" />
          <textarea v-model="tplContent" rows="2" placeholder="模板内容（≤2000 字）"></textarea>
          <button class="btn primary sm" :disabled="!tplName || !tplContent || tplSaving" @click="addTemplate">
            {{ tplSaving ? '添加中…' : '添加模板' }}
          </button>
        </div>
        <div class="tpl-list">
          <div v-for="t in templates" :key="t.id" class="tpl-item">
            <b>{{ t.name }}</b>
            <span class="muted small tpl-preview">{{ t.content }}</span>
            <button class="action-btn danger" @click="removeTemplate(t)">删除</button>
          </div>
          <div v-if="templates.length === 0" class="muted small" style="padding:8px 0">暂无模板</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../api/client'

const items = ref([])
const stats = ref(null)
const total = ref(0)
const page = ref(1)
const pageSize = 10
const error = ref('')
const statusFilter = ref('')
const keyword = ref('')

const replying = ref(null)
const timeline = ref([])
const replyText = ref('')
const replySaving = ref(false)

const templates = ref([])
const tplPick = ref('')
const tplOpen = ref(false)
const tplName = ref('')
const tplContent = ref('')
const tplSaving = ref(false)

const config = ref({ daily_limit: 3, captcha_ttl: 120, query_rate: 5 })
const configSaving = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function statusLabel(s) {
  if (s === 'pending') return '待回复'
  if (s === 'replied') return '已回复'
  if (s === 'closed') return '已关闭'
  return s || '待回复'
}

function statusClass(s) {
  if (s === 'pending') return 'disabled'
  if (s === 'closed') return 'disabled'
  return 'active'
}

function fmtTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
}

async function copyArchive(m) {
  try {
    await navigator.clipboard.writeText(m.archive_no || '')
    alert('档案号已复制：' + m.archive_no)
  } catch {
    /* ignore */
  }
}

async function load(p) {
  page.value = p || 1
  error.value = ''
  try {
    const params = { page: page.value, page_size: pageSize }
    if (statusFilter.value) params.status = statusFilter.value
    if (keyword.value.trim()) params.keyword = keyword.value.trim()
    const { data } = await api.get('/admin/messages', { params })
    items.value = data.items
    total.value = data.total
    stats.value = data.stats
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  }
}

async function toggleRead(m) {
  try {
    await api.put('/admin/messages/' + m.id + '/read', { is_read: !m.is_read })
    m.is_read = !m.is_read
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

async function openReply(m) {
  replying.value = m
  replyText.value = ''
  tplPick.value = ''
  timeline.value = []
  try {
    const { data } = await api.get('/admin/messages/' + m.id + '/replies')
    timeline.value = data || []
  } catch {
    /* ignore */
  }
  await loadTemplates()
}

function applyTemplate() {
  const t = templates.value.find((x) => x.id === tplPick.value)
  if (t) replyText.value = t.content
}

async function saveReply() {
  if (!replying.value) return
  replySaving.value = true
  try {
    const { data } = await api.put('/admin/messages/' + replying.value.id + '/reply', { reply: replyText.value })
    if (data.code !== 0) throw new Error(data.msg || '保存失败')
    replying.value.reply = replyText.value
    replying.value.is_read = true
    replying.value.status = 'replied'
    timeline.value.push({
      id: 'local-' + Date.now(),
      sender_type: 'admin',
      sender_name: '我',
      content: replyText.value,
      created_time: new Date().toISOString(),
    })
    replyText.value = ''
    tplPick.value = ''
    await load(page.value)
  } catch (e) {
    alert(e.response?.data?.detail || e.message || '保存失败')
  } finally {
    replySaving.value = false
  }
}

async function closeMessage() {
  if (!replying.value) return
  if (!confirm('关闭后访客将无法继续追问，确定？')) return
  try {
    await api.post('/admin/messages/' + replying.value.id + '/close')
    replying.value.status = 'closed'
    await load(page.value)
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

async function reopenMessage() {
  if (!replying.value) return
  try {
    await api.post('/admin/messages/' + replying.value.id + '/reopen')
    replying.value.status = 'pending'
    await load(page.value)
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

async function removeMessage(m) {
  if (!confirm('删除这条留言？')) return
  try {
    await api.delete('/admin/messages/' + m.id)
    await load(page.value)
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

async function loadConfig() {
  try {
    const { data } = await api.get('/admin/messages/config')
    config.value = data
  } catch { /* ignore */ }
}

async function saveConfig() {
  configSaving.value = true
  try {
    const { data } = await api.put('/admin/messages/config', config.value)
    config.value = data
    alert('配置已保存')
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    configSaving.value = false
  }
}

// ===== 快捷回复模板 =====
async function loadTemplates() {
  try {
    const { data } = await api.get('/admin/messages/templates')
    templates.value = data || []
  } catch {
    /* ignore */
  }
}

async function addTemplate() {
  tplSaving.value = true
  try {
    await api.post('/admin/messages/templates', { name: tplName.value.trim(), content: tplContent.value.trim() })
    tplName.value = ''
    tplContent.value = ''
    await loadTemplates()
  } catch (e) {
    alert(e.response?.data?.detail || '添加失败')
  } finally {
    tplSaving.value = false
  }
}

async function removeTemplate(t) {
  if (!confirm('删除模板「' + t.name + '」？')) return
  try {
    await api.delete('/admin/messages/templates/' + t.id)
    templates.value = templates.value.filter((x) => x.id !== t.id)
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

onMounted(() => {
  load(1)
  loadConfig()
  loadTemplates()
})
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.config-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
  max-width: 320px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field > span {
  font-size: 13px;
  font-weight: 600;
  color: var(--admin-text-muted);
}

.field input {
  padding: 9px 12px;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  font-size: 13px;
  background: var(--admin-card);
  color: var(--admin-text);
  font-family: inherit;
}

.msg-cell {
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.archive-no {
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 12px;
  color: #2563eb;
  cursor: pointer;
  white-space: nowrap;
}

.filter-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
  max-width: 640px;
}

.filter-bar select,
.kw-input {
  padding: 8px 12px;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  font-size: 13px;
  background: var(--admin-card);
  color: var(--admin-text);
}

.kw-input {
  flex: 1;
  min-width: 220px;
}

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 300;
  padding: 20px;
}

.modal {
  width: 100%;
  max-width: 460px;
  background: var(--admin-card);
  border: 1px solid var(--admin-border);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.modal.wide {
  max-width: 620px;
}

.modal h3 {
  font-size: 15px;
  color: var(--admin-text);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-x {
  border: none;
  background: none;
  color: var(--admin-text-muted);
  font-size: 15px;
  cursor: pointer;
}

.m-archive {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.modal-content {
  font-size: 13px;
  color: var(--admin-text);
  background: var(--admin-bg);
  border-radius: 8px;
  padding: 10px 12px;
  max-height: 120px;
  overflow-y: auto;
  white-space: pre-wrap;
}

.modal textarea {
  padding: 10px 12px;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  font-size: 13.5px;
  background: var(--admin-bg);
  color: var(--admin-text);
  font-family: inherit;
  resize: vertical;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.timeline {
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-top: 1px dashed var(--admin-border);
  padding-top: 10px;
}

.tl-item {
  border-left: 3px solid var(--admin-border);
  padding-left: 10px;
}

.tl-item.tl-visitor {
  border-left-color: #f5a524;
}

.tl-item.tl-admin {
  border-left-color: #2563eb;
}

.tl-head {
  display: flex;
  gap: 10px;
  align-items: baseline;
  font-size: 12px;
}

.tl-content {
  margin: 3px 0 0;
  font-size: 13px;
  color: var(--admin-text);
  white-space: pre-wrap;
}

.tpl-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.tpl-row select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  font-size: 13px;
  background: var(--admin-bg);
  color: var(--admin-text);
}

.tpl-add {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tpl-add input,
.tpl-add textarea {
  padding: 8px 12px;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  font-size: 13px;
  background: var(--admin-bg);
  color: var(--admin-text);
  font-family: inherit;
}

.tpl-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 260px;
  overflow-y: auto;
}

.tpl-item {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid var(--admin-border);
  border-radius: 8px;
  padding: 8px 10px;
}

.tpl-item b {
  font-size: 13px;
  flex: none;
}

.tpl-preview {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
