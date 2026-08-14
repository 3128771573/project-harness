<template>
  <div>
    <header class="page-head">
      <div>
        <h1>访问记录</h1>
        <p class="sub">访客流量 · 时间/IP/路径追踪</p>
      </div>
      <div class="actions">
        <div class="search-box">
          <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
          <input v-model.trim="keyword" placeholder="搜索 IP / 路径" @keyup.enter="load(1)" />
        </div>
        <button class="btn" @click="load(page)"><svg viewBox="0 0 24 24" style="width:14px;height:14px;fill:currentColor"><path d="M17.65 6.35A7.95 7.95 0 0012 4a8 8 0 108 8h-2a6 6 0 11-1.76-4.24L13 11h7V4l-2.35 2.35z"/></svg>刷新</button>
      </div>
    </header>

    <!-- 统计卡 -->
    <section class="stat-grid" v-if="stats">
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">总访问量</div>
          <div class="stat-value">{{ stats.total_visits }}</div>
        </div>
        <div class="stat-icon blue"><svg viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/></svg></div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">今日访问</div>
          <div class="stat-value">{{ stats.today_visits }}</div>
        </div>
        <div class="stat-icon green"><svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg></div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">独立 IP</div>
          <div class="stat-value">{{ stats.unique_ips }}</div>
          <div class="stat-foot">今日 {{ stats.today_unique_ips }}</div>
        </div>
        <div class="stat-icon violet"><svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 010-5 2.5 2.5 0 010 5z"/></svg></div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">页面浏览</div>
          <div class="stat-value">{{ stats.page_views }}</div>
        </div>
        <div class="stat-icon amber"><svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg></div>
      </div>
    </section>

    <!-- 记录表格 -->
    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>时间</th>
            <th>IP</th>
            <th>类型</th>
            <th>路径</th>
            <th>设备</th>
            <th>用户</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in items" :key="v.id">
            <td class="muted" style="white-space:nowrap">{{ fmtTime(v.created_time) }}</td>
            <td class="uid-cell">{{ v.ip || '—' }}</td>
            <td>
              <span :class="['type-tag', v.method === 'PAGE' ? 'page' : 'api']">
                {{ v.method === 'PAGE' ? '页面' : (v.method || 'API') }}
              </span>
            </td>
            <td class="path-cell" :title="v.path">{{ v.path }}</td>
            <td class="muted">{{ v.device || '—' }}</td>
            <td>{{ v.username || (v.uid ? '已登录' : '<span class="muted">访客</span>') }}</td>
            <td>
              <span :class="['status-badge', (v.status_code || 200) < 400 ? 'active' : 'disabled']">
                {{ v.status_code || 200 }}
              </span>
            </td>
          </tr>
          <tr v-if="items.length === 0">
            <td colspan="7" style="text-align:center;padding:36px 0" class="muted">暂无访问记录</td>
          </tr>
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
const stats = ref(null)
const total = ref(0)
const page = ref(1)
const pageSize = 15
const keyword = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function fmtTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

async function load(p) {
  page.value = p || 1
  try {
    const { data } = await api.get('/admin/visits', {
      params: { page: page.value, page_size: pageSize, keyword: keyword.value || undefined },
    })
    items.value = data.items
    total.value = data.total
    stats.value = data.stats
  } catch { /* ignore */ }
}

onMounted(() => load(1))
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.type-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.type-tag.page {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
}

.type-tag.api {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
}

.path-cell {
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
  font-size: 12.5px;
}

.stat-foot {
  font-size: 11.5px;
  color: var(--admin-text-muted);
  margin-top: 4px;
}
</style>
