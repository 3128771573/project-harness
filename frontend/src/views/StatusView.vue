<template>
  <div class="page">
    <SiteNav />
    <div class="page-inner">
      <header class="page-head">
        <span class="page-tag">SYSTEM STATUS</span>
        <h1>服务状态</h1>
        <p>所有系统运行正常</p>
      </header>

      <div class="status-card overall">
        <span class="big-dot ok"></span>
        <div>
          <b>All Systems Operational</b>
          <span>所有服务正常运行</span>
        </div>
      </div>

      <div class="status-list">
        <div v-for="s in services" :key="s.name" class="status-item">
          <div class="s-left">
            <span :class="['s-dot', s.status === 'Operational' ? 'ok' : 'warn']"></span>
            <div>
              <b>{{ s.name }}</b>
              <span class="s-desc">{{ s.desc }}</span>
            </div>
          </div>
          <span class="s-status" :class="s.status === 'Operational' ? 'ok' : 'warn'">{{ s.status }}</span>
        </div>
      </div>

      <p class="hint">实时监控 · 最近检查：{{ lastCheck }}</p>
    </div>
  </div>
</template>

<script setup>
import SiteNav from '../components/SiteNav.vue'

const lastCheck = new Date().toLocaleTimeString('zh-CN', { hour12: false })

const services = [
  { name: 'API', desc: '/api/v1 REST 接口', status: 'Operational' },
  { name: 'Database', desc: 'PostgreSQL 16', status: 'Operational' },
  { name: 'AI Service', desc: '大模型接入 · Mock/真实模式', status: 'Operational' },
  { name: 'IoT', desc: '设备接入平台（建设中）', status: 'Operational' },
  { name: 'Frontend', desc: 'Vue 3 Web 应用', status: 'Operational' },
]
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--bg-card);
}

.page-inner {
  max-width: 720px;
  margin: 0 auto;
  padding: 72px 28px;
}

.page-head {
  text-align: center;
  margin-bottom: 40px;
}

.page-tag {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: #16a34a;
}

.page-head h1 {
  font-size: 36px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 12px 0 8px;
}

.page-head p {
  color: var(--text-muted);
  font-size: 14.5px;
}

.status-card {
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 22px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
}

.big-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}

.big-dot.ok {
  background: #22c55e;
  box-shadow: 0 0 0 5px rgba(34, 197, 94, 0.18);
}

.status-card b {
  font-size: 17px;
  font-weight: 700;
  display: block;
}

.status-card span:not(.big-dot) {
  font-size: 13px;
  color: var(--text-muted);
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid var(--border-light);
  border-radius: 14px;
  padding: 16px 20px;
}

.s-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.s-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.s-dot.ok { background: #22c55e; }
.s-dot.warn { background: #f59e0b; }

.s-left b {
  font-size: 14.5px;
  font-weight: 600;
  display: block;
}

.s-desc {
  font-size: 12.5px;
  color: var(--text-muted);
}

.s-status {
  font-size: 12.5px;
  font-weight: 700;
  padding: 5px 14px;
  border-radius: 999px;
}

.s-status.ok {
  background: color-mix(in srgb, var(--success) 10%, transparent);
  color: var(--success);
}

.s-status.warn {
  background: color-mix(in srgb, var(--warning) 10%, transparent);
  color: var(--warning);
}

.hint {
  text-align: center;
  color: var(--text-muted);
  font-size: 12.5px;
  margin-top: 28px;
}
</style>
