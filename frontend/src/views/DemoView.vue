<template>
  <div class="page">
    <SiteNav />
    <div class="page-inner">
      <header class="page-head">
        <span class="page-tag">DEMO LABORATORY</span>
        <h1>Demo 实验室</h1>
        <p>技术实验与组件展示，不断生长</p>
      </header>

      <div class="demo-grid">
        <div v-for="d in demos" :key="d.name" class="demo-card" :class="d.state">
          <div class="demo-icon">{{ d.icon }}</div>
          <b>{{ d.name }}</b>
          <span class="demo-desc">{{ d.desc }}</span>
          <span class="demo-state">{{ stateText(d.state) }}</span>
        </div>
      </div>

      <p class="hint">每个 Demo 都在规划中，随着平台迭代逐步开放。</p>
    </div>
  </div>
</template>

<script setup>
import SiteNav from '../components/SiteNav.vue'

const demos = [
  { icon: '💳', name: '支付 Demo', desc: '订单生成 · 支付流程 · 状态机', state: 'planned' },
  { icon: '🎬', name: '视频播放器', desc: '在线播放 · 媒体组件', state: 'planned' },
  { icon: '🎵', name: '音乐播放器', desc: '音频播放 · 播放列表', state: 'planned' },
  { icon: '🧠', name: 'AI 组件', desc: '对话式交互 · 流式输出', state: 'active' },
  { icon: '🧩', name: '交互组件', desc: 'UI 组件实验集合', state: 'planned' },
  { icon: '📈', name: '数据可视化', desc: '实时图表 · 数据曲线', state: 'planned' },
]

function stateText(s) {
  return s === 'active' ? '已上线' : '规划中'
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--bg-card);
}

.page-inner {
  max-width: 960px;
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
  color: #2b6de9;
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

.demo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
}

.demo-card {
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 28px 22px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
  transition: box-shadow 0.2s, transform 0.2s;
}

.demo-card:hover {
  box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08);
  transform: translateY(-3px);
}

.demo-card.active {
  border: 1px solid color-mix(in srgb, var(--success) 35%, transparent);
  background: color-mix(in srgb, var(--success) 8%, transparent);
}

.demo-icon {
  font-size: 34px;
}

.demo-card b {
  font-size: 16px;
}

.demo-desc {
  font-size: 13px;
  color: var(--text-muted);
}

.demo-state {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 999px;
  background: var(--bg-code);
  color: var(--text-muted);
}

.demo-card.active .demo-state {
  background: color-mix(in srgb, var(--success) 12%, transparent);
  color: var(--success);
}

.hint {
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
  margin-top: 40px;
}
</style>
