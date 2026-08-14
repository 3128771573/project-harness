<template>
  <div>
    <header class="topbar">
      <h1>系统监控</h1>
      <button class="btn small" @click="load" :disabled="loading">刷新</button>
    </header>

    <section v-if="error" class="panel">
      <p class="error-text">{{ error }}</p>
    </section>

    <template v-else-if="sys">
      <section class="panel">
        <h3>资源使用率 <span class="muted small">(X230 宿主机)</span></h3>
        <div class="meter-row">
          <div class="meter-label">
            <span>CPU</span>
            <span class="mono">{{ sys.cpu }}%</span>
          </div>
          <div class="meter"><div class="meter-fill" :style="fillStyle(sys.cpu)"></div></div>
        </div>
        <div class="meter-row">
          <div class="meter-label">
            <span>内存 RAM</span>
            <span class="mono">{{ sys.memory }}%</span>
          </div>
          <div class="meter"><div class="meter-fill" :style="fillStyle(sys.memory)"></div></div>
        </div>
        <div class="meter-row">
          <div class="meter-label">
            <span>磁盘 Disk</span>
            <span class="mono">{{ sys.disk }}%</span>
          </div>
          <div class="meter"><div class="meter-fill" :style="fillStyle(sys.disk)"></div></div>
        </div>
      </section>

      <section class="panel">
        <h3>运行信息</h3>
        <ul class="status-list">
          <li><span class="dot ok"></span>系统运行时间：{{ sys.uptime }}</li>
          <li><span class="dot ok"></span>采样时间：{{ formatTime(sys.collected_at) }}</li>
        </ul>
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
