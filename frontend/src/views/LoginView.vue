<template>
  <AuthLayout title="欢迎回来" subtitle="登录 Harness Platform">
    <!-- 模式切换 -->
    <div class="mode-tabs">
      <button type="button" :class="['mode-tab', mode === 'password' ? 'active' : '']" @click="mode = 'password'">密码登录</button>
      <button type="button" :class="['mode-tab', mode === 'code' ? 'active' : '']" @click="mode = 'code'">验证码登录</button>
    </div>

    <!-- 密码登录 -->
    <form v-if="mode === 'password'" @submit.prevent="onSubmit" class="form">
      <label class="field">
        <span>邮箱</span>
        <input v-model.trim="form.email" type="email" placeholder="you@example.com" required autocomplete="email" />
      </label>
      <label class="field">
        <span>密码</span>
        <input v-model="form.password" type="password" placeholder="••••••••" required autocomplete="current-password" />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" class="btn" :disabled="loading">
        {{ loading ? '登录中…' : '登 录' }}
      </button>
      <p class="switch">
        <router-link to="/forgot" class="forgot-link">忘记密码？</router-link>
      </p>
    </form>

    <!-- 验证码登录 -->
    <form v-else @submit.prevent="onCodeSubmit" class="form">
      <label class="field">
        <span>邮箱</span>
        <div class="code-row">
          <input v-model.trim="form.email" type="email" placeholder="you@example.com" required autocomplete="email" />
          <button type="button" class="send-code-btn" :disabled="cooldown > 0 || sending" @click="sendCode">
            {{ sending ? '发送中…' : cooldown > 0 ? `${cooldown}s` : '获取验证码' }}
          </button>
        </div>
      </label>
      <label class="field">
        <span>验证码</span>
        <input v-model.trim="form.code" placeholder="6 位邮箱验证码" maxlength="8" required inputmode="numeric" />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="msg" class="success-msg">{{ msg }}</p>
      <button type="submit" class="btn" :disabled="loading">
        {{ loading ? '登录中…' : '验证码登录' }}
      </button>
      <p class="switch">还没有账号？<router-link to="/register">立即注册</router-link></p>
    </form>
  </AuthLayout>
</template>

<script setup>
import { onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import AuthLayout from '../layouts/AuthLayout.vue'

const router = useRouter()
const mode = ref('password')
const form = reactive({ email: '', password: '', code: '' })
const error = ref('')
const msg = ref('')
const loading = ref(false)
const sending = ref(false)
const cooldown = ref(0)
let timer = null

function saveSession(data) {
  localStorage.setItem('harness_access', data.access_token)
  localStorage.setItem('harness_refresh', data.refresh_token)
  localStorage.setItem('harness_user', JSON.stringify(data.user))
  router.push('/dashboard')
}

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/auth/login', { email: form.email, password: form.password })
    saveSession(data)
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function sendCode() {
  if (!form.email) {
    error.value = '请先填写邮箱'
    return
  }
  error.value = ''
  sending.value = true
  try {
    const { data } = await api.post('/auth/send-code', { email: form.email, purpose: 'login' })
    msg.value = data.message
    cooldown.value = data.cooldown || 60
    timer = setInterval(() => {
      cooldown.value -= 1
      if (cooldown.value <= 0) clearInterval(timer)
    }, 1000)
    if (data.dev_code) msg.value = `⚠️ 开发模式验证码：${data.dev_code}`
  } catch (e) {
    error.value = e.response?.data?.detail || '发送失败'
  } finally {
    sending.value = false
  }
}

async function onCodeSubmit() {
  error.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/auth/login-code', { email: form.email, code: form.code })
    saveSession(data)
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped src="../assets/auth.css"></style>
<style scoped>
.mode-tabs {
  display: flex;
  gap: 6px;
  background: var(--bg-secondary);
  border-radius: 999px;
  padding: 4px;
  margin-bottom: 22px;
}

.mode-tab {
  flex: 1;
  padding: 9px 12px;
  border: none;
  border-radius: 999px;
  background: transparent;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}

.mode-tab.active {
  background: var(--bg-card);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.code-row {
  display: flex;
  gap: 8px;
}

.code-row input {
  flex: 1;
  min-width: 0;
}

.send-code-btn {
  padding: 0 14px;
  border: 1px solid var(--primary-color);
  background: var(--bg-active);
  color: var(--primary-color);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  font-family: inherit;
  transition: all 0.15s;
}

.send-code-btn:hover:not(:disabled) {
  background: var(--primary-color);
  color: #fff;
}

.send-code-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.success-msg {
  color: var(--success);
  font-size: 13px;
  text-align: center;
  background: rgba(16, 185, 129, 0.08);
  padding: 9px 12px;
  border-radius: 8px;
}

.forgot-link {
  font-size: 13px;
}
</style>
