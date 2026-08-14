<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">H</div>
      <div class="sidebar-label">管理控制台</div>
      <nav>
        <router-link to="/admin/dashboard" class="nav-item">仪表盘</router-link>
        <router-link to="/admin/users" class="nav-item">用户管理</router-link>
        <router-link to="/admin/system" class="nav-item">系统监控</router-link>
      </nav>
      <div class="sidebar-spacer"></div>
      <router-link to="/dashboard" class="nav-item back-link">← 返回前台</router-link>
      <button class="logout" @click="logout">退出登录</button>
    </aside>

    <main class="main">
      <router-view />
    </main>
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
.sidebar-label {
  color: #7d8496;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 0 14px 10px;
}

.sidebar-spacer {
  flex: 1;
}

.back-link {
  font-size: 13px;
  color: #8fa0c9;
}
</style>
