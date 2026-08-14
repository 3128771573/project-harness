<template>
  <div>
    <header class="page-head">
      <div>
        <h1>日志审计</h1>
        <p class="sub">记录管理员的每一次关键操作，可追溯</p>
      </div>
      <div class="actions">
        <button class="btn" @click="load"><svg viewBox="0 0 24 24" style="width:14px;height:14px;fill:currentColor"><path d="M17.65 6.35A7.95 7.95 0 0012 4a8 8 0 108 8h-2a6 6 0 11-1.76-4.24L13 11h7V4l-2.35 2.35z"/></svg>刷新</button>
      </div>
    </header>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr><th>时间</th><th>操作人</th><th>操作</th><th>详情</th><th>IP</th><th>结果</th></tr>
        </thead>
        <tbody>
          <tr v-for="l in items" :key="l.id">
            <td class="muted" style="white-space:nowrap">{{ fmtTime(l.created_time) }}</td>
            <td><b>{{ l.actor_name }}</b></td>
            <td><span class="action-tag">{{ actionLabel(l.action) }}</span></td>
            <td class="muted">{{ l.detail || '—' }}</td>
            <td class="uid-cell">{{ l.ip || '—' }}</td>
            <td>
              <span :class="['status-badge', l.success ? 'active' : 'disabled']">
                {{ l.success ? '成功' : '失败' }}
              </span>
            </td>
          </tr>
          <tr v-if="items.length === 0"><td colspan="6" style="text-align:center;padding:36px 0" class="muted">暂无审计日志</td></tr>
        </tbody>
      </table>
      <div class="table-footer">
        <span>共 {{ total }} 条</span>
        <div class="pager">
          <button class="page-btn" :disabled="page <= 1" @click="load(page-1)">‹</button>
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <button class="page-btn" :disabled="page >= totalPages" @click="load(page+1)">›</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../api/client'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 15
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function actionLabel(a) {
  const map = {
    'user.status': '用户状态',
    'user.role': '修改角色',
    'user.role.denied': '越权尝试',
    'user.sessions.revoke': '吊销会话',
    'user.password.reset': '重置密码',
    'settings.update': '系统设置',
    'ai.config.update': 'AI 配置',
  }
  return map[a] || a
}

function fmtTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

async function load(p) {
  page.value = p || 1
  try {
    const { data } = await api.get('/admin/audit-logs', { params: { page: page.value, page_size: pageSize } })
    items.value = data.items
    total.value = data.total
  } catch { /* ignore */ }
}

onMounted(() => load(1))
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.action-tag {
  display: inline-block;
  background: #f1f2f6;
  color: var(--text-secondary);
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}
</style>
