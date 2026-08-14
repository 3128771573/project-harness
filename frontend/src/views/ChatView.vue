<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">H</div>
      <nav>
        <router-link to="/dashboard" class="nav-item">仪表盘</router-link>
        <router-link to="/ai" class="nav-item active">AI 对话</router-link>
        <a class="nav-item">Demo 平台</a>
        <router-link v-if="isAdmin" to="/admin/dashboard" class="nav-item">管理后台</router-link>
      </nav>
      <button class="logout" @click="logout">退出登录</button>
    </aside>

    <main class="main chat-main">
      <header class="topbar">
        <h1>AI 对话</h1>
        <div class="model-chip">{{ model }}</div>
      </header>

      <section class="chat-panel" ref="chatBox">
        <div v-if="messages.length === 0" class="chat-empty">
          <p>👋 输入你的问题，开始对话</p>
        </div>
        <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
          <div class="bubble">{{ m.content }}</div>
        </div>
        <div v-if="loading" class="msg assistant">
          <div class="bubble typing">正在思考…</div>
        </div>
      </section>

      <form @submit.prevent="send" class="chat-input">
        <input
          v-model.trim="question"
          placeholder="问点什么…（Enter 发送）"
          :disabled="loading"
          maxlength="4000"
        />
        <button type="submit" class="btn small" :disabled="loading || !question">
          {{ loading ? '…' : '发送' }}
        </button>
      </form>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'

const router = useRouter()
const isAdmin = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('harness_user') || 'null')
    return ['admin', 'super_admin'].includes(u?.role)
  } catch {
    return false
  }
})
const messages = ref([])
const question = ref('')
const loading = ref(false)
const model = ref('...')
const chatBox = ref(null)

async function scrollBottom() {
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

async function loadModels() {
  try {
    const { data } = await api.get('/ai/models')
    model.value = data.join(', ')
  } catch { /* ignore */ }
}

async function loadHistory() {
  try {
    const { data } = await api.get('/ai/history', { params: { limit: 20 } })
    messages.value = data.items
      .slice()
      .reverse()
      .map((h) => [
        { role: 'user', content: h.question },
        { role: 'assistant', content: h.answer },
      ])
      .flat()
    await scrollBottom()
  } catch { /* ignore */ }
}

async function send() {
  const q = question.value
  if (!q || loading.value) return
  question.value = ''
  messages.value.push({ role: 'user', content: q })
  loading.value = true
  await scrollBottom()
  try {
    const { data } = await api.post('/ai/chat', { question: q })
    messages.value.push({ role: 'assistant', content: data.answer })
    model.value = data.model
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '⚠️ ' + (e.response?.data?.detail || '请求失败') })
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

function logout() {
  localStorage.removeItem('harness_access')
  localStorage.removeItem('harness_refresh')
  localStorage.removeItem('harness_user')
  router.push('/login')
}

onMounted(() => {
  loadModels()
  loadHistory()
})
</script>

<style scoped src="../assets/chat.css"></style>
