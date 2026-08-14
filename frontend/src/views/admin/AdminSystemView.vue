<template>
  <div>
    <header class="page-head">
      <div>
        <h1>系统监控</h1>
        <p class="sub">X230 宿主机资源实时状态</p>
      </div>
      <div class="actions">
        <button class="btn" :disabled="loading" @click="load">
          <svg viewBox="0 0 24 24" style="width:14px;height:14px;fill:currentColor"><path d="M17.65 6.35A7.95 7.95 0 0012 4a8 8 0 108 8h-2a6 6 0 11-1.76-4.24L13 11h7V4l-2.35 2.35z"/></svg>
          {{ loading ? '刷新中…' : '刷新' }}
        </button>
      </div>
    </header>

    <div v-if="error" class="panel">
      <p class="error-text">{{ error }}</p>
    </div>

    <template v-else-if="sys">
      <section class="panel">
        <div class="panel-title">资源使用率</div>
        <p class="panel-sub">上次采样：{{ formatTime(sys.collected_at) }}</p>

        <div class="meter-row">
          <div class="meter-label">
            <span class="meter-name">CPU</span>
            <span class="meter-val">{{ sys.cpu }}%</span>
          </div>
          <div class="meter"><div class="meter-fill" :style="fillStyle(sys.cpu)"></div></div>
        </div>

        <div class="meter-row">
          <div class="meter-label">
            <span class="meter-name">内存 RAM</span>
            <span class="meter-val">{{ sys.memory }}%</span>
          </div>
          <div class="meter"><div class="meter-fill" :style="fillStyle(sys.memory)"></div></div>
        </div>

        <div class="meter-row">
          <div class="meter-label">
            <span class="meter-name">磁盘 Disk</span>
            <span class="meter-val">{{ sys.disk }}%</span>
          </div>
          <div class="meter"><div class="meter-fill" :style="fillStyle(sys.disk)"></div></div>
        </div>
      </section>

      <section class="stat-grid" style="grid-template-columns: repeat(3, 1fr)">
        <div class="stat-card">
          <div class="stat-info">
            <div class="stat-label">运行时长</div>
            <div class="stat-value" style="font-size:18px">{{ sys.uptime }}</div>
          </div>
          <div class="stat-icon blue">
            <svg viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-info">
            <div class="stat-label">服务状态</div>
            <div class="stat-value" style="font-size:18px">
              <span class="status-line"><span class="pulse-dot"></span> 正常</span>
            </div>
          </div>
          <div class="stat-icon green">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-info">
            <div class="stat-label">数据来源</div>
            <div class="stat-value" style="font-size:18px">/proc 实时</div>
          </div>
          <div class="stat-icon amber">
            <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
          </div>
        </div>
      </section>
    </template>

    <section v-else class="panel"><p class="muted">加载中…</p></section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../../api/client'

const sys = ref(null)
const error = ref('')
const loading = ref(false)

function fillStyle(pct) {
  const color = pct >= 85 ? '#dc2626' : pct >= 60 ? '#d97706' : '#16a34a'
  return { width: Math.min(100, pct) + '%', background: color }
}

function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/admin/system/status')
    sys.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '系统监控加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped src="../../assets/admin.css"></style>
