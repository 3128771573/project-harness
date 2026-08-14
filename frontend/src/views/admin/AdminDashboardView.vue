<template>
  <div>
    <header class="page-head">
      <div>
        <h1>仪表盘</h1>
        <p class="sub">平台数据总览</p>
      </div>
      <div class="actions">
        <button class="btn" @click="load">
          <svg viewBox="0 0 24 24" style="width:14px;height:14px;fill:currentColor"><path d="M17.65 6.35A7.95 7.95 0 0012 4a8 8 0 108 8h-2a6 6 0 11-1.76-4.24L13 11h7V4l-2.35 2.35z"/></svg>
          刷新
        </button>
      </div>
    </header>

    <section class="stat-grid">
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">用户总数</div>
          <div class="stat-value">{{ stats?.total_users ?? '—' }}</div>
        </div>
        <div class="stat-icon blue">
          <svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">今日新增</div>
          <div class="stat-value">{{ stats?.today_new_users ?? '—' }}</div>
        </div>
        <div class="stat-icon green">
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">AI 调用总数</div>
          <div class="stat-value">{{ stats?.total_ai_calls ?? '—' }}</div>
        </div>
        <div class="stat-icon violet">
          <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">今日 AI 调用</div>
          <div class="stat-value">{{ stats?.today_ai_calls ?? '—' }}</div>
        </div>
        <div class="stat-icon amber">
          <svg viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-title">系统状态</div>
      <p class="panel-sub">X230 宿主机运行情况</p>
      <p v-if="sysError" class="error-text">{{ sysError }}</p>
      <div v-else-if="sys" class="status-line">
        <span class="pulse-dot"></span>
        服务运行正常 · 已运行 {{ sys.uptime }}
      </div>
      <div v-else class="status-line muted">加载中…</div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../api/client'

const stats = ref(null)
const sys = ref(null)
const sysError = ref('')

async function load() {
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
}

onMounted(load)
</script>

<style scoped src="../../assets/admin.css"></style>
