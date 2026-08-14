<template>
  <AuthLayout title="创建账号" subtitle="加入 Harness">
    <form @submit.prevent="onSubmit" class="form">
      <label class="field">
        <span>用户名</span>
        <input v-model.trim="form.username" placeholder="字母数字下划线，3-32位" required autocomplete="username" />
      </label>

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

      <label class="field">
        <span>密码</span>
        <input v-model="form.password" type="password" placeholder="至少 8 位，含大小写/数字/符号" required autocomplete="new-password" />
      </label>

      <label class="field">
        <span>确认密码</span>
        <input v-model="form.confirm" type="password" placeholder="再次输入密码" required autocomplete="new-password" />
      </label>

      <label class="checkbox-row">
        <input v-model="agree" type="checkbox" required />
        <span>
          我已年满 18 周岁（或已由监护人同意），并已阅读、理解且同意
          <router-link to="/terms" target="_blank">《用户协议》</router-link> 与
          <router-link to="/privacy" target="_blank">《隐私政策》</router-link>
          （含即时通讯功能条款：消息保存期限、内容审核、水印溯源声明）
        </span>
      </label>

      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="msg" class="success-msg">{{ msg }}</p>

      <button type="submit" class="btn" :disabled="loading || !agree">
        {{ loading ? '注册中…' : '注 册' }}
      </button>
      <p class="switch">已有账号？<router-link to="/login">直接登录</router-link></p>
    </form>
  </AuthLayout>
</template>

<script setup>
import { onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import AuthLayout from '../layouts/AuthLayout.vue'

const router = useRouter()
const form = reactive({ username: '', email: '', password: '', confirm: '', code: '' })
const agree = ref(false)
const error = ref('')
const msg = ref('')
const loading = ref(false)
const sending = ref(false)
const cooldown = ref(0)
let timer = null

async function sendCode() {
  if (!form.email) {
    error.value = '请先填写邮箱'
    return
  }
  error.value = ''
  sending.value = true
  try {
    const { data } = await api.post('/auth/send-code', { email: form.email, purpose: 'register' })
    msg.value = data.message
    cooldown.value = data.cooldown || 60
    timer = setInterval(() => {
      cooldown.value -= 1
      if (cooldown.value <= 0) clearInterval(timer)
    }, 1000)
    if (data.dev_code) {
      msg.value = `⚠️ 开发模式（未配置 SMTP），验证码：${data.dev_code}`
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '发送失败'
  } finally {
    sending.value = false
  }
}

async function onSubmit() {
  error.value = ''
  // 前端校验：确认密码
  if (form.password !== form.confirm) {
    error.value = '两次输入的密码不一致'
    return
  }
  // 前端校验：密码强度提示
  if (form.password.length < 8) {
    error.value = '密码至少 8 位'
    return
  }
  loading.value = true
  try {
    const { data } = await api.post('/auth/register', {
      username: form.username,
      email: form.email,
      password: form.password,
      code: form.code,
    })
    localStorage.setItem('harness_access', data.access_token)
    localStorage.setItem('harness_refresh', data.refresh_token)
    localStorage.setItem('harness_user', JSON.stringify(data.user))
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || '注册失败，请稍后重试'
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
</style>
