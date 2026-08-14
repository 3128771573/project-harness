<template>
  <div class="admin-shell">
    <!-- 侧边栏 -->
    <aside class="admin-sidebar">
      <div class="brand">
        <BrandLogo size="sm" />
        <div class="brand-text">
          <span class="brand-name">Harness</span>
          <span class="brand-sub">Admin Console</span>
        </div>
      </div>

      <nav class="admin-nav">
        <span class="nav-group">概览</span>
        <router-link to="/admin/dashboard" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>
          <span>仪表盘</span>
        </router-link>

        <span class="nav-group">管理</span>
        <router-link to="/admin/users" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
          <span>用户管理</span>
        </router-link>
        <router-link to="/admin/roles" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>
          <span>权限管理</span>
        </router-link>

        <span class="nav-group">AI</span>
        <router-link to="/admin/ai-config" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
          <span>AI 配置</span>
        </router-link>
        <router-link to="/admin/usage" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
          <span>用量统计</span>
        </router-link>

        <span class="nav-group">系统</span>
        <router-link to="/admin/system" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M19.14 12.94a7.07 7.07 0 000-1.88l2.03-1.58a.5.5 0 00.12-.64l-1.92-3.32a.5.5 0 00-.61-.22l-2.39.96a7.2 7.2 0 00-1.62-.94l-.36-2.54a.5.5 0 00-.5-.42h-3.84a.5.5 0 00-.5.42l-.36 2.54c-.59.24-1.13.56-1.62.94l-2.39-.96a.5.5 0 00-.61.22L2.74 8.84a.5.5 0 00.12.64l2.03 1.58a7.07 7.07 0 000 1.88l-2.03 1.58a.5.5 0 00-.12.64l1.92 3.32c.13.22.4.3.61.22l2.39-.96c.49.38 1.03.7 1.62.94l.36 2.54c.04.24.25.42.5.42h3.84c.25 0 .46-.18.5-.42l.36-2.54a7.2 7.2 0 001.62-.94l2.39.96c.22.08.48 0 .61-.22l1.92-3.32a.5.5 0 00-.12-.64l-2.03-1.58zM12 15.5A3.5 3.5 0 1112 8.5a3.5 3.5 0 010 7z"/></svg>
          <span>系统监控</span>
        </router-link>
        <router-link to="/admin/audit" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
          <span>日志审计</span>
        </router-link>
        <router-link to="/admin/security" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>
          <span>安全中心</span>
        </router-link>
        <router-link to="/admin/visits" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
          <span>访问记录</span>
        </router-link>
        <router-link to="/admin/settings" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 00.12-.61l-1.92-3.32a.49.49 0 00-.61-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 00-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.61.22L2.61 8.72c-.12.19-.07.45.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58a.49.49 0 00-.12.61l1.92 3.32c.12.22.37.29.61.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .61-.22l1.92-3.32a.49.49 0 00-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
          <span>系统设置</span>
        </router-link>
        <router-link to="/admin/notices" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M3 10v4h2l4 4V6L5 10H3zm12 1.5c0-2-1-3.7-2.5-4.5v9c1.5-.8 2.5-2.5 2.5-4.5zM9 3v18l4-3h4c1.1 0 2-.9 2-2v-8c0-1.1-.9-2-2-2h-4L9 3z"/></svg>
          <span>公告管理</span>
        </router-link>
        <router-link to="/admin/messages" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 12h-2v-2h2v2zm0-4h-2V7h2v3z"/></svg>
          <span>留言管理</span>
        </router-link>
        <router-link v-if="isSuperAdmin" to="/admin/watermark" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
          <span>水印取证</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <router-link to="/dashboard" class="back-link">
          <svg viewBox="0 0 24 24" class="icon"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
          <span>返回前台</span>
        </router-link>
        <router-link to="/status" class="back-link">
          <svg viewBox="0 0 24 24" class="icon"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
          <span>服务状态</span>
        </router-link>
        <button class="logout" @click="logout">
          <svg viewBox="0 0 24 24" class="icon"><path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5-5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg>
          <span>退出登录</span>
        </button>
      </div>
    </aside>

    <!-- 主内容 -->
    <div class="admin-main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '../components/BrandLogo.vue'

const router = useRouter()

const isSuperAdmin = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('harness_user') || 'null')
    return u?.role === 'super_admin'
  } catch {
    return false
  }
})

function logout() {
  localStorage.removeItem('harness_access')
  localStorage.removeItem('harness_refresh')
  localStorage.removeItem('harness_user')
  router.push('/')
}
</script>

<style scoped>
/* 深色主题：GitHub / Vercel Dashboard 风格 */
.admin-shell {
  display: flex;
  min-height: 100vh;
  background: var(--brand-block);
  color: var(--text-secondary);
}

/* ===== 侧边栏 ===== */
.admin-sidebar {
  width: 232px;
  flex-shrink: 0;
  background: var(--brand-block);
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  padding: 20px 14px;
  position: sticky;
  top: 0;
  height: 100vh;
  border-right: 1px solid var(--border-color);
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 4px 8px 24px;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: 15px;
  font-weight: 700;
  color: #fff;
}

.brand-sub {
  font-size: 10.5px;
  color: var(--text-muted);
  margin-top: 1px;
  letter-spacing: 0.03em;
}

.admin-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  overflow-y: auto;
}

.nav-group {
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 16px 12px 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 11px;
  color: var(--text-muted);
  padding: 9px 12px;
  border-radius: 9px;
  font-size: 13.5px;
  font-weight: 500;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}

.nav-item .icon {
  width: 17px;
  height: 17px;
  fill: currentColor;
  flex-shrink: 0;
}

.nav-item:hover {
  background: var(--sidebar-hover);
  color: var(--text-secondary);
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.25), rgba(124, 58, 237, 0.25));
  color: #fff;
  font-weight: 600;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-top: 14px;
  border-top: 1px solid var(--border-color);
}

.back-link {
  display: flex;
  align-items: center;
  gap: 11px;
  color: var(--text-muted);
  padding: 9px 12px;
  border-radius: 9px;
  font-size: 13px;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}

.back-link .icon {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

.back-link:hover {
  background: var(--sidebar-hover);
  color: var(--text-secondary);
}

.logout {
  display: flex;
  align-items: center;
  gap: 11px;
  color: var(--text-muted);
  background: transparent;
  border: none;
  padding: 9px 12px;
  border-radius: 9px;
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s;
}

.logout .icon {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

.logout:hover {
  background: rgba(220, 38, 38, 0.15);
  color: #fca5a5;
}

/* ===== 主内容 ===== */
.admin-main {
  flex: 1;
  padding: 30px 36px 44px;
  max-width: 1240px;
  min-width: 0;
  overflow-x: hidden;
}
</style>
