<template>
  <div class="oauth-page">
    <div class="oauth-card">
      <template v-if="error">
        <p class="oauth-emoji">⚠️</p>
        <h1>登录未完成</h1>
        <p class="oauth-sub">{{ errorText }}</p>
        <router-link to="/login" class="oauth-link">返回登录</router-link>
      </template>
      <template v-else-if="need2fa">
        <p class="oauth-emoji">🔐</p>
        <h1>两步验证</h1>
        <p class="oauth-sub">该账号已开启两步验证，请输入动态验证码</p>
        <form @submit.prevent="submit(true)" class="form">
          <label class="field">
            <span>动态验证码</span>
            <input v-model.trim="totpCode" placeholder="6 位动态验证码" maxlength="8" required inputmode="numeric" />
          </label>
          <p v-if="msg" class="oauth-err">{{ msg }}</p>
          <button type="submit" class="btn" :disabled="loading">{{ loading ? '验证中…' : '验证并登录' }}</button>
        </form>
      </template>
      <template v-else>
        <p class="oauth-emoji">⏳</p>
        <h1>正在登录…</h1>
        <p class="oauth-sub">请稍候，正在为您建立会话</p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'
import { saveSession } from '../utils/session'

const route = useRoute()
const router = useRouter()
const error = ref('')
const need2fa = ref(false)
const loading = ref(false)
const totpCode = ref('')
const msg = ref('')

const errorText =
  {
    denied: '您取消了 GitHub 授权',
    invalid: '登录参数无效，请重新尝试',
    state: '安全校验未通过，请重新尝试',
    token: '获取授权令牌失败，请重试',
    userinfo: '获取用户信息失败，请重试',
    disabled: '该账号已被禁用',
  }[route.query.error] || (route.query.error ? '登录失败，请重试' : '')

onMounted(() => {
  if (route.query.error) return
  submit(false)
})

async function submit(withTotp) {
  const code = route.query.code
  if (!code) {
    error.value = '缺少登录凭据，请重新登录'
    return
  }
  loading.value = true
  msg.value = ''
  try {
    const { data } = await api.post('/auth/oauth/exchange', {
      code,
      totp_code: withTotp ? totpCode.value : undefined,
    })
    saveSession(data)
    router.push('/dashboard')
  } catch (e) {
    if (e.response?.status === 428) {
      need2fa.value = true
    } else if (e.response?.status === 401) {
      msg.value = '验证码错误'
    } else {
      error.value = e.response?.data?.detail || '登录失败，请重试'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.oauth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--bg-primary);
}

.oauth-card {
  width: 100%;
  max-width: 380px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  box-shadow: var(--shadow-lg);
  padding: 36px 32px;
  text-align: center;
}

.oauth-emoji { font-size: 40px; margin-bottom: 12px; }
.oauth-card h1 { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
.oauth-sub { font-size: 13.5px; color: var(--text-muted); margin-bottom: 20px; }
.oauth-err { color: var(--error); font-size: 13px; margin-top: 10px; }
.oauth-link {
  display: inline-block;
  margin-top: 12px;
  font-size: 13.5px;
  color: var(--primary-color);
  text-decoration: none;
}
.form { text-align: left; }
.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.field span { font-size: 13px; font-weight: 600; color: var(--text-muted); }
.field input {
  padding: 12px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 14px;
  background: var(--bg-input);
  color: var(--text-primary);
}
.field input:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15); }
.btn {
  width: 100%;
  padding: 13px;
  border: none;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
