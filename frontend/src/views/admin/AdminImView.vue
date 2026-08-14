<template>
  <div>
    <header class="page-head">
      <div>
        <h1>举报审核</h1>
        <p class="sub">用户举报消息进入审核队列 · 处理（删除/封禁/忽略）后由机器人私信告知举报者</p>
      </div>
      <div class="actions">
        <button class="btn" @click="load()">刷新</button>
      </div>
    </header>

    <div class="filter-bar">
      <button
        v-for="f in filters"
        :key="f.value"
        class="filter-btn"
        :class="{ on: statusFilter === f.value }"
        @click="statusFilter = f.value; page = 1; load()"
      >
        {{ f.label }}
      </button>
    </div>

    <section class="panel">
      <div v-if="items.length === 0" class="muted" style="padding: 16px 0">暂无举报</div>
      <div v-for="r in items" :key="r.id" class="report-row">
        <div class="report-head">
          <b>{{ r.reporter.nickname || r.reporter.username }}</b>
          <span class="muted">举报了 {{ r.target_type === 'dm' ? '私信' : '群消息' }} · {{ formatTime(r.created_time) }}</span>
          <span :class="['status-badge', r.status === 'pending' ? 'active' : 'disabled']">
            {{ statusLabel(r.status) }}
          </span>
        </div>
        <div class="report-msg">
          <span v-if="r.message_sender" class="muted">发送者：{{ r.message_sender.nickname || r.message_sender.username }} · </span>
          <span>{{ r.message_content || '（消息已不存在）' }}</span>
        </div>
        <div class="report-reason">原因：{{ r.reason }}</div>
        <div v-if="r.status === 'pending'" class="report-actions">
          <button class="action-btn danger" @click="handle(r, 'delete')">删除消息</button>
          <button class="action-btn danger" @click="handle(r, 'ban')">封禁发送者</button>
          <button class="action-btn" @click="handle(r, 'ignore')">忽略</button>
        </div>
      </div>
    </section>

    <div v-if="total > pageSize" class="pager">
      <button class="btn sm" :disabled="page <= 1" @click="page--; load()">上一页</button>
      <span class="muted">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button class="btn sm" :disabled="page * pageSize >= total" @click="page++; load()">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../../api/client'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const statusFilter = ref('pending')
const filters = [
  { value: 'pending', label: '待处理' },
  { value: '', label: '全部' },
  { value: 'handled', label: '已处理' },
  { value: 'ignored', label: '已忽略' },
]

function statusLabel(s) {
  if (s === 'pending') return '待处理'
  if (s === 'handled') return '已处理'
  return '已忽略'
}

async function load() {
  try {
    const params = { page: page.value, page_size: pageSize }
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await api.get('/admin/im/reports', { params })
    items.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    alert(e.response?.data?.detail || '加载失败')
  }
}

async function handle(r, action) {
  const labels = { delete: '删除该消息', ban: '封禁发送者账号', ignore: '忽略该举报' }
  if (!confirm('确定' + labels[action] + '？处理结果将自动通过机器人私信告知举报者。')) return
  try {
    const note = prompt('备注（可选，会一并告知举报者）：') || undefined
    const { data } = await api.post('/admin/im/reports/' + r.id + '/handle', { action, note: note || null })
    alert('已处理：' + data.result)
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

function formatTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (x) => String(x).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
}

onMounted(load)
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.filter-btn {
  padding: 6px 14px;
  border: 1px solid var(--admin-border);
  background: var(--admin-card);
  border-radius: 20px;
  font-size: 12.5px;
  cursor: pointer;
  color: var(--admin-text-muted);
}

.filter-btn.on {
  background: #2563eb;
  color: #fff;
  border-color: transparent;
}

.report-row {
  border-bottom: 1px solid var(--admin-border);
  padding: 14px 0;
}

.report-row:last-child {
  border-bottom: none;
}

.report-head {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13.5px;
  flex-wrap: wrap;
}

.report-msg {
  margin-top: 8px;
  font-size: 13px;
  background: var(--admin-bg);
  border-radius: 8px;
  padding: 8px 12px;
  word-break: break-all;
}

.report-reason {
  margin-top: 6px;
  font-size: 12.5px;
  color: var(--admin-text-muted);
}

.report-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}

.pager {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  margin-top: 16px;
}
</style>
