<template>
  <AuthLayout title="欢迎回来" subtitle="登录 Project Harness">
    <form @submit.prevent="onSubmit" class="form">
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
      <p class="switch">还没有账号？<router-link to="/register">立即注册</router-link></p>
    </form>
  </AuthLayout>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import AuthLayout from '../layouts/AuthLayout.vue'

const router = useRouter()
const form = reactive({ email: '', password: '' })
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/auth/login', form)
    localStorage.setItem('harness_access', data.access_token)
    localStorage.setItem('harness_refresh', data.refresh_token)
    localStorage.setItem('harness_user', JSON.stringify(data.user))
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped src="../assets/auth.css"></style>
