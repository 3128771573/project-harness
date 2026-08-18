<template>
  <header class="site-nav">
    <div class="nav-inner">
      <router-link to="/" class="brand">
        <BrandLogo size="sm" />
        <span class="brand-name">Harness</span>
      </router-link>

      <nav class="nav-links" :class="{ open: navOpen }">
        <router-link to="/ai" class="nav-link">AI</router-link>
        <router-link to="/iot" class="nav-link">IoT</router-link>
        <router-link to="/docs" class="nav-link">Docs</router-link>
        <router-link to="/pricing" class="nav-link">定价</router-link>
        <router-link to="/guestbook" class="nav-link">留言</router-link>
      </nav>

      <!-- 移动端汉堡菜单 -->
      <button class="hamburger" :class="{ open: navOpen }" @click="navOpen = !navOpen" aria-label="菜单">
        <span></span><span></span><span></span>
      </button>

      <!-- 未登录 -->
      <div v-if="!user" class="nav-actions">
        <router-link to="/login" class="btn ghost sm">登录</router-link>
        <router-link to="/register" class="btn primary sm">注册</router-link>
      </div>

      <!-- 已登录 -->
      <div v-else class="nav-actions user-area">
        <!-- 私信入口（未读角标） -->
        <router-link to="/messages" class="bell-btn im-btn" aria-label="私信">
          <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
          <span v-if="imUnread > 0" class="bell-dot">{{ imUnread > 99 ? '99+' : imUnread }}</span>
        </router-link>
        <!-- 公告铃铛 -->
        <div class="bell-wrap">
          <button class="bell-btn" :class="{ open: bellOpen }" @click="bellOpen = !bellOpen" aria-label="公告">
            <svg viewBox="0 0 24 24"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>
            <span v-if="unreadCount > 0" class="bell-dot">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
          </button>
          <div v-if="bellOpen" class="bell-menu">
            <div class="bell-head">
              <span>公告</span>
              <button class="bell-read" @click="markAllRead">全部已读</button>
            </div>
            <div v-if="notices.length === 0" class="bell-empty">暂无公告</div>
            <div
              v-for="n in notices"
              :key="n.id"
              class="bell-item"
              :class="{ open: openNoticeId === n.id }"
              @click="openNoticeId = openNoticeId === n.id ? null : n.id"
            >
              <b>{{ n.title }}</b>
              <span class="bell-time">{{ fmtNoticeDate(n.published_at) }}</span>
              <p v-if="openNoticeId === n.id" class="bell-content">{{ n.content }}</p>
            </div>
          </div>
        </div>
        <button class="user-chip" @click="menuOpen = !menuOpen">
          <img v-if="user.avatar" :src="user.avatar" class="chip-avatar" alt="" />
          <span v-else class="chip-avatar">{{ initial }}</span>
          <span class="chip-name">{{ user.nickname || user.username }}</span>
          <svg viewBox="0 0 24 24" class="chev" :class="{ open: menuOpen }"><path d="M7 10l5 5 5-5z"/></svg>
        </button>
        <div v-if="menuOpen" class="user-menu" @click="menuOpen = false">
          <router-link to="/dashboard" class="menu-item">
            <svg viewBox="0 0 24 24"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>
            个人中心
          </router-link>
          <router-link to="/ai" class="menu-item">
            <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
            我的 AI
          </router-link>
          <router-link to="/messages" class="menu-item">
            <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
            我的私信
            <span v-if="imUnread > 0" class="menu-badge">{{ imUnread > 99 ? '99+' : imUnread }}</span>
          </router-link>
          <router-link to="/settings" class="menu-item">
            <svg viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 00.12-.61l-1.92-3.32a.49.49 0 00-.61-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 00-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.61.22L2.61 8.72c-.12.19-.07.45.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58a.49.49 0 00-.12.61l1.92 3.32c.12.22.37.29.61.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .61-.22l1.92-3.32a.49.49 0 00-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
            设置
          </router-link>
          <router-link v-if="isAdmin" to="/admin/dashboard" class="menu-item">
            <svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
            管理后台
          </router-link>
          <div class="menu-divider"></div>
          <button class="menu-item danger" @click="logout">
            <svg viewBox="0 0 24 24"><path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5-5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg>
            退出登录
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import BrandLogo from './BrandLogo.vue'

const router = useRouter()
const menuOpen = ref(false)
const navOpen = ref(false)

// ===== 私信未读角标（30s 轮询） =====
const imUnread = ref(0)
let imTimer = null

async function refreshImUnread() {
  if (!localStorage.getItem('harness_access')) return
  try {
    const { data } = await api.get('/im/unread')
    imUnread.value = data.total || 0
  } catch {
    /* ignore */
  }
}

// ===== 公告铃铛 =====
const bellOpen = ref(false)
const notices = ref([])
const openNoticeId = ref(null)
const lastReadAt = ref(0)

const unreadCount = computed(() =>
  notices.value.filter((n) => new Date(n.published_at).getTime() > lastReadAt.value).length
)

function fmtNoticeDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

function markAllRead() {
  lastReadAt.value = Date.now()
  try {
    localStorage.setItem('harness_notice_read_at', String(lastReadAt.value))
  } catch { /* ignore */ }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/public/notices')
    notices.value = data.items || []
    lastReadAt.value = Number(localStorage.getItem('harness_notice_read_at') || 0)
  } catch { /* ignore */ }
  refreshImUnread()
  imTimer = setInterval(refreshImUnread, 30000)
})

onUnmounted(() => {
  clearInterval(imTimer)
})

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('harness_user') || 'null')
  } catch {
    return null
  }
})

const initial = computed(() => (user.value?.username?.[0] || 'U').toUpperCase())

const isAdmin = computed(() => ['admin', 'super_admin'].includes(user.value?.role))

async function logout() {
  const { logoutSession } = await import('../utils/session')
  await logoutSession()
  router.push('/')
}
</script>

<style scoped>
.site-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--nav-bg, rgba(255, 255, 255, 0.82));
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border-color);
}

.nav-inner {
  max-width: 1120px;
  margin: 0 auto;
  padding: 0 28px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.brand-logo {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: linear-gradient(135deg, #2b6de9, #7aa5f0);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
}

.brand-name {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.nav-links {
  display: flex;
  gap: 30px;
  margin-left: 48px;
  flex: 1;
}

.nav-link {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.15s;
}

.nav-link:hover {
  color: var(--text-primary);
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.btn.sm {
  padding: 8px 16px;
}

.btn.primary {
  background: var(--text-primary);
  color: var(--text-inverse);
}

.btn.primary:hover {
  opacity: 0.85;
}

.btn.ghost {
  background: transparent;
  color: var(--text-secondary);
  border-color: var(--border-color);
}

.btn.ghost:hover {
  background: var(--bg-hover);
}

/* 已登录用户区 */
.user-area {
  position: relative;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 9px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 5px 10px 5px 5px;
  border-radius: 999px;
  font-family: inherit;
  transition: background 0.15s;
}

.user-chip:hover {
  background: var(--bg-hover);
}

.chip-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--gradient-brand);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  object-fit: cover;
}

.chip-name {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-primary);
}

.chev {
  width: 16px;
  height: 16px;
  fill: var(--text-muted);
  transition: transform 0.2s;
}

.chev.open {
  transform: rotate(180deg);
}

.user-menu {
  position: absolute;
  top: 46px;
  right: 0;
  min-width: 200px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  box-shadow: var(--shadow-lg);
  padding: 6px;
  z-index: 200;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 9px;
  border: none;
  background: transparent;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  text-align: left;
  text-decoration: none;
  font-family: inherit;
  transition: background 0.12s;
}

.menu-item svg {
  width: 16px;
  height: 16px;
  fill: var(--text-muted);
}

.menu-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.menu-item.danger {
  color: var(--error);
}

.menu-item.danger svg {
  fill: var(--error);
}

.menu-item.danger:hover {
  background: rgba(220, 38, 38, 0.08);
}

.menu-divider {
  height: 1px;
  background: var(--border-color);
  margin: 5px 4px;
}

/* 移动端汉堡按钮 */
.hamburger {
  display: none;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  width: 36px;
  height: 36px;
  padding: 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  flex-shrink: 0;
}

.hamburger span {
  display: block;
  height: 2px;
  border-radius: 2px;
  background: var(--text-primary);
  transition: transform 0.2s, opacity 0.2s;
}

.hamburger.open span:nth-child(1) { transform: translateY(6px) rotate(45deg); }
.hamburger.open span:nth-child(2) { opacity: 0; }
.hamburger.open span:nth-child(3) { transform: translateY(-6px) rotate(-45deg); }

/* 公告铃铛 */
.bell-wrap {
  position: relative;
}

.bell-btn {
  position: relative;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
  text-decoration: none;
}

.bell-btn:hover {
  background: var(--bg-hover);
}

.bell-btn svg {
  width: 18px;
  height: 18px;
  fill: var(--text-secondary);
}

.bell-btn.open svg {
  fill: var(--primary);
}

.menu-badge {
  margin-left: auto;
  background: var(--error, #e5484d);
  color: #fff;
  font-size: 11px;
  border-radius: 10px;
  padding: 1px 7px;
}

.bell-dot {
  position: absolute;
  top: 3px;
  right: 3px;
  min-width: 15px;
  height: 15px;
  padding: 0 3px;
  border-radius: 999px;
  background: var(--error);
  color: #fff;
  font-size: 9.5px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.bell-menu {
  position: absolute;
  top: 44px;
  right: 0;
  width: 300px;
  max-height: 380px;
  overflow-y: auto;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  box-shadow: var(--shadow-lg);
  z-index: 200;
  padding: 6px;
}

.bell-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}

.bell-read {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 12px;
  color: var(--primary);
  font-family: inherit;
}

.bell-read:hover {
  text-decoration: underline;
}

.bell-empty {
  padding: 14px 10px;
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
}

.bell-item {
  padding: 10px 12px;
  border-radius: 9px;
  cursor: pointer;
}

.bell-item:hover {
  background: var(--bg-hover);
}

.bell-item b {
  display: block;
  font-size: 13px;
  color: var(--text-primary);
}

.bell-time {
  font-size: 11px;
  color: var(--text-muted);
}

.bell-content {
  margin: 6px 0 0;
  font-size: 12.5px;
  color: var(--text-secondary);
  white-space: pre-line;
  line-height: 1.6;
}

@media (max-width: 700px) {
  .hamburger {
    display: inline-flex;
  }

  .nav-links {
    display: none;
    position: absolute;
    top: 60px;
    left: 0;
    right: 0;
    flex-direction: column;
    gap: 2px;
    margin-left: 0;
    padding: 10px 28px 14px;
    background: var(--nav-bg, rgba(255, 255, 255, 0.95));
    backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--border-color);
    box-shadow: var(--shadow);
  }

  .nav-links.open {
    display: flex;
  }

  .nav-link {
    padding: 9px 0;
    font-size: 15px;
  }

  .chip-name {
    display: none;
  }
}
</style>
