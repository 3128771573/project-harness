<template>
  <div class="maint-page">
    <div class="maint-card">
      <div class="maint-icon">🔧</div>
      <h1>系统维护中</h1>
      <p class="maint-msg">{{ message }}</p>
      <p class="maint-sub">我们正在升级服务，预计很快恢复。给您带来不便，敬请谅解。</p>
      <button class="btn" @click="refresh">刷新状态</button>
      <div class="maint-admin-entry" v-if="!isAdmin">
        <p>如果您是管理员，请先登录后再进入后台</p>
        <router-link to="/login" class="btn primary">管理员登录</router-link>
      </div>
      <p v-else class="maint-tip">您已以管理员身份登录，维护模式下可正常访问后台（系统设置中可关闭维护模式）</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

const message = ref('系统正在升级维护，请稍后再试。')

const isAdmin = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('harness_user') || 'null')
    return !!(u && ['admin', 'super_admin'].includes(u.role))
  } catch {
    return false
  }
})

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

.maint-admin-entry {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px dashed var(--border-color, #e5e7eb);
  font-size: 13px;
  color: var(--text-secondary, #555);
}

.maint-admin-entry p {
  margin: 0 0 10px;
}

.maint-admin-entry .btn {
  display: inline-block;
}
</style>
