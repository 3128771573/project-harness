<template>
  <div class="page">
    <SiteNav />
    <div class="page-inner">
      <header class="page-head">
        <span class="page-tag">IOT PLATFORM</span>
        <h1>IoT 设备平台</h1>
        <p>连接传感器与设备，构建智能应用</p>
      </header>

      <!-- 设备卡片 -->
      <div class="dev-grid">
        <div class="dev-card" v-for="d in devices" :key="d.name">
          <div class="dev-card-head">
            <span class="dev-type">{{ d.type }}</span>
            <span class="dev-status" :class="d.online ? 'on' : 'off'">
              <span class="st-dot"></span>{{ d.online ? 'Online' : 'Offline' }}
            </span>
          </div>
          <div class="dev-main">
            <span>{{ d.metric.label }}</span>
            <b>{{ d.metric.value }}<small>{{ d.metric.unit }}</small></b>
          </div>
          <div class="dev-foot">
            <span>ID: {{ d.id }}</span>
            <span>{{ d.lastSeen }}</span>
          </div>
        </div>
      </div>

      <!-- 实时曲线 -->
      <section class="chart-panel">
        <div class="chart-head">
          <div>
            <b>实时数据曲线</b>
            <span class="muted">温度传感器 · 最近 30 分钟</span>
          </div>
          <span class="live-tag">LIVE</span>
        </div>
        <svg viewBox="0 0 600 160" class="chart" preserveAspectRatio="none">
          <polyline :points="linePoints" fill="none" stroke="url(#lg2)" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
          <defs>
            <linearGradient id="lg2" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stop-color="#2563EB"/>
              <stop offset="1" stop-color="#7C3AED"/>
            </linearGradient>
          </defs>
        </svg>
        <div class="chart-axis">
          <span>30m</span><span>20m</span><span>10m</span><span>现在</span>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SiteNav from '../components/SiteNav.vue'

const devices = [
  { id: 'dev-001', type: '温度传感器', name: 'temp1', online: true, metric: { label: '温度', value: '26.5', unit: '℃' }, lastSeen: '刚刚' },
  { id: 'dev-002', type: '湿度传感器', name: 'humi1', online: true, metric: { label: '湿度', value: '60', unit: '%' }, lastSeen: '刚刚' },
  { id: 'dev-003', type: '气压传感器', name: 'press1', online: false, metric: { label: '气压', value: '—', unit: 'hPa' }, lastSeen: '2 小时前' },
]

// 模拟温度曲线
const linePoints = computed(() => {
  const pts = []
  for (let i = 0; i <= 40; i++) {
    const x = (i / 40) * 600
    const base = 80 + Math.sin(i / 4) * 18 + (i / 40) * 12
    pts.push(`${x.toFixed(1)},${base.toFixed(1)}`)
  }
  return pts.join(' ')
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--bg-card);
}

.page-inner {
  max-width: 1000px;
  margin: 0 auto;
  padding: 72px 28px;
}

.page-head {
  text-align: center;
  margin-bottom: 48px;
}

.page-tag {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: #059669;
}

.page-head h1 {
  font-size: 38px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 12px 0 10px;
}

.page-head p {
  color: var(--text-muted);
  font-size: 15px;
}

.dev-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
  margin-bottom: 28px;
}

.dev-card {
  background: var(--brand-block);
  border-radius: 18px;
  padding: 22px;
  color: #fff;
  transition: transform 0.2s, box-shadow 0.2s;
}

.dev-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 44px rgba(15, 23, 42, 0.28);
}

.dev-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.dev-type {
  font-size: 12.5px;
  color: var(--text-muted);
  font-weight: 600;
}

.dev-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
}

.dev-status.on {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.dev-status.off {
  background: rgba(148, 163, 184, 0.15);
  color: var(--text-muted);
}

.st-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.dev-status.on .st-dot {
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.25);
}

.dev-main {
  text-align: center;
  padding: 12px 0 18px;
}

.dev-main span {
  display: block;
  font-size: 12.5px;
  color: var(--text-muted);
}

.dev-main b {
  font-size: 40px;
  font-weight: 800;
}

.dev-main small {
  font-size: 15px;
  color: var(--text-muted);
  font-weight: 500;
}

.dev-foot {
  display: flex;
  justify-content: space-between;
  font-size: 11.5px;
  color: var(--text-muted);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 14px;
}

.chart-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
}

.chart-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-head b {
  font-size: 15px;
  font-weight: 700;
  display: block;
}

.chart-head .muted {
  font-size: 12.5px;
  color: var(--text-muted);
}

.live-tag {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: #dc2626;
  color: #fff;
  padding: 3px 8px;
  border-radius: 5px;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.chart {
  width: 100%;
  height: 160px;
  background:
    linear-gradient(rgba(15, 23, 42, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(15, 23, 42, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  border-radius: 10px;
}

.chart-axis {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 8px;
}
</style>
