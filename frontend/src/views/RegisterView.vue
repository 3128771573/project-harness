<template>
  <AuthLayout title="创建账号" subtitle="加入 Project Harness">
    <form @submit.prevent="onSubmit" class="form">
      <label class="field">
        <span>用户名</span>
        <input v-model.trim="form.username" placeholder="字母数字下划线，3-32位" required autocomplete="username" />
      </label>
      <label class="field">
        <span>邮箱</span>
        <input v-model.trim="form.email" type="email" placeholder="you@example.com" required autocomplete="email" />
      </label>
      <label class="field">
        <span>密码</span>
        <input v-model="form.password" type="password" placeholder="至少 8 位" required autocomplete="new-password" />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" class="btn" :disabled="loading">
        {{ loading ? '注册中…' : '注 册' }}
      </button>
      <p class="switch">已有账号？<router-link to="/login">直接登录</router-link></p>
    </form>
  </AuthLayout>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import AuthLayout from '../layouts/AuthLayout.vue'

const router = useRouter()
const form = reactive({ username: '', email: '', password: '' })
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/auth/register', form)
    localStorage.setItem('harness_token', data.access_token)
    localStorage.setItem('harness_user', JSON.stringify(data.user))
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped src="../assets/auth.css"></style>
