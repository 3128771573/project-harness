<template>
  <div class="maint-page">
    <div class="maint-card">
      <div class="maint-icon">{{ icon }}</div>
      <h1>{{ title }}</h1>
      <p class="maint-msg">{{ message }}</p>
      <p class="maint-sub" v-if="mode === 'block_new'">已登录用户可以正常访问，无需操作</p>
      <p class="maint-sub" v-else-if="mode === 'admin_only'">当前仅管理员可访问</p>
      <p class="maint-sub" v-else>我们正在升级服务，给您带来不便，敬请谅解。</p>
      <div v-if="countdown > 0" class="countdown">
        <span>预计恢复倒计时</span>
        <b class="mono">{{ cdText }}</b>
      </div>
      <button class="btn" @click="refresh">刷新状态</button>
      <div class="maint-admin-entry" v-if="!isAdmin">
        <p>如果您是管理员，请先登录后再进入后台</p>
        <router-link to="/login" class="btn primary">管理员登录</router-link>
      </div>
      <p v-else class="maint-tip">您已以管理员身份登录，维护模式下可正常访问后台（维护模式管理可关闭）</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const mode = ref('full')
const message = ref('系统正在升级维护，请稍后再试。')
const autoCloseAt = ref('')
let countdown = ref(0)
let timer = null

const icon = computed(() => ({ full: '🔧', block_new: '🚪', scheduled: '⏰', admin_only: '🔒' })[mode.value] || '🔧')
const title = computed(() => ({ full: '系统维护中', block_new: '站内调整中', scheduled: '定时维护中', admin_only: '仅管理员访问' })[mode.value] || '系统维护中')
const cdText = computed(() => {
  const s = Math.max(0, countdown.value)
  const pad = (x) => String(x).padStart(2, '0')
  return pad(Math.floor(s / 3600)) + ':' + pad(Math.floor((s % 3600) / 60)) + ':' + pad(s % 60)
})

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
    mode.value = d.mode || 'full'
    message.value = d.reason || d.message || message.value
    autoCloseAt.value = d.auto_close_at || ''
    if (!d.maintenance) {
      window.location.href = '/'
      return
    }
    updateCountdown()
    if (autoCloseAt.value) {
      clearInterval(timer)
      timer = setInterval(updateCountdown, 1000)
    }
  } catch {
    /* ignore */
  }
}

function updateCountdown() {
  if (!autoCloseAt.value) {
    countdown.value = 0
    return
  }
  countdown.value = Math.max(0, Math.floor((new Date(autoCloseAt.value).getTime() - Date.now()) / 1000))
}

onMounted(() => {
  refresh()
  clearInterval(timer)
  timer = setInterval(() => {
    if (!autoCloseAt.value) refresh()
  }, 30000)
})

onUnmounted(() => clearInterval(timer))
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
  max-width: 480px;
}

.maint-icon {
  font-size: 56px;
  margin-bottom: 16px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
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

.countdown {
  margin: 0 0 20px;
  padding: 12px 16px;
  border: 1px dashed var(--border-color, #e5e7eb);
  border-radius: 12px;
  display: inline-block;
}

.countdown span {
  display: block;
  font-size: 12px;
  color: var(--text-muted, #888);
  margin-bottom: 4px;
}

.countdown b {
  font-size: 24px;
  color: var(--primary-color, #2b6de9);
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

.mono {
  font-family: var(--font-mono, ui-monospace, monospace);
}
</style>
