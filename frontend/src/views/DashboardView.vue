<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">H</div>
      <nav>
        <a class="nav-item active">仪表盘</a>
        <a class="nav-item">AI 对话</a>
        <a class="nav-item">Demo 平台</a>
        <a class="nav-item">管理后台</a>
      </nav>
      <button class="logout" @click="logout">退出登录</button>
    </aside>

    <main class="main">
      <header class="topbar">
        <h1>仪表盘</h1>
        <div class="user-chip">
          <span class="avatar">{{ avatarChar }}</span>
          <span>{{ user?.nickname || user?.username }}</span>
        </div>
      </header>

      <section class="cards">
        <div class="card">
          <h3>UID</h3>
          <p class="big mono">{{ user?.uid }}</p>
        </div>
        <div class="card">
          <h3>用户名</h3>
          <p class="big">{{ user?.username }}</p>
        </div>
        <div class="card">
          <h3>邮箱</h3>
          <p class="big">{{ user?.email }}</p>
        </div>
        <div class="card">
          <h3>注册时间</h3>
          <p class="big">{{ formatTime(user?.created_time) }}</p>
        </div>
      </section>

      <section class="panel">
        <h3>Phase 1 状态</h3>
        <ul class="status-list">
          <li><span class="dot ok"></span>用户系统 v0.5（注册 / 登录 / UID）</li>
          <li><span class="dot soon"></span>AI 模块 —— 规划中</li>
          <li><span class="dot soon"></span>Demo 平台 —— 规划中</li>
          <li><span class="dot soon"></span>管理后台 —— 规划中</li>
        </ul>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('harness_user') || 'null')
  } catch {
    return null
  }
})

const avatarChar = computed(() => (user.value?.username?.[0] || 'U').toUpperCase())

function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

function logout() {
  localStorage.removeItem('harness_token')
  localStorage.removeItem('harness_user')
  router.push('/login')
}
</script>

<style scoped src="../assets/dashboard.css"></style>
