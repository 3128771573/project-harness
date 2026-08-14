<template>
  <div>
    <header class="topbar">
      <h1>管理仪表盘</h1>
      <div class="user-chip">
        <span class="avatar">{{ avatarChar }}</span>
        <span>{{ user?.username }} ({{ user?.role }})</span>
      </div>
    </header>

    <section class="cards">
      <div class="card">
        <h3>用户总数</h3>
        <p class="big">{{ stats?.total_users ?? '—' }}</p>
      </div>
      <div class="card">
        <h3>今日新增</h3>
        <p class="big">{{ stats?.today_new_users ?? '—' }}</p>
      </div>
      <div class="card">
        <h3>AI 调用总数</h3>
        <p class="big">{{ stats?.total_ai_calls ?? '—' }}</p>
      </div>
      <div class="card">
        <h3>今日 AI 调用</h3>
        <p class="big">{{ stats?.today_ai_calls ?? '—' }}</p>
      </div>
    </section>

    <section class="panel">
      <h3>系统状态</h3>
      <p v-if="sysError" class="error-text">{{ sysError }}</p>
      <div v-else-if="sys" class="status-line">
        <span class="dot ok"></span> 服务运行正常 · uptime {{ sys.uptime }}
      </div>
      <div v-else class="status-line"><span class="dot soon"></span> 加载中…</div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../api/client'

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('harness_user') || 'null')
  } catch {
    return null
  }
})
const avatarChar = computed(() => (user.value?.username?.[0] || 'A').toUpperCase())
const stats = ref(null)
const sys = ref(null)
const sysError = ref('')

onMounted(async () => {
  try {
    const { data } = await api.get('/admin/stats')
    stats.value = data
  } catch (e) {
    sysError.value = e.response?.data?.detail || '统计加载失败'
  }
  try {
    const { data } = await api.get('/admin/system/status')
    sys.value = data
  } catch (e) {
    sysError.value = e.response?.data?.detail || '系统状态加载失败'
  }
})
</script>

<style scoped src="../../assets/admin.css"></style>
