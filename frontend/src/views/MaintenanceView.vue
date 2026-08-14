<template>
  <div class="maint-page">
    <div class="maint-card">
      <div class="maint-icon">🔧</div>
      <h1>系统维护中</h1>
      <p class="maint-msg">{{ message }}</p>
      <p class="maint-sub">我们正在升级服务，预计很快恢复。给您带来不便，敬请谅解。</p>
      <button class="btn" @click="refresh">刷新状态</button>
      <p class="maint-tip">管理员可在维护结束后正常访问后台（无需拦截）</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const message = ref('系统正在升级维护，请稍后再试。')

async function refresh() {
  try {
    const resp = await fetch('/api/v1/public/maintenance')
    const d = await resp.json()
    message.value = d.message || message.value
    if (!d.maintenance) {
      window.location.href = '/'
    }
  } catch {
    /* ignore */
  }
}

onMounted(refresh)
</script>

<style scoped>
.maint-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card, #fff);
  padding: 24px;
}

.maint-card {
  text-align: center;
  max-width: 460px;
}

.maint-icon {
  font-size: 56px;
  margin-bottom: 16px;
  animation: spin 6s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.maint-card h1 {
  font-size: 24px;
  margin: 0 0 12px;
  color: var(--text-primary, #111);
}

.maint-msg {
  font-size: 15px;
  color: var(--text-secondary, #555);
  line-height: 1.7;
  margin: 0 0 8px;
}

.maint-sub {
  font-size: 13px;
  color: var(--text-muted, #888);
  margin: 0 0 20px;
}

.maint-tip {
  margin-top: 18px;
  font-size: 12px;
  color: var(--text-muted, #aaa);
}
</style>
