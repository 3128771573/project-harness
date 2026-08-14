<template>
  <header class="site-nav">
    <div class="nav-inner">
      <router-link to="/" class="brand">
        <div class="brand-logo">H</div>
        <span class="brand-name">Harness</span>
      </router-link>

      <nav class="nav-links">
        <router-link to="/ai" class="nav-link">AI</router-link>
        <router-link to="/demo" class="nav-link">Demo</router-link>
        <router-link to="/iot" class="nav-link">IoT</router-link>
        <router-link to="/docs" class="nav-link">Docs</router-link>
      </nav>

      <!-- 未登录 -->
      <div v-if="!user" class="nav-actions">
        <router-link to="/login" class="btn ghost sm">登录</router-link>
        <router-link to="/register" class="btn primary sm">注册</router-link>
      </div>

      <!-- 已登录 -->
      <div v-else class="nav-actions user-area">
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
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const menuOpen = ref(false)

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('harness_user') || 'null')
  } catch {
    return null
  }
})

const initial = computed(() => (user.value?.username?.[0] || 'U').toUpperCase())

const isAdmin = computed(() => ['admin', 'super_admin'].includes(user.value?.role))

function logout() {
  localStorage.removeItem('harness_access')
  localStorage.removeItem('harness_refresh')
  localStorage.removeItem('harness_user')
  router.push('/')
}
</script>

<style scoped>
.site-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
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
  color: #111827;
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
  color: #4b5563;
  text-decoration: none;
  transition: color 0.15s;
}

.nav-link:hover {
  color: #111827;
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
  background: #111827;
  color: #fff;
}

.btn.primary:hover {
  background: #1f2937;
}

.btn.ghost {
  background: transparent;
  color: #374151;
  border-color: #e5e7eb;
}

.btn.ghost:hover {
  background: #f8f9fc;
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
  background: #f3f4f6;
}

.chip-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2b6de9, #7aa5f0);
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
  color: #111827;
}

.chev {
  width: 16px;
  height: 16px;
  fill: #6b7280;
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
  background: #fff;
  border: 1px solid #eef0f5;
  border-radius: 14px;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.12);
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
  color: #374151;
  cursor: pointer;
  text-align: left;
  text-decoration: none;
  font-family: inherit;
  transition: background 0.12s;
}

.menu-item svg {
  width: 16px;
  height: 16px;
  fill: #6b7280;
}

.menu-item:hover {
  background: #f8f9fc;
  color: #111827;
}

.menu-item.danger {
  color: #dc2626;
}

.menu-item.danger svg {
  fill: #dc2626;
}

.menu-item.danger:hover {
  background: #fef2f2;
}

.menu-divider {
  height: 1px;
  background: #f0f1f5;
  margin: 5px 4px;
}

@media (max-width: 700px) {
  .nav-links {
    display: none;
  }
  .chip-name {
    display: none;
  }
}
</style>
