<template>
  <div class="messages-page">
    <!-- 明水印层（昵称 + UID + 时间，防截图传播） -->
    <div class="wm-layer" :style="wmBackground" aria-hidden="true"></div>

    <aside class="conv-panel">
      <div class="conv-head">
        <h2>私信</h2>
        <div class="search-box">
          <input
            v-model="searchQ"
            placeholder="搜索用户发起私信…"
            @input="onSearch"
            @focus="searchFocus = true"
            @blur="onSearchBlur"
          />
          <div v-if="searchFocus && searchResults.length" class="search-results">
            <div
              v-for="u in searchResults"
              :key="u.uid"
              class="search-item"
              @mousedown.prevent="startWith(u)"
            >
              <img v-if="u.avatar" :src="u.avatar" class="s-avatar" alt="" />
              <span v-else class="s-avatar">{{ (u.nickname || u.username)[0] }}</span>
              <span class="s-name">{{ u.nickname || u.username }}</span>
              <span class="s-uname">@{{ u.username }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="conv-list">
        <div v-if="!convs.length && !loading" class="conv-empty">
          暂无会话<br /><span>搜索用户发起私信</span>
        </div>
        <div
          v-for="c in convs"
          :key="c.id"
          class="conv-item"
          :class="{ active: active && active.id === c.id }"
          @click="openConv(c)"
        >
          <img v-if="c.other.avatar" :src="c.other.avatar" class="c-avatar" alt="" />
          <span v-else class="c-avatar">{{ (c.other.nickname || c.other.username)[0] }}</span>
          <div class="c-main">
            <div class="c-top">
              <b class="c-name">{{ c.other.nickname || c.other.username }}</b>
              <span class="c-time">{{ fmtListTime(c.last_message_at || c.created_time) }}</span>
            </div>
            <div class="c-last">
              <span class="c-text">{{ lastText(c) }}</span>
              <span v-if="c.unread > 0" class="c-unread">{{ c.unread > 99 ? '99+' : c.unread }}</span>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <section v-if="active" class="chat-pane">
      <header class="chat-head">
        <button class="back-btn" @click="closeChat" title="返回列表">←</button>
        <img v-if="active.other.avatar" :src="active.other.avatar" class="c-avatar" alt="" />
        <span v-else class="c-avatar">{{ (active.other.nickname || active.other.username)[0] }}</span>
        <div class="ch-info">
          <b>{{ active.other.nickname || active.other.username }}</b>
          <span class="ch-sub">@{{ active.other.username }}<template v-if="isBot"> · 官方公告账号</template></span>
        </div>
        <div class="ch-actions">
          <span class="ws-state" :class="wsState">{{ wsLabel }}</span>
          <button v-if="!isBot" class="btn ghost sm" @click="blockPartner" title="拉黑对方（双向禁止互发，可随时解除）">拉黑</button>
          <button class="btn ghost sm" @click="hideConv" title="删除会话（仅隐藏我的视图，对方记录保留）">删除</button>
        </div>
      </header>

      <div class="msg-area" @contextmenu.prevent @copy.prevent @dragstart.prevent>
        <div v-if="loadingMsgs" class="msg-hint">加载中…</div>
        <button v-else-if="hasMore" class="load-more" @click="loadOlder">加载更早消息</button>
        <div
          v-for="m in msgs"
          :key="m.id"
          class="msg-row"
          :class="{ mine: m.sender_id === me.uid, bot: m.sender_id === BOT_UID }"
        >
          <div class="bubble" :class="{ recalled: m.status === 'recalled' }">
            <template v-if="m.status === 'recalled'">
              <span class="recalled-text">{{ m.sender_id === me.uid ? '你撤回了一条消息' : '对方撤回了一条消息' }}</span>
            </template>
            <template v-else>
              <div v-if="m.kind === 'image'" class="msg-img">
                <img :src="m.content" alt="图片消息" @click="previewUrl = m.content" />
              </div>
              <div v-else class="msg-text" v-html="mdHtml(m)"></div>
              <span class="zw-mark" aria-hidden="true">{{ zwFor(m) }}</span>
            </template>
            <div class="msg-meta">
              <span class="m-time">{{ fmtMsgTime(m.created_time) }}</span>
              <span v-if="m.sender_id === me.uid && m.status === 'active'" class="m-read">{{ isRead(m) ? '已读' : '' }}</span>
              <button v-if="canRecall(m)" class="m-recall" @click="recall(m)">撤回</button>
              <button v-if="m.sender_id !== me.uid && m.status === 'active'" class="m-recall" @click="reportMsg(m)">举报</button>
              <button v-if="m.status === 'active'" class="m-copy" @click="copyMsg(m)" title="复制消息（含溯源水印）">复制</button>
            </div>
          </div>
        </div>
      </div>

      <div class="composer">
        <button class="img-btn" title="发送图片（≤5MB）" @click="imgInput.click()">🖼</button>
        <input
          ref="imgInput"
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          hidden
          @change="onImage"
        />
        <textarea
          v-model="draft"
          rows="2"
          maxlength="4000"
          placeholder="输入消息…（Enter 发送，Shift+Enter 换行）"
          @keydown.enter.exact.prevent="sendText"
        ></textarea>
        <button class="btn primary" :disabled="sending || !draft.trim()" @click="sendText">发送</button>
      </div>
    </section>

    <section v-else class="chat-empty">
      <div class="ce-inner">
        <div class="ce-icon">💬</div>
        <p>选择左侧会话，或搜索用户发起私信</p>
        <p class="ce-sub">消息页已启用明水印 + 文本溯源水印，截图/复制均可追溯</p>
      </div>
    </section>

    <div v-if="previewUrl" class="img-preview" @click="previewUrl = null">
      <img :src="previewUrl" alt="预览" />
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import api from '../api/client'
import { renderMarkdown } from '../utils/markdown'
import { encodeTextWatermark } from '../utils/watermark'

const BOT_UID = 'bot-harness-official'

// ===== 当前用户 =====
const me = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('harness_user') || 'null')
  } catch {
    return null
  }
})

// ===== 会话列表 =====
const isBot = computed(() => active.value?.other?.uid === BOT_UID)
const convs = ref([])
const loading = ref(false)
const active = ref(null)
const msgs = ref([])
const hasMore = ref(false)
const loadingMsgs = ref(false)
const draft = ref('')
const sending = ref(false)
const previewUrl = ref('')
const imgInput = ref(null)
const zwCache = new Map()

async function loadConvs() {
  try {
    const { data } = await api.get('/im/conversations')
    const list = data.items || []
    convs.value = list
    if (active.value) {
      const upd = list.find((c) => c.id === active.value.id)
      if (upd) {
        active.value.other_last_read_at = upd.other_last_read_at
        active.value.unread = upd.unread
      }
    }
  } catch {
    /* ignore */
  }
}

async function openConv(c) {
  active.value = c
  await Promise.all([loadMsgs(c), markRead(c)])
  joinRoom(c.id)
}

async function closeChat() {
  if (active.value) leaveRoom(active.value.id)
  active.value = null
  msgs.value = []
}

async function loadMsgs(c) {
  loadingMsgs.value = true
  try {
    const { data } = await api.get('/im/conversations/' + c.id + '/messages?limit=50')
    msgs.value = (data.items || []).slice().reverse()
    hasMore.value = data.has_more
    await nextTick()
    scrollBottom(true)
  } catch {
    /* ignore */
  } finally {
    loadingMsgs.value = false
  }
}

async function loadOlder() {
  if (!active.value || !msgs.value.length) return
  const before = msgs.value[0].created_time
  try {
    const { data } = await api.get(
      '/im/conversations/' + active.value.id + '/messages?limit=50&before=' + encodeURIComponent(before)
    )
    const older = (data.items || []).slice().reverse()
    const known = new Set(msgs.value.map((m) => m.id))
    msgs.value = older.filter((m) => !known.has(m.id)).concat(msgs.value)
    hasMore.value = data.has_more
  } catch {
    /* ignore */
  }
}

async function markRead(c) {
  try {
    await api.post('/im/conversations/' + c.id + '/read')
    c.unread = 0
  } catch {
    /* ignore */
  }
}

async function sendText() {
  const text = draft.value.trim()
  if (!text || sending.value || !active.value) return
  sending.value = true
  try {
    const { data } = await api.post('/im/conversations/' + active.value.id + '/messages', {
      kind: 'text',
      content: text,
    })
    draft.value = ''
    upsertMsg(data)
    touchConv(data)
  } catch (e) {
    alert(e.response?.data?.detail || '发送失败')
  } finally {
    sending.value = false
  }
}

async function onImage(ev) {
  const file = ev.target.files?.[0]
  ev.target.value = ''
  if (!file || !active.value) return
  if (file.size > 5 * 1024 * 1024) {
    alert('图片不能超过 5MB')
    return
  }
  const fd = new FormData()
  fd.append('file', file)
  sending.value = true
  try {
    const up = await api.post('/im/upload', fd)
    const { data } = await api.post('/im/conversations/' + active.value.id + '/messages', {
      kind: 'image',
      content: up.data.url,
    })
    upsertMsg(data)
    touchConv(data)
  } catch (e) {
    alert(e.response?.data?.detail || '图片发送失败')
  } finally {
    sending.value = false
  }
}

async function recall(m) {
  if (!confirm('确定撤回这条消息？')) return
  try {
    await api.post('/im/messages/' + m.id + '/recall')
    m.status = 'recalled'
    const c = convs.value.find((x) => x.id === active.value?.id)
    if (c && c.last_message && c.last_message.id === m.id) c.last_message.status = 'recalled'
  } catch (e) {
    alert(e.response?.data?.detail || '撤回失败')
  }
}

async function hideConv() {
  if (!active.value) return
  if (!confirm('删除会话将仅隐藏你的视图（对方记录保留），确定？')) return
  try {
    await api.delete('/im/conversations/' + active.value.id)
    convs.value = convs.value.filter((c) => c.id !== active.value.id)
    closeChat()
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

async function blockPartner() {
  if (!active.value || isBot) return
  const name = active.value.other.nickname || active.value.other.username
  if (!confirm('拉黑 ' + name + ' 后双方将无法互发私信（可在设置中解除），确定？')) return
  try {
    await api.post('/im/blocks', { user_id: active.value.other.uid })
    alert('已拉黑 ' + name)
  } catch (e) {
    alert(e.response?.data?.detail || '拉黑失败')
  }
}

async function reportMsg(m) {
  const reason = prompt('举报原因（100 字内，将进入管理员审核队列）：')
  if (!reason) return
  try {
    await api.post('/im/messages/' + m.id + '/report', { reason: reason.slice(0, 200) })
    alert('已提交举报，管理员将尽快处理')
  } catch (e) {
    alert(e.response?.data?.detail || '举报失败')
  }
}

async function copyMsg(m) {
  try {
    await navigator.clipboard.writeText(m.content + '\n' + zwFor(m))
    alert('已复制（含溯源水印）')
  } catch {
    try {
      const ta = document.createElement('textarea')
      ta.value = m.content + '\n' + zwFor(m)
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      alert('已复制（含溯源水印）')
    } catch {
      alert('复制失败')
    }
  }
}

// ===== 消息渲染 =====
function mdHtml(m) {
  return renderMarkdown(m.content)
}

function zwFor(m) {
  if (zwCache.has(m.id)) return zwCache.get(m.id)
  const ts = Math.floor(new Date(m.created_time).getTime() / 1000)
  const zw = encodeTextWatermark(me.value.uid, m.id, ts)
  zwCache.set(m.id, zw)
  return zw
}

function canRecall(m) {
  if (m.sender_id !== me.value.uid || m.status !== 'active') return false
  const age = Date.now() - new Date(m.created_time).getTime()
  return age < 2 * 60 * 1000
}

function isRead(m) {
  if (!active.value?.other_last_read_at) return false
  return new Date(active.value.other_last_read_at).getTime() >= new Date(m.created_time).getTime()
}

function upsertMsg(m) {
  if (!msgs.value.some((x) => x.id === m.id)) msgs.value.push(m)
}

function touchConv(m) {
  const c = convs.value.find((x) => x.id === active.value?.id)
  if (c) {
    c.last_message = m
    c.last_message_at = m.created_time
    convs.value = [c].concat(convs.value.filter((x) => x.id !== c.id))
  }
}

function lastText(c) {
  const lm = c.last_message
  if (!lm) return ''
  if (lm.status === 'recalled') return lm.sender_id === me.value.uid ? '你撤回了一条消息' : '对方撤回了一条消息'
  if (lm.kind === 'image') return '[图片]'
  const s = lm.content.replace(/\n/g, ' ')
  return s.length > 24 ? s.slice(0, 24) + '…' : s
}

// ===== 时间格式化 =====
function pad(n) {
  return n < 10 ? '0' + n : String(n)
}

function fmtListTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  const yest = new Date(now.getTime() - 86400000)
  if (sameDay) return pad(d.getHours()) + ':' + pad(d.getMinutes())
  if (d.toDateString() === yest.toDateString()) return '昨天'
  return (d.getMonth() + 1) + '月' + d.getDate() + '日'
}

function fmtMsgTime(iso) {
  const d = new Date(iso)
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  const hm = pad(d.getHours()) + ':' + pad(d.getMinutes())
  if (sameDay) return hm
  return (d.getMonth() + 1) + '月' + d.getDate() + '日 ' + hm
}

// ===== 用户搜索 =====
const searchQ = ref('')
const searchResults = ref([])
const searchFocus = ref(false)
let searchTimer = null

function onSearch() {
  clearTimeout(searchTimer)
  const q = searchQ.value.trim()
  if (!q) {
    searchResults.value = []
    return
  }
  searchTimer = setTimeout(async () => {
    try {
      const { data } = await api.get('/im/users?q=' + encodeURIComponent(q))
      searchResults.value = data.items || []
    } catch {
      searchResults.value = []
    }
  }, 300)
}

function onSearchBlur() {
  setTimeout(() => {
    searchFocus.value = false
  }, 200)
}

async function startWith(u) {
  searchQ.value = ''
  searchResults.value = []
  try {
    const { data } = await api.post('/im/conversations', { user_id: u.uid })
    let c = convs.value.find((x) => x.id === data.id)
    if (!c) {
      convs.value = [data].concat(convs.value)
      c = data
    } else {
      c.other = data.other
      c.unread = data.unread
      c.last_message = data.last_message
      c.last_message_at = data.last_message_at
    }
    openConv(c)
  } catch (e) {
    alert(e.response?.data?.detail || '无法发起会话')
  }
}

// ===== WebSocket 实时通道 =====
const wsState = ref('closed') // closed / connecting / open
const ws = ref(null)
let wsTimer = null
let wsPingTimer = null
let retry = 0
let joinedCid = null
let reloadTimer = null

const wsLabel = computed(() => {
  if (wsState.value === 'open') return '● 实时'
  if (wsState.value === 'connecting') return '连接中…'
  return '○ 已断开'
})

function wsUrl() {
  const token = localStorage.getItem('harness_access') || ''
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return proto + '://' + window.location.host + '/api/v1/im/ws?token=' + encodeURIComponent(token)
}

function connectWs() {
  clearTimeout(wsTimer)
  if (!me.value) return
  wsState.value = 'connecting'
  let sock
  try {
    sock = new WebSocket(wsUrl())
  } catch {
    scheduleReconnect()
    return
  }
  ws.value = sock
  sock.onopen = () => {
    wsState.value = 'open'
    retry = 0
    // 心跳：25s ping，保活并探测断线
    clearInterval(wsPingTimer)
    wsPingTimer = setInterval(() => {
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        ws.value.send(JSON.stringify({ type: 'ping' }))
      }
    }, 25000)
    if (active.value) joinRoom(active.value.id)
    loadConvs()
  }
  sock.onmessage = (ev) => {
    try {
      handleWsEvent(JSON.parse(ev.data))
    } catch {
      /* ignore */
    }
  }
  sock.onclose = () => {
    wsState.value = 'closed'
    joinedCid = null
    clearInterval(wsPingTimer)
    scheduleReconnect()
  }
  sock.onerror = () => {
    try {
      sock.close()
    } catch {
      /* ignore */
    }
  }
}

function scheduleReconnect() {
  const delay = Math.min(30000, 1000 * Math.pow(2, retry))
  retry += 1
  wsTimer = setTimeout(connectWs, delay)
}

function joinRoom(cid) {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    if (joinedCid && joinedCid !== cid) leaveRoom(joinedCid)
    ws.value.send(JSON.stringify({ type: 'join', conversation_id: cid }))
    joinedCid = cid
  }
}

function leaveRoom(cid) {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({ type: 'leave', conversation_id: cid }))
  }
  if (joinedCid === cid) joinedCid = null
}

function handleWsEvent(e) {
  if (e.type === 'im.message') {
    const cid = e.conversation_id
    if (active.value && cid === active.value.id) {
      if (!msgs.value.some((m) => m.id === e.message.id)) {
        msgs.value.push(e.message)
        scrollBottom(false)
      }
      markRead(active.value)
    } else {
      const c = convs.value.find((x) => x.id === cid)
      if (c) {
        c.unread += 1
        c.last_message = e.message
        c.last_message_at = e.message.created_time
        convs.value = [c].concat(convs.value.filter((x) => x.id !== c.id))
      } else {
        loadConvs()
      }
    }
  } else if (e.type === 'im.recalled') {
    const m = msgs.value.find((x) => x.id === e.message_id)
    if (m) {
      m.status = 'recalled'
    }
    const c = convs.value.find((x) => x.id === e.conversation_id)
    if (c && c.last_message && c.last_message.id === e.message_id) {
      c.last_message.status = 'recalled'
    }
  } else if (e.type === 'im.read') {
    if (active.value && e.conversation_id === active.value.id) {
      active.value.other_last_read_at = new Date().toISOString()
    }
  } else if (e.type === 'im.conv_update') {
    clearTimeout(reloadTimer)
    reloadTimer = setTimeout(loadConvs, 500)
  }
}

function scrollBottom(force) {
  nextTick(() => {
    const area = document.querySelector('.msg-area')
    if (area) area.scrollTop = area.scrollHeight
  })
}

// ===== 明水印层 =====
const wmBackground = ref('')
let wmTimer = null

function buildWatermark() {
  if (!me.value) return
  const nick = me.value.nickname || me.value.username
  const now = new Date()
  const pad2 = (n) => (n < 10 ? '0' + n : String(n))
  const dateStr = now.getFullYear() + '-' + pad2(now.getMonth() + 1) + '-' + pad2(now.getDate()) + ' ' + pad2(now.getHours()) + ':' + pad2(now.getMinutes())
  const text = nick + ' (UID: ' + me.value.uid + ') · ' + dateStr
  const svg =
    "<svg xmlns='http://www.w3.org/2000/svg' width='280' height='220'>" +
    "<text x='50%' y='50%' font-size='13' fill='rgba(120,120,120,0.055)' " +
    "font-family='system-ui,sans-serif' text-anchor='middle' " +
    "transform='rotate(-25 140 110)'>" + text + '</text></svg>'
  wmBackground.value = {
    backgroundImage: "url('data:image/svg+xml;utf8," + encodeURIComponent(svg) + "')",
    backgroundSize: '280px 220px',
  }
}

// ===== 生命周期 =====
onMounted(async () => {
  buildWatermark()
  wmTimer = setInterval(buildWatermark, 30000)
  loading.value = true
  await loadConvs()
  loading.value = false
  connectWs()
})

onUnmounted(() => {
  clearTimeout(wsTimer)
  clearTimeout(reloadTimer)
  clearInterval(wsPingTimer)
  clearInterval(wmTimer)
  if (ws.value) {
    try {
      ws.value.onclose = null
      ws.value.close()
    } catch {
      /* ignore */
    }
  }
})
</script>

<style scoped>
.messages-page {
  position: relative;
  display: flex;
  height: calc(100vh - 60px);
  background: var(--bg, #f7f8fa);
}

/* 明水印层：不遮挡交互 */
.wm-layer {
  position: fixed;
  inset: 0;
  z-index: 30;
  pointer-events: none;
  background-repeat: repeat;
}

.conv-panel {
  width: 320px;
  min-width: 260px;
  border-right: 1px solid var(--border-color, #e5e7eb);
  background: var(--bg-card, #fff);
  display: flex;
  flex-direction: column;
  z-index: 40;
}

.conv-head {
  padding: 14px 14px 10px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.conv-head h2 {
  margin: 0 0 10px;
  font-size: 17px;
}

.search-box {
  position: relative;
}

.search-box input {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 12px;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  background: var(--bg-secondary, #f1f3f5);
  font-size: 13px;
  outline: none;
}

.search-results {
  position: absolute;
  top: 42px;
  left: 0;
  right: 0;
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 10px;
  box-shadow: var(--shadow-sm, 0 2px 8px rgba(0, 0, 0, 0.08));
  z-index: 60;
  overflow: hidden;
}

.search-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  cursor: pointer;
}

.search-item:hover {
  background: var(--bg-hover, #f1f3f5);
}

.s-avatar,
.c-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--primary-color, #2b6de9);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  object-fit: cover;
  flex: none;
}

.s-name {
  font-weight: 600;
  font-size: 13px;
}

.s-uname {
  color: var(--text-muted, #888);
  font-size: 12px;
  margin-left: auto;
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
}

.conv-empty {
  text-align: center;
  color: var(--text-muted, #888);
  font-size: 13px;
  padding: 40px 10px;
  line-height: 1.8;
}

.conv-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 10px;
  cursor: pointer;
  align-items: center;
}

.conv-item:hover {
  background: var(--bg-hover, #f1f3f5);
}

.conv-item.active {
  background: var(--bg-active, #e8f0fe);
}

.c-main {
  flex: 1;
  min-width: 0;
}

.c-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.c-name {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.c-time {
  color: var(--text-muted, #888);
  font-size: 11px;
  flex: none;
}

.c-last {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-top: 3px;
}

.c-text {
  color: var(--text-secondary, #666);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.c-unread {
  background: var(--error, #e5484d);
  color: #fff;
  font-size: 11px;
  border-radius: 10px;
  padding: 1px 7px;
  flex: none;
}

/* ===== 聊天窗 ===== */
.chat-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  position: relative;
  z-index: 40;
  background: var(--bg, #f7f8fa);
}

.chat-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  background: var(--bg-card, #fff);
}

.back-btn {
  display: none;
  border: none;
  background: none;
  font-size: 18px;
  cursor: pointer;
  color: var(--text-primary, #111);
}

.ch-info {
  flex: 1;
  min-width: 0;
}

.ch-info b {
  font-size: 14px;
}

.ch-sub {
  display: block;
  color: var(--text-muted, #888);
  font-size: 11px;
}

.ch-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ws-state {
  font-size: 11px;
  color: var(--text-muted, #888);
}

.ws-state.open {
  color: var(--success, #30a46c);
}

.ws-state.connecting {
  color: var(--warning, #f5a524);
}

.msg-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  user-select: none;
  -webkit-user-select: none;
}

.msg-hint {
  text-align: center;
  color: var(--text-muted, #888);
  font-size: 12px;
}

.load-more {
  align-self: center;
  border: 1px solid var(--border-color, #e5e7eb);
  background: var(--bg-card, #fff);
  border-radius: 20px;
  padding: 6px 16px;
  font-size: 12px;
  cursor: pointer;
  color: var(--text-secondary, #666);
}

.msg-row {
  display: flex;
}

.msg-row.mine {
  justify-content: flex-end;
}

.bubble {
  max-width: 66%;
  padding: 9px 12px;
  border-radius: 12px;
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-color, #e5e7eb);
  position: relative;
  font-size: 13.5px;
  line-height: 1.55;
  overflow-wrap: break-word;
}

.msg-row.mine .bubble {
  background: var(--primary-color, #2b6de9);
  color: #fff;
  border-color: transparent;
}

.msg-row.bot .bubble {
  background: #fff7e6;
  border-color: #ffe1a8;
}

.msg-row.mine .msg-text :deep(a) {
  color: #fff;
}

.msg-text :deep(p) {
  margin: 0 0 6px;
}

.msg-text :deep(p:last-child) {
  margin-bottom: 0;
}

.msg-text :deep(pre) {
  background: rgba(0, 0, 0, 0.06);
  border-radius: 8px;
  padding: 8px;
  overflow-x: auto;
  font-size: 12px;
}

.bubble.recalled {
  background: var(--bg-secondary, #f1f3f5);
  color: var(--text-muted, #888);
  font-size: 12.5px;
  border-style: dashed;
}

.msg-img img {
  max-width: 240px;
  max-height: 240px;
  border-radius: 8px;
  display: block;
  cursor: zoom-in;
}

.zw-mark {
  font-size: 0;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 11px;
}

.m-time {
  opacity: 0.65;
}

.m-read {
  opacity: 0.85;
}

.m-recall,
.m-copy {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 11px;
  padding: 0;
  color: inherit;
  opacity: 0.75;
  text-decoration: underline;
}

.m-recall:hover,
.m-copy:hover {
  opacity: 1;
}

/* ===== 输入区 ===== */
.composer {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 14px;
  border-top: 1px solid var(--border-color, #e5e7eb);
  background: var(--bg-card, #fff);
}

.composer textarea {
  flex: 1;
  resize: none;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 13.5px;
  background: var(--bg-secondary, #f1f3f5);
  outline: none;
  color: var(--text-primary, #111);
  line-height: 1.5;
}

.img-btn {
  border: 1px solid var(--border-color, #e5e7eb);
  background: var(--bg-secondary, #f1f3f5);
  border-radius: 10px;
  width: 38px;
  height: 38px;
  font-size: 16px;
  cursor: pointer;
  flex: none;
}

/* ===== 空态 ===== */
.chat-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 40;
  position: relative;
}

.ce-inner {
  text-align: center;
  color: var(--text-muted, #888);
}

.ce-icon {
  font-size: 42px;
  margin-bottom: 10px;
}

.ce-sub {
  font-size: 12px;
  opacity: 0.75;
}

/* ===== 图片预览 ===== */
.img-preview {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  cursor: zoom-out;
}

.img-preview img {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: 8px;
}

/* ===== 移动端 ===== */
@media (max-width: 760px) {
  .conv-panel {
    width: 100%;
  }
  .chat-pane {
    position: fixed;
    inset: 60px 0 0 0;
  }
  .back-btn {
    display: block;
  }
}
</style>
