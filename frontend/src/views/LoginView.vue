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
      <label v-if="need2fa" class="field">
        <span>两步验证码</span>
        <input
          v-model.trim="form.totp_code"
          placeholder="6 位动态验证码"
          maxlength="8"
          required
          inputmode="numeric"
          autocomplete="one-time-code"
        />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" class="btn" :disabled="loading">
        {{ loading ? '登录中…' : need2fa ? '验证并登录' : '登 录' }}
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
      <label v-if="need2fa" class="field">
        <span>两步验证码</span>
        <input
          v-model.trim="form.totp_code"
          placeholder="6 位动态验证码"
          maxlength="8"
          required
          inputmode="numeric"
          autocomplete="one-time-code"
        />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="msg" class="success-msg">{{ msg }}</p>
      <button type="submit" class="btn" :disabled="loading">
        {{ loading ? '登录中…' : '验证码登录' }}
      </button>
      <p class="switch">还没有账号？<router-link to="/register">立即注册</router-link></p>
    </form>

    <!-- 第三方登录 -->
    <div v-if="oauthProviders.some((p) => p.provider === 'github' && p.enabled)" class="oauth-divider">
      <span>或</span>
    </div>
    <div v-if="oauthProviders.some((p) => p.provider === 'github' && p.enabled)" class="oauth-row">
      <a href="/api/v1/auth/oauth/github" class="oauth-btn">
        <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true">
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
        </svg>
        GitHub 登录
      </a>
    </div>
  </AuthLayout>
</template>

<script setup>
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import AuthLayout from '../layouts/AuthLayout.vue'

const router = useRouter()
const mode = ref('password')
const oauthProviders = ref([])

onMounted(async () => {
  try {
    const { data } = await api.get('/auth/oauth/providers')
    oauthProviders.value = data
  } catch { /* 忽略：未启用时按钮不显示 */ }
})
const form = reactive({ email: '', password: '', code: '', totp_code: '' })
const error = ref('')
const msg = ref('')
const need2fa = ref(false)
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
    const { data } = await api.post('/auth/login', {
      email: form.email,
      password: form.password,
      totp_code: need2fa.value ? form.totp_code : undefined,
    })
    saveSession(data)
  } catch (e) {
    if (e.response?.status === 428) {
      need2fa.value = true
      error.value = '该账号已开启两步验证，请输入动态验证码'
    } else {
      error.value = e.response?.data?.detail || '登录失败，请稍后重试'
    }
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
    const { data } = await api.post('/auth/login-code', {
      email: form.email,
      code: form.code,
      totp_code: need2fa.value ? form.totp_code : undefined,
    })
    saveSession(data)
  } catch (e) {
    if (e.response?.status === 428) {
      need2fa.value = true
      error.value = '该账号已开启两步验证，请输入动态验证码'
    } else {
      error.value = e.response?.data?.detail || '登录失败'
    }
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

/* 第三方登录 */
.oauth-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 18px 0 12px;
  color: var(--text-muted);
  font-size: 12px;
}

.oauth-divider::before,
.oauth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-color);
}

.oauth-row {
  display: flex;
  justify-content: center;
}

.oauth-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.15s;
}

.oauth-btn:hover {
  border-color: var(--text-secondary);
  background: var(--bg-hover);
}
</style>
