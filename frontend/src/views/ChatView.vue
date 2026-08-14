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
      <div class="sidebar-theme">
        <ThemeSwitcher />
      </div>
      <button class="logout" @click="logout">退出登录</button>
    </aside>

    <main class="main chat-main">
      <!-- 顶部美化区 -->
      <header class="chat-header">
        <div class="header-grad"></div>
        <div class="header-content">
          <div class="header-title">
            <h1>AI Assistant</h1>
            <p class="sub">多模型对话 · 流式输出 · 深度思考</p>
          </div>
          <div class="header-controls">
            <!-- 深度思考 Toggle -->
            <label class="think-toggle" :class="{ on: deepThink }">
              <input v-model="deepThink" type="checkbox" />
              <span class="toggle-track"><span class="toggle-thumb"></span></span>
              <span class="toggle-label">🧠 深度思考</span>
            </label>
            <!-- 模型选择 -->
            <select v-model="selectedModel" class="model-select" :disabled="loading">
              <option value="mock">Mock 模式</option>
              <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
            </select>
            <!-- 清空 -->
            <button class="clear-btn" title="清空对话" @click="clearChat">🗑</button>
          </div>
        </div>
      </header>

      <div class="chat-body">
        <!-- 聊天区 -->
        <section class="chat-panel" ref="chatBox">
          <div v-if="messages.length === 0" class="chat-empty">
            <p class="empty-emoji">✨</p>
            <p class="empty-title">你好，我是 Harness AI</p>
            <p class="empty-sub">支持 Markdown、LaTeX 公式与代码高亮<br />开启深度思考可获得更细致的推理</p>
            <div class="empty-prompts">
              <button v-for="p in prompts" :key="p" class="prompt-pill" @click="question = p; send()">{{ p }}</button>
            </div>
          </div>

          <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
            <div v-if="m.role === 'assistant'" class="msg-avatar">✦</div>
            <div class="bubble-wrap">
              <!-- 思考过程折叠 -->
              <div v-if="m.role === 'assistant' && m.reasoning" class="reasoning-block">
                <button class="reasoning-head" @click="m.showReasoning = !m.showReasoning">
                  <span class="reasoning-dot"></span>
                  <span>思考过程</span>
                  <span class="reasoning-chev" :class="{ open: m.showReasoning }">▾</span>
                </button>
                <div v-if="m.showReasoning" class="reasoning-body">{{ m.reasoning }}</div>
              </div>

              <div v-if="m.role === 'assistant' && m.content === '' && loading" class="bubble assistant typing">
                <span class="tdot"></span><span class="tdot"></span><span class="tdot"></span>
              </div>

              <div v-else class="bubble" :class="m.role">
                <!-- AI 消息渲染 Markdown -->
                <div v-if="m.role === 'assistant'" class="md-body" v-html="renderHtml(m)" />
                <!-- 用户消息纯文本 -->
                <span v-else>{{ m.content }}</span>
                <span v-if="m.role === 'assistant' && loading && i === messages.length - 1" class="cursor">▍</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Model Info 侧栏 -->
        <aside class="model-side">
          <div class="side-card">
            <div class="side-head"><span class="side-dot"></span> Model Info</div>
            <div class="side-row"><span>当前模型</span><b>{{ currentModelLabel }}</b></div>
            <div class="side-row"><span>对话历史</span><b>{{ historyTotal }}</b></div>
            <div class="side-row"><span>深度思考</span><b :class="deepThink ? 'ok' : ''">{{ deepThink ? '开启' : '关闭' }}</b></div>
            <div class="side-row"><span>状态</span><b class="ok">{{ loading ? '思考中…' : '就绪' }}</b></div>
          </div>
          <div class="side-card">
            <div class="side-head">Markdown 支持</div>
            <div class="md-hint">**加粗** · *斜体*</div>
            <div class="md-hint">`行内代码`</div>
            <div class="md-hint">$E=mc^2$ 公式</div>
            <div class="md-hint">```python 代码块</div>
          </div>
        </aside>
      </div>

      <!-- 输入区 -->
      <form @submit.prevent="send" class="chat-input">
        <input
          v-model.trim="question"
          placeholder="问点什么…（Enter 发送 · Shift+Enter 换行）"
          :disabled="loading"
          maxlength="4000"
        />
        <button type="submit" class="send-btn" :disabled="loading || !question">
          <svg v-if="!loading" viewBox="0 0 24 24" style="width:16px;height:16px;fill:currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          <span v-else class="send-dots"><span class="tdot"></span><span class="tdot"></span><span class="tdot"></span></span>
        </button>
      </form>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BrandLogo from '../components/BrandLogo.vue'
import ThemeSwitcher from '../components/ThemeSwitcher.vue'
import api from '../api/client'
import { renderMarkdown } from '../utils/markdown'

const router = useRouter()
const messages = ref([])
const question = ref('')
const loading = ref(false)
const models = ref([])
const selectedModel = ref('mock')
const deepThink = ref(false)
const historyTotal = ref(0)
const chatBox = ref(null)

const prompts = [
  '帮我写一段 Python 代码',
  '解释一下什么是 MQTT',
  '讲一个物理公式的推导',
  '生成一个 JSON 示例',
]

const isAdmin = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('harness_user') || 'null')
    return ['admin', 'super_admin'].includes(u?.role)
  } catch {
    return false
  }
})

const currentModelLabel = computed(() => {
  if (deepThink.value) return 'Reasoner (深度思考)'
  return selectedModel.value === 'mock' ? 'Mock' : selectedModel.value
})

function renderHtml(m) {
  return renderMarkdown(m.content || '')
}

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
      .map((h) => ({
        role: 'user',
        content: h.question,
        reasoning: '',
      }, {
        role: 'assistant',
        content: h.answer,
        reasoning: '',
        showReasoning: false,
      }))
      .flat()
    await scrollBottom()
  } catch { /* ignore */ }
}

function clearChat() {
  if (messages.value.length && !loading.value) {
    messages.value = []
    question.value = ''
  }
}

async function send() {
  const q = question.value
  if (!q || loading.value) return
  question.value = ''
  loading.value = true

  messages.value.push({ role: 'user', content: q })
  const aiMsg = { role: 'assistant', content: '', reasoning: '', showReasoning: false }
  messages.value.push(aiMsg)
  await scrollBottom()

  try {
    const token = localStorage.getItem('harness_access')
    const resp = await fetch('/api/v1/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ question: q, stream: true, reasoning: deepThink.value }),
    })

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: '请求失败' }))
      aiMsg.content = '⚠️ ' + (err.detail || '请求失败')
      await scrollBottom()
      return
    }

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // 按 SSE 空行分割事件
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const line = part.trim()
        if (!line.startsWith('data:')) continue
        const raw = line.slice(5).trim()
        if (!raw) continue
        let evt
        try {
          evt = JSON.parse(raw)
        } catch {
          continue
        }
        if (evt.type === 'reasoning') {
          aiMsg.reasoning += evt.content
        } else if (evt.type === 'content') {
          aiMsg.content += evt.content
          await scrollBottom()
        } else if (evt.type === 'done') {
          historyTotal.value += 1
        } else if (evt.type === 'error') {
          aiMsg.content = '⚠️ ' + (evt.content || '请求失败')
        }
      }
    }
    // 处理缓冲尾部
    if (buffer) {
      const line = buffer.trim()
      if (line.startsWith('data:')) {
        const raw = line.slice(5).trim()
        try {
          const evt = JSON.parse(raw)
          if (evt.type === 'reasoning') aiMsg.reasoning += evt.content
          else if (evt.type === 'content') aiMsg.content += evt.content
        } catch { /* ignore */ }
      }
    }
    aiMsg.showReasoning = !!aiMsg.reasoning
  } catch (e) {
    aiMsg.content = '⚠️ 网络错误，请重试'
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
/* ===== 侧边栏 Logo ===== */
.logo-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px 26px;
}

.logo-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--sidebar-text);
}

.sidebar-theme {
  padding: 8px;
  margin-bottom: 4px;
}

.sidebar-theme :deep(.theme-switcher) {
  width: 100%;
}

.sidebar-theme :deep(.ts-option) {
  flex: 1;
  justify-content: center;
  padding: 7px 8px;
}

.sidebar-theme :deep(.ts-label) {
  display: none;
}

/* ===== 顶部美化区 ===== */
.chat-main {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding-bottom: 24px;
  max-width: 1240px;
}

.chat-header {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-lg);
  margin-bottom: 18px;
  border: 1px solid var(--border-light);
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
}

.header-grad {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(600px 140px at 10% -30%, rgba(37, 99, 235, 0.12), transparent),
    radial-gradient(500px 120px at 90% -20%, rgba(124, 58, 237, 0.12), transparent);
  pointer-events: none;
}

.header-content {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 26px;
  gap: 16px;
  flex-wrap: wrap;
}

.header-title h1 {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #111827, #2563eb);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.header-title .sub {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 3px;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* 深度思考 Toggle */
.think-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--bg);
  transition: all 0.2s;
}

.think-toggle.on {
  border-color: var(--accent);
  background: #f5f3ff;
}

.think-toggle input {
  display: none;
}

.toggle-track {
  width: 34px;
  height: 19px;
  border-radius: 999px;
  background: #d1d5db;
  position: relative;
  transition: background 0.2s;
}

.think-toggle.on .toggle-track {
  background: linear-gradient(135deg, var(--primary), var(--accent));
}

.toggle-thumb {
  position: absolute;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  background: var(--bg-card);
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.think-toggle.on .toggle-thumb {
  transform: translateX(15px);
}

.toggle-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.think-toggle.on .toggle-label {
  color: var(--accent);
}

/* 模型选择 */
.model-select {
  padding: 8px 13px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  background: var(--card);
  cursor: pointer;
  font-family: inherit;
  box-shadow: var(--shadow-sm);
  color: var(--text);
}

.clear-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--card);
  cursor: pointer;
  font-size: 15px;
  transition: all 0.15s;
}

.clear-btn:hover {
  background: #fef2f2;
  border-color: #fecaca;
}

/* ===== 聊天区 ===== */
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
  gap: 18px;
  min-width: 0;
}

/* 空状态 */
.chat-empty {
  margin: auto;
  text-align: center;
  color: var(--text-muted);
  max-width: 480px;
}

.empty-emoji {
  font-size: 46px;
  margin-bottom: 10px;
}

.empty-title {
  font-size: 19px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
}

.empty-sub {
  font-size: 13.5px;
  line-height: 1.8;
  margin-bottom: 22px;
}

.empty-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.prompt-pill {
  padding: 8px 16px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--bg);
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.prompt-pill:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--bg-active);
}

/* 消息 */
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

.bubble-wrap {
  max-width: 82%;
  min-width: 0;
}

.bubble {
  padding: 13px 17px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.msg.user .bubble {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  border-bottom-right-radius: 4px;
}

.msg.assistant .bubble {
  background: var(--bg-secondary);
  color: var(--text);
  border-bottom-left-radius: 4px;
}

/* 思考过程 */
.reasoning-block {
  margin-bottom: 8px;
}

.reasoning-head {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 12.5px;
  color: var(--text-muted);
  font-family: inherit;
  width: 100%;
  transition: background 0.15s;
}

.reasoning-head:hover {
  background: var(--bg-secondary);
}

.reasoning-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse 1.5s infinite;
}

.reasoning-chev {
  margin-left: auto;
  transition: transform 0.2s;
  font-size: 11px;
}

.reasoning-chev.open {
  transform: rotate(180deg);
}

.reasoning-body {
  margin-top: 8px;
  padding: 10px 14px;
  background: var(--bg-secondary);
  border: 1px dashed var(--border);
  border-radius: 10px;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.7;
  white-space: pre-wrap;
}

/* 打字动画 */
.bubble.typing {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 16px 18px;
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

.send-dots {
  display: inline-flex;
  gap: 3px;
  align-items: center;
}

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* 流式光标 */
.cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--primary);
  margin-left: 2px;
  vertical-align: -2px;
  animation: blink 0.9s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ===== Markdown 渲染样式 ===== */
.md-body :deep(p) {
  margin: 0 0 10px;
}

.md-body :deep(p:last-child) {
  margin-bottom: 0;
}

.md-body :deep(h1), .md-body :deep(h2), .md-body :deep(h3) {
  margin: 14px 0 8px;
  font-weight: 700;
}

.md-body :deep(h1) { font-size: 17px; }
.md-body :deep(h2) { font-size: 16px; }
.md-body :deep(h3) { font-size: 15px; }

.md-body :deep(ul), .md-body :deep(ol) {
  margin: 8px 0;
  padding-left: 22px;
}

.md-body :deep(li) {
  margin: 4px 0;
}

.md-body :deep(blockquote) {
  border-left: 3px solid var(--primary);
  padding: 6px 14px;
  margin: 10px 0;
  background: var(--bg-secondary);
  border-radius: 0 8px 8px 0;
  color: var(--text-muted);
}

.md-body :deep(code) {
  background: rgba(15, 23, 42, 0.07);
  padding: 2px 6px;
  border-radius: 5px;
  font-size: 12.5px;
  font-family: var(--font-mono);
}

.md-body :deep(pre) {
  background: var(--brand-block);
  border-radius: 10px;
  padding: 14px 16px;
  margin: 10px 0;
  overflow-x: auto;
}

.md-body :deep(pre code) {
  background: transparent;
  padding: 0;
  color: var(--text-secondary);
  font-size: 12.5px;
  line-height: 1.6;
}

.md-body :deep(table) {
  border-collapse: collapse;
  margin: 10px 0;
  font-size: 13px;
}

.md-body :deep(th), .md-body :deep(td) {
  border: 1px solid var(--border);
  padding: 7px 12px;
}

.md-body :deep(th) {
  background: var(--bg-secondary);
}

.md-body :deep(a) {
  color: var(--primary);
}

/* KaTeX */
.md-body :deep(.katex-block) {
  margin: 12px 0;
  overflow-x: auto;
}

.md-body :deep(.katex-inline) {
  padding: 0 2px;
}

/* ===== Model Info 侧栏 ===== */
.model-side {
  width: 230px;
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

.md-hint {
  font-size: 12px;
  color: var(--text-muted);
  padding: 4px 0;
  font-family: var(--font-mono);
  word-break: break-all;
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  padding: 13px 18px;
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
