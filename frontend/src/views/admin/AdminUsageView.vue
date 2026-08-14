<template>
  <div>
    <header class="page-head">
      <div>
        <h1>用量统计</h1>
        <p class="sub">每位用户的 AI 使用量 · 全站累计 {{ usage?.total_calls ?? 0 }} 次</p>
      </div>
      <div class="actions">
        <button class="btn" @click="load">
          <svg viewBox="0 0 24 24" style="width:14px;height:14px;fill:currentColor"><path d="M17.65 6.35A7.95 7.95 0 0012 4a8 8 0 108 8h-2a6 6 0 11-1.76-4.24L13 11h7V4l-2.35 2.35z"/></svg>
          刷新
        </button>
      </div>
    </header>

    <div class="stat-grid" style="grid-template-columns: repeat(3, 1fr)">
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">使用用户</div>
          <div class="stat-value">{{ usage?.items?.filter(u => u.total_calls > 0).length ?? '—' }}</div>
        </div>
        <div class="stat-icon blue">
          <svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">全站累计调用</div>
          <div class="stat-value">{{ usage?.total_calls ?? '—' }}</div>
        </div>
        <div class="stat-icon violet">
          <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">注册用户</div>
          <div class="stat-value">{{ usage?.total ?? '—' }}</div>
        </div>
        <div class="stat-icon green">
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
        </div>
      </div>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>用户</th>
            <th>UID</th>
            <th>总调用</th>
            <th>今日调用</th>
            <th>最近使用</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in usage?.items || []" :key="u.uid">
            <td>
              <div class="user-cell">
                <span class="user-avatar">{{ initial(u.username) }}</span>
                <div>
                  <div class="name">{{ u.username }}</div>
                  <div class="email">{{ u.email }}</div>
                </div>
              </div>
            </td>
            <td><span class="uid-cell" :title="u.uid">{{ shortUid(u.uid) }}</span></td>
            <td>
              <span class="count-badge" :class="u.total_calls > 0 ? 'used' : ''">{{ u.total_calls }}</span>
            </td>
            <td class="muted">{{ u.today_calls }}</td>
            <td class="muted">{{ u.last_used ? formatTime(u.last_used) : '从未使用' }}</td>
          </tr>
          <tr v-if="!usage?.items?.length">
            <td colspan="5" style="text-align:center; padding:36px 0" class="muted">暂无数据</td>
          </tr>
        </tbody>
      </table>

      <div class="table-footer">
        <span>按总调用量降序排列</span>
        <div class="pager">
          <button class="page-btn" :disabled="page <= 1" @click="load(page - 1)">‹</button>
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <button class="page-btn" :disabled="page >= totalPages" @click="load(page + 1)">›</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../api/client'

const usage = ref(null)
const page = ref(1)
const pageSize = 10

const totalPages = computed(() => Math.max(1, Math.ceil((usage.value?.total || 0) / pageSize)))

function initial(name) {
  return (name || '?')[0].toUpperCase()
}

function shortUid(uid) {
  return uid ? uid.slice(0, 8) + '…' : ''
}

function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

async function load(p) {
  page.value = p || 1
  try {
    const { data } = await api.get('/admin/usage', { params: { page: page.value, page_size: pageSize } })
    usage.value = data
  } catch { /* interceptor 处理 */ }
}

onMounted(() => load(1))
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 700;
  background: #f1f2f6;
  color: #6b7280;
  font-variant-numeric: tabular-nums;
}

.count-badge.used {
  background: #eef2ff;
  color: #4338ca;
}
</style>
