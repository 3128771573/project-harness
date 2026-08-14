<template>
  <div class="admin-shell">
    <!-- 侧边栏 -->
    <aside class="admin-sidebar">
      <div class="brand">
        <div class="brand-logo">H</div>
        <div class="brand-text">
          <span class="brand-name">Harness</span>
          <span class="brand-sub">管理控制台</span>
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
        <router-link to="/admin/system" class="nav-item" active-class="active">
          <svg viewBox="0 0 24 24" class="icon"><path d="M19.14 12.94a7.07 7.07 0 000-1.88l2.03-1.58a.5.5 0 00.12-.64l-1.92-3.32a.5.5 0 00-.61-.22l-2.39.96a7.2 7.2 0 00-1.62-.94l-.36-2.54a.5.5 0 00-.5-.42h-3.84a.5.5 0 00-.5.42l-.36 2.54c-.59.24-1.13.56-1.62.94l-2.39-.96a.5.5 0 00-.61.22L2.74 8.84a.5.5 0 00.12.64l2.03 1.58a7.07 7.07 0 000 1.88l-2.03 1.58a.5.5 0 00-.12.64l1.92 3.32c.13.22.4.3.61.22l2.39-.96c.49.38 1.03.7 1.62.94l.36 2.54c.04.24.25.42.5.42h3.84c.25 0 .46-.18.5-.42l.36-2.54a7.2 7.2 0 001.62-.94l2.39.96c.22.08.48 0 .61-.22l1.92-3.32a.5.5 0 00-.12-.64l-2.03-1.58zM12 15.5A3.5 3.5 0 1112 8.5a3.5 3.5 0 010 7z"/></svg>
          <span>系统监控</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <router-link to="/dashboard" class="back-link">
          <svg viewBox="0 0 24 24" class="icon"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
          <span>返回前台</span>
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
import { useRouter } from 'vue-router'

const router = useRouter()

function logout() {
  localStorage.removeItem('harness_access')
  localStorage.removeItem('harness_refresh')
  localStorage.removeItem('harness_user')
  router.push('/login')
}
</script>

<style scoped>
.admin-shell {
  display: flex;
  min-height: 100vh;
  background: #f4f5f9;
}

/* ===== 侧边栏 ===== */
.admin-sidebar {
  width: 232px;
  flex-shrink: 0;
  background: #171a23;
  color: #fff;
  display: flex;
  flex-direction: column;
  padding: 20px 14px;
  position: sticky;
  top: 0;
  height: 100vh;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 8px 22px;
}

.brand-logo {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: linear-gradient(135deg, #4f7cf7, #7aa5f0);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 19px;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(79, 124, 247, 0.35);
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-name {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.brand-sub {
  font-size: 11px;
  color: #8b93a7;
  margin-top: 2px;
}

.admin-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.nav-group {
  color: #6b7280;
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
  color: #9aa3b5;
  padding: 10px 12px;
  border-radius: 9px;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}

.nav-item .icon {
  width: 18px;
  height: 18px;
  fill: currentColor;
  flex-shrink: 0;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #e8eaf0;
}

.nav-item.active {
  background: #2b6de9;
  color: #fff;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(43, 109, 233, 0.4);
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
}

.back-link {
  display: flex;
  align-items: center;
  gap: 11px;
  color: #8b93a7;
  padding: 10px 12px;
  border-radius: 9px;
  font-size: 13px;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}

.back-link .icon {
  width: 17px;
  height: 17px;
  fill: currentColor;
}

.back-link:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #d5d9e3;
}

.logout {
  display: flex;
  align-items: center;
  gap: 11px;
  color: #8b93a7;
  background: transparent;
  border: none;
  padding: 10px 12px;
  border-radius: 9px;
  font-size: 13px;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s;
}

.logout .icon {
  width: 17px;
  height: 17px;
  fill: currentColor;
}

.logout:hover {
  background: rgba(220, 38, 38, 0.15);
  color: #ff9b9b;
}

/* ===== 主内容 ===== */
.admin-main {
  flex: 1;
  padding: 28px 36px 40px;
  max-width: 1200px;
  min-width: 0;
}
</style>
