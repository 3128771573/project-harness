<template>
  <div>
    <header class="page-head">
      <div>
        <h1>留言管理</h1>
        <p class="sub">访客匿名留言 · 回复后访客可凭查询码查看</p>
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

    <!-- 列表 -->
    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>时间</th>
            <th>昵称</th>
            <th>邮箱</th>
            <th>内容</th>
            <th>IP</th>
            <th>状态</th>
            <th style="text-align:right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in items" :key="m.id">
            <td class="muted" style="white-space:nowrap">{{ fmtTime(m.created_time) }}</td>
            <td>{{ m.nickname || '匿名' }}</td>
            <td class="muted">{{ m.email || '—' }}</td>
            <td class="msg-cell" :title="m.content">{{ m.content }}</td>
            <td class="uid-cell">{{ m.ip || '—' }}</td>
            <td>
              <span :class="['status-badge', m.is_read ? 'active' : 'disabled']">{{ m.is_read ? '已读' : '未读' }}</span>
              <span v-if="m.reply" class="status-badge active">已回复</span>
            </td>
            <td style="text-align:right; white-space:nowrap">
              <button class="action-btn" @click="toggleRead(m)">{{ m.is_read ? '标未读' : '标已读' }}</button>
              <button class="action-btn" @click="openReply(m)">回复</button>
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

    <!-- 回复弹窗 -->
    <div v-if="replying" class="modal-mask" @click.self="replying = null">
      <div class="modal">
        <h3>回复留言</h3>
        <p class="muted small">{{ replying.nickname || '匿名' }} · {{ fmtTime(replying.created_time) }}</p>
        <p class="modal-content">{{ replying.content }}</p>
        <textarea v-model.trim="replyText" rows="4" maxlength="2000" placeholder="输入回复内容（≤2000 字）"></textarea>
        <div class="modal-actions">
          <button class="action-btn" @click="replying = null">取消</button>
          <button class="btn primary" :disabled="!replyText || replySaving" @click="saveReply">
            {{ replySaving ? '保存中…' : '保存回复' }}
          </button>
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
const replying = ref(null)
const replyText = ref('')
const replySaving = ref(false)
const config = ref({ daily_limit: 3, captcha_ttl: 120, query_rate: 5 })
const configSaving = ref(false)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function fmtTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
}

async function load(p) {
  page.value = p || 1
  error.value = ''
  try {
    const { data } = await api.get('/admin/messages', { params: { page: page.value, page_size: pageSize } })
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

function openReply(m) {
  replying.value = m
  replyText.value = m.reply || ''
}

async function saveReply() {
  if (!replying.value) return
  replySaving.value = true
  try {
    await api.put('/admin/messages/' + replying.value.id + '/reply', { reply: replyText.value })
    replying.value.reply = replyText.value
    replying.value.is_read = true
    replying.value = null
    await load(page.value)
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    replySaving.value = false
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

onMounted(() => {
  load(1)
  loadConfig()
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
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
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

.modal h3 {
  font-size: 15px;
  color: var(--admin-text);
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
</style>
