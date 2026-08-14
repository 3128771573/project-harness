<template>
  <div>
    <header class="page-head">
      <div>
        <h1>安全中心</h1>
        <p class="sub">登录记录与风险事件</p>
      </div>
      <div class="actions">
        <button class="btn" @click="load"><svg viewBox="0 0 24 24" style="width:14px;height:14px;fill:currentColor"><path d="M17.65 6.35A7.95 7.95 0 0012 4a8 8 0 108 8h-2a6 6 0 11-1.76-4.24L13 11h7V4l-2.35 2.35z"/></svg>刷新</button>
      </div>
    </header>

    <div class="stat-grid" style="grid-template-columns: repeat(3, 1fr)">
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">登录总次数</div>
          <div class="stat-value">{{ total }}</div>
        </div>
        <div class="stat-icon blue"><svg viewBox="0 0 24 24" style="width:19px;height:19px;fill:#fff"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM4 12c0-4.41 3.59-8 8-8 .34 0 .67.02 1 .05V10h2V4.59c2.9 1.41 5 4.42 5 7.9v.51H4v-.5z"/></svg></div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">成功登录</div>
          <div class="stat-value">{{ okCount }}</div>
        </div>
        <div class="stat-icon green"><svg viewBox="0 0 24 24" style="width:19px;height:19px;fill:#fff"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">失败尝试</div>
          <div class="stat-value" :style="{ color: failCount > 0 ? '#dc2626' : '' }">{{ failCount }}</div>
        </div>
        <div class="stat-icon amber"><svg viewBox="0 0 24 24" style="width:19px;height:19px;fill:#fff"><path d="M11 15h2v2h-2zm0-8h2v6h-2zm.99-5C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/></svg></div>
      </div>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr><th>时间</th><th>用户</th><th>登录方式</th><th>IP</th><th>设备</th><th>结果</th><th>原因</th></tr>
        </thead>
        <tbody>
          <tr v-for="l in items" :key="l.id">
            <td class="muted" style="white-space:nowrap">{{ fmtTime(l.created_time) }}</td>
            <td><b>{{ l.username || l.email || '—' }}</b></td>
            <td style="white-space:nowrap">
              <span class="method-tag">{{ methodLabel(l.method) }}</span>
              <span v-if="l.used_2fa" class="method-tag totp" title="通过两步验证">2FA</span>
            </td>
            <td class="uid-cell">{{ l.ip || '—' }}</td>
            <td class="muted">{{ l.device || '—' }}</td>
            <td>
              <span :class="['status-badge', l.success ? 'active' : 'disabled']">{{ l.success ? '成功' : '失败' }}</span>
            </td>
            <td class="muted">{{ l.reason || '—' }}</td>
          </tr>
          <tr v-if="items.length === 0"><td colspan="7" style="text-align:center;padding:36px 0" class="muted">暂无登录记录</td></tr>
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
const okCount = computed(() => items.value.filter(i => i.success).length)
const failCount = computed(() => items.value.filter(i => !i.success).length)

function fmtTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function methodLabel(m) {
  return { password: '密码', code: '邮箱验证码', sso: 'GitHub SSO', register: '注册', reset: '密码重置' }[m] || (m || '—')
}

async function load(p) {
  page.value = p || 1
  try {
    const { data } = await api.get('/admin/login-logs', { params: { page: page.value, page_size: pageSize } })
    items.value = data.items
    total.value = data.total
  } catch { /* ignore */ }
}

onMounted(() => load(1))
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.method-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  background: rgba(99, 102, 241, 0.12);
  color: #818cf8;
  margin-right: 4px;
}

.method-tag.totp {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
}
</style>
