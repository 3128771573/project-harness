<template>
  <AuthLayout title="重置密码" subtitle="通过邮箱验证码找回">
    <form @submit.prevent="onSubmit" class="form">
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
        <span>新密码</span>
        <input v-model="form.new_password" type="password" placeholder="至少 8 位，含大小写/数字/符号" required autocomplete="new-password" />
      </label>
      <label class="field">
        <span>确认新密码</span>
        <input v-model="form.confirm" type="password" placeholder="再次输入新密码" required autocomplete="new-password" />
      </label>

      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="msg" class="success-msg">{{ msg }}</p>

      <button type="submit" class="btn" :disabled="loading">
        {{ loading ? '提交中…' : '重置密码' }}
      </button>
      <p class="switch">想起密码了？<router-link to="/login">返回登录</router-link></p>
    </form>
  </AuthLayout>
</template>

<script setup>
import { onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import AuthLayout from '../layouts/AuthLayout.vue'

const router = useRouter()
const form = reactive({ email: '', code: '', new_password: '', confirm: '' })
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
    const { data } = await api.post('/auth/send-code', { email: form.email, purpose: 'reset' })
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

async function onSubmit() {
  error.value = ''
  if (form.new_password !== form.confirm) {
    error.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  try {
    const { data } = await api.post('/auth/reset-password', {
      email: form.email,
      token: form.code,
      new_password: form.new_password,
    })
    msg.value = data.message
    setTimeout(() => router.push('/login'), 1500)
  } catch (e) {
    error.value = e.response?.data?.detail || '重置失败'
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
