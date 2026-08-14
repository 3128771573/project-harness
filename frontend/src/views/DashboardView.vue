<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo-wrap">
        <BrandLogo size="md" />
        <span class="logo-name">Harness</span>
      </div>
      <nav>
        <router-link to="/dashboard" class="nav-item active">仪表盘</router-link>
        <router-link to="/ai" class="nav-item">AI 对话</router-link>
        <router-link to="/iot" class="nav-item">IoT 平台</router-link>
        <router-link to="/settings" class="nav-item">安全设置</router-link>
        <router-link v-if="isAdmin" to="/admin/dashboard" class="nav-item">管理后台</router-link>
      </nav>
      <div class="sidebar-theme">
        <ThemeSwitcher />
      </div>
      <button class="logout" @click="logout">退出登录</button>
    </aside>

    <main class="main">
      <!-- 欢迎区 -->
      <header class="welcome-bar fade-up">
        <div>
          <h1>{{ greeting }}，{{ user?.nickname || user?.username }}</h1>
          <p class="welcome-sub">Your workspace · {{ today }}</p>
        </div>
        <div class="user-chip">
          <img v-if="user?.avatar" :src="user.avatar" class="avatar-img" alt="" />
          <span v-else class="avatar">{{ avatarChar }}</span>
          <span>{{ user?.nickname || user?.username }}</span>
          <span v-if="user?.role" class="role-chip">{{ user.role }}</span>
        </div>
      </header>

      <!-- 今日概览（数字增长动画） -->
      <section class="stat-grid fade-up">
        <div class="stat-card">
          <div class="stat-info">
            <div class="stat-label">AI Usage</div>
            <div class="stat-value">
              <CountUp :value="todayStats.aiCalls ?? 0" suffix=" 次" />
            </div>
            <div class="stat-foot">今日请求</div>
          </div>
          <div class="stat-icon blue"><svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg></div>
        </div>
        <div class="stat-card">
          <div class="stat-info">
            <div class="stat-label">Devices</div>
            <div class="stat-value">
              <CountUp :value="todayStats.onlineDevices ?? 0" suffix=" 在线" />
            </div>
            <div class="stat-foot">共 {{ todayStats.devices ?? 0 }} 台设备</div>
          </div>
          <div class="stat-icon green"><svg viewBox="0 0 24 24"><path d="M17 10.5V7a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h12a1 1 0 001-1v-3.5l4 4v-11l-4 4z"/></svg></div>
        </div>
        <div class="stat-card">
          <div class="stat-info">
            <div class="stat-label">System</div>
            <div class="stat-value">
              <CountUp :value="99.9" :decimals="1" suffix="%" />
            </div>
            <div class="stat-foot">服务可用性</div>
          </div>
          <div class="stat-icon amber"><svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg></div>
        </div>
        <div class="stat-card">
          <div class="stat-info">
            <div class="stat-label">Member</div>
            <div class="stat-value">
              <CountUp :value="daysJoinedNum" suffix=" 天" />
            </div>
            <div class="stat-foot">加入平台</div>
          </div>
          <div class="stat-icon violet"><svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg></div>
        </div>
      </section>

      <!-- 快速入口 -->
      <section class="quick-row fade-up">
        <router-link to="/ai" class="quick-card">
          <span class="q-emoji">🤖</span>
          <div><b>AI Assistant</b><span>多模型对话</span></div>
          <span class="q-arrow">→</span>
        </router-link>
        <router-link to="/iot" class="quick-card">
          <span class="q-emoji">📡</span>
          <div><b>IoT Monitor</b><span>设备监控</span></div>
          <span class="q-arrow">→</span>
        </router-link>
        <router-link to="/demo" class="quick-card">
          <span class="q-emoji">🧪</span>
          <div><b>Demo Lab</b><span>实验展示</span></div>
          <span class="q-arrow">→</span>
        </router-link>
        <router-link to="/settings" class="quick-card">
          <span class="q-emoji">⚙️</span>
          <div><b>Settings</b><span>账号安全</span></div>
          <span class="q-arrow">→</span>
        </router-link>
      </section>

      <!-- 最近活动 -->
      <section class="panel fade-up">
        <h3>最近活动</h3>
        <div v-if="activities.length === 0" class="empty-state">
          <p class="muted">暂无活动记录</p>
          <router-link to="/ai" class="btn small">去体验 AI →</router-link>
        </div>
        <div v-else class="activity-list">
          <div v-for="a in activities" :key="a.id" class="activity-item">
            <span class="act-icon" :class="a.type">{{ a.icon }}</span>
            <div class="act-body">
              <b>{{ a.title }}</b>
              <span class="act-time">{{ a.time }}</span>
            </div>
            <span v-if="a.detail" class="act-detail">{{ a.detail }}</span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '../components/BrandLogo.vue'
import ThemeSwitcher from '../components/ThemeSwitcher.vue'
import CountUp from '../components/CountUp.vue'
import api from '../api/client'

const router = useRouter()
const user = ref(null)
const todayStats = ref({})
const activities = ref([])

const avatarChar = computed(() => (user.value?.username?.[0] || 'U').toUpperCase())
const isAdmin = computed(() => ['admin', 'super_admin'].includes(user.value?.role))
const today = new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return 'Good morning'
  if (h < 18) return 'Good afternoon'
  return 'Good evening'
})

const daysJoinedNum = computed(() => {
  if (!user.value?.created_time) return 0
  return Math.max(1, Math.floor((Date.now() - new Date(user.value.created_time)) / 86400000))
})

async function load() {
  try {
    const { data } = await api.get('/user/profile')
    user.value = data
    localStorage.setItem('harness_user', JSON.stringify(data))
  } catch { /* ignore */ }

  // 今日 AI 调用（从历史接口统计今天次数）
  try {
    const { data } = await api.get('/ai/history', { params: { limit: 100 } })
    const now = new Date()
    const todayCount = data.items.filter((h) => {
      const d = new Date(h.created_time)
      return d.toDateString() === now.toDateString()
    }).length
    todayStats.value.aiCalls = todayCount
  } catch { /* ignore */ }

  // 最近活动：AI 记录 + 登录记录混合
  try {
    const { data: ai } = await api.get('/ai/history', { params: { limit: 5 } })
    const { data: logs } = await api.get('/user/login-logs')
    const acts = []
    ai.items.forEach((h) =>
      acts.push({
        id: 'ai-' + h.id,
        type: 'ai',
        icon: '🤖',
        title: 'AI 对话',
        detail: h.question.slice(0, 40),
        time: fmtTime(h.created_time),
      })
    )
    logs.items
      .filter((l) => l.success)
      .forEach((l) =>
        acts.push({
          id: 'lg-' + l.id,
          type: 'login',
          icon: '🔐',
          title: '登录成功',
          detail: l.device || '',
          time: fmtTime(l.created_time),
        })
      )
    acts.sort((a, b) => new Date(b.time) - new Date(a.time))
    activities.value = acts.slice(0, 8)
  } catch { /* ignore */ }
}

function fmtTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function logout() {
  localStorage.removeItem('harness_access')
  localStorage.removeItem('harness_refresh')
  localStorage.removeItem('harness_user')
  router.push('/')
}

onMounted(load)
</script>

<style scoped src="../assets/dashboard.css"></style>
<style scoped>
/* 侧边栏 */
.logo-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px 26px;
}

.logo-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--sidebar-text);
}

.sidebar-theme {
  padding: 8px;
  margin-bottom: 4px;
}

.sidebar-theme :deep(.theme-switcher) {
  width: 100%;
}

.sidebar-theme :deep(.ts-option) {
  flex: 1;
  justify-content: center;
  padding: 7px 8px;
}

.sidebar-theme :deep(.ts-label) {
  display: none;
}

/* 欢迎区 */
.welcome-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 26px;
  gap: 16px;
  flex-wrap: wrap;
}

.welcome-bar h1 {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.welcome-sub {
  color: var(--text-muted);
  font-size: 13.5px;
  margin-top: 4px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--card);
  padding: 7px 14px 7px 7px;
  border-radius: 999px;
  box-shadow: var(--shadow-sm);
  font-size: 14px;
  font-weight: 600;
}

.avatar,
.avatar-img {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar {
  background: linear-gradient(135deg, var(--primary), #7aa5f0);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}

.role-chip {
  background: var(--bg-active);
  color: var(--primary-color);
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
}

/* 统计卡 */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}

.stat-card {
  background: var(--card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 18px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: box-shadow 0.2s, transform 0.2s;
}

.stat-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

.stat-label {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-muted);
}

.stat-value {
  font-size: 26px;
  font-weight: 800;
  margin-top: 4px;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.stat-foot {
  font-size: 11.5px;
  color: var(--text-muted);
  margin-top: 4px;
}

.stat-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon svg {
  width: 18px;
  height: 18px;
  fill: #fff;
}

.stat-icon.blue { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.stat-icon.green { background: linear-gradient(135deg, #22c55e, #16a34a); }
.stat-icon.amber { background: linear-gradient(135deg, #f59e0b, #d97706); }
.stat-icon.violet { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }

/* 快速入口 */
.quick-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 13px;
  background: var(--card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 16px 18px;
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.2s, transform 0.2s;
}

.quick-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

.q-emoji {
  font-size: 24px;
}

.quick-card b {
  font-size: 14.5px;
  font-weight: 700;
  display: block;
}

.quick-card span:not(.q-emoji):not(.q-arrow) {
  font-size: 12px;
  color: var(--text-muted);
}

.q-arrow {
  margin-left: auto;
  color: #c0c7d1;
  font-size: 15px;
}

/* 最近活动 */
.panel {
  background: var(--card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 22px;
  box-shadow: var(--shadow-sm);
}

.panel h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
}

.activity-list {
  display: flex;
  flex-direction: column;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 4px;
  border-bottom: 1px solid var(--border-light);
}

.activity-item:last-child {
  border-bottom: none;
}

.act-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  flex-shrink: 0;
}

.act-icon.ai { background: var(--bg-active); }
.act-icon.login { background: color-mix(in srgb, var(--success) 12%, transparent); }

.act-body {
  flex: 1;
}

.act-body b {
  font-size: 14px;
  font-weight: 600;
  display: block;
}

.act-time {
  font-size: 12px;
  color: var(--text-muted);
}

.act-detail {
  font-size: 12.5px;
  color: var(--text-muted);
  max-width: 40%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  padding: 26px 0;
}

.empty-state .muted {
  margin-bottom: 14px;
  font-size: 14px;
}

.btn.small {
  padding: 9px 20px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
}
</style>
