<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo-wrap">
        <BrandLogo size="md" />
        <span class="logo-name">Harness</span>
      </div>
      <nav>
        <router-link to="/dashboard" class="nav-item">仪表盘</router-link>
        <router-link to="/ai" class="nav-item active">AI 对话</router-link>
        <router-link to="/iot" class="nav-item">IoT 平台</router-link>
        <router-link to="/settings" class="nav-item">安全设置</router-link>
        <router-link v-if="isAdmin" to="/admin/dashboard" class="nav-item">管理后台</router-link>
      </nav>
      <button class="logout" @click="logout">退出登录</button>
    </aside>

    <main class="main chat-main">
      <header class="chat-head">
        <div>
          <h1>AI Assistant</h1>
          <p class="sub">多模型对话 · 历史记录</p>
        </div>
        <!-- 模型选择 -->
        <select v-model="selectedModel" class="model-select" :disabled="loading">
          <option value="mock">Mock 模式</option>
          <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
        </select>
      </header>

      <div class="chat-body">
        <!-- 聊天区 -->
        <section class="chat-panel" ref="chatBox">
          <div v-if="messages.length === 0" class="chat-empty">
            <p class="empty-emoji">🤖</p>
            <p>输入你的问题，开始对话</p>
          </div>
          <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
            <div v-if="m.role === 'assistant'" class="msg-avatar">✦</div>
            <div class="bubble">{{ m.content }}</div>
          </div>
          <div v-if="loading" class="msg assistant">
            <div class="msg-avatar">✦</div>
            <div class="bubble typing"><span class="tdot"></span><span class="tdot"></span><span class="tdot"></span></div>
          </div>
        </section>

        <!-- Model Info 侧栏 -->
        <aside class="model-side">
          <div class="side-card">
            <div class="side-head"><span class="side-dot"></span> Model Info</div>
            <div class="side-row"><span>当前模型</span><b>{{ selectedModel === 'mock' ? 'Mock' : selectedModel }}</b></div>
            <div class="side-row"><span>对话历史</span><b>{{ historyTotal }}</b></div>
            <div class="side-row"><span>状态</span><b class="ok">{{ loading ? '思考中…' : '就绪' }}</b></div>
          </div>
          <div class="side-card">
            <div class="side-head">快捷提示</div>
            <button v-for="p in prompts" :key="p" class="prompt-chip" @click="question = p; send()">{{ p }}</button>
          </div>
        </aside>
      </div>

      <!-- 输入区 -->
      <form @submit.prevent="send" class="chat-input">
        <input
          v-model.trim="question"
          placeholder="问点什么…（Enter 发送）"
          :disabled="loading"
          maxlength="4000"
        />
        <button type="submit" class="send-btn" :disabled="loading || !question">
          {{ loading ? '…' : '发送' }}
        </button>
      </form>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '../components/BrandLogo.vue'
import api from '../api/client'

const router = useRouter()
const messages = ref([])
const question = ref('')
const loading = ref(false)
const models = ref([])
const selectedModel = ref('mock')
const historyTotal = ref(0)
const chatBox = ref(null)

const prompts = ['帮我写一段 Python 代码', '解释一下什么是 MQTT', '总结一篇技术文章的要点', '生成一个 JSON 示例']

const isAdmin = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('harness_user') || 'null')
    return ['admin', 'super_admin'].includes(u?.role)
  } catch {
    return false
  }
})

async function scrollBottom() {
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

async function loadModels() {
  try {
    const { data } = await api.get('/ai/models')
    models.value = data.filter((m) => m !== 'mock')
  } catch { /* ignore */ }
}

async function loadHistory() {
  try {
    const { data } = await api.get('/ai/history', { params: { limit: 20 } })
    historyTotal.value = data.total
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
    historyTotal.value += 1
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
  router.push('/')
}

onMounted(() => {
  loadModels()
  loadHistory()
})
</script>

<style scoped src="../assets/chat.css"></style>
<style scoped>
.logo-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px 26px;
}

.logo-name {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.chat-main {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding-bottom: 24px;
  max-width: 1200px;
}

.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.chat-head h1 {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.chat-head .sub {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 2px;
}

.model-select {
  padding: 9px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 13.5px;
  font-weight: 600;
  background: var(--card);
  cursor: pointer;
  font-family: inherit;
  box-shadow: var(--shadow-sm);
}

.chat-body {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.chat-panel {
  flex: 1;
  overflow-y: auto;
  background: var(--card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.chat-empty {
  margin: auto;
  color: var(--text-muted);
  text-align: center;
}

.empty-emoji {
  font-size: 44px;
  margin-bottom: 12px;
}

.msg {
  display: flex;
  gap: 10px;
}

.msg.user {
  justify-content: flex-end;
}

.msg-avatar {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 2px;
}

.bubble {
  max-width: 78%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg.user .bubble {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  border-bottom-right-radius: 4px;
}

.msg.assistant .bubble {
  background: #f4f5f7;
  color: var(--text);
  border-bottom-left-radius: 4px;
}

.bubble.typing {
  display: flex;
  gap: 4px;
  align-items: center;
}

.tdot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
  animation: bounce 1.2s infinite;
}

.tdot:nth-child(2) { animation-delay: 0.2s; }
.tdot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

/* Model Info 侧栏 */
.model-side {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
}

.side-card {
  background: var(--card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 18px;
  box-shadow: var(--shadow-sm);
}

.side-head {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 14px;
  color: var(--text-secondary);
}

.side-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
}

.side-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  font-size: 13px;
}

.side-row span {
  color: var(--text-muted);
}

.side-row b {
  font-weight: 600;
  color: var(--text);
}

.side-row b.ok {
  color: var(--success);
}

.prompt-chip {
  display: block;
  width: 100%;
  text-align: left;
  padding: 9px 12px;
  margin-bottom: 8px;
  border: 1px solid var(--border-light);
  border-radius: 9px;
  background: #fafbfc;
  font-size: 12.5px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.12s;
  font-family: inherit;
}

.prompt-chip:hover {
  border-color: var(--primary);
  background: #eef2ff;
  color: var(--primary-dark);
}

.prompt-chip:last-child {
  margin-bottom: 0;
}

/* 输入区 */
.chat-input {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.chat-input input {
  flex: 1;
  padding: 13px 18px;
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 14px;
  background: var(--card);
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.chat-input input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.send-btn {
  padding: 13px 26px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .model-side {
    display: none;
  }
}
</style>
