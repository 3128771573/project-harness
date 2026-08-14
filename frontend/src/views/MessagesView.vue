<template>
  <div class="messages-page">
    <!-- 明水印层（昵称 + UID + 时间，防截图传播） -->
    <div class="wm-layer" :style="wmBackground" aria-hidden="true"></div>

    <aside class="conv-panel">
      <div class="conv-head">
        <div class="mode-tabs">
          <button :class="{ on: viewMode === 'dm' }" @click="switchMode('dm')">私信</button>
          <button :class="{ on: viewMode === 'group' }" @click="switchMode('group')">群聊</button>
        </div>
        <div v-if="viewMode === 'dm'" class="search-box">
          <input
            v-model="searchQ"
            placeholder="搜索用户发起私信…"
            @input="onSearch"
            @focus="searchFocus = true"
            @blur="onSearchBlur"
          />
          <div v-if="searchFocus && searchResults.length" class="search-results">
            <div v-for="u in searchResults" :key="u.uid" class="search-item" @mousedown.prevent="startWith(u)">
              <img v-if="u.avatar" :src="u.avatar" class="s-avatar" alt="" />
              <span v-else class="s-avatar">{{ (u.nickname || u.username)[0] }}</span>
              <span class="s-name">{{ u.nickname || u.username }}</span>
              <span class="s-uname">@{{ u.username }}</span>
            </div>
          </div>
        </div>
        <div v-else class="group-create-bar">
          <button class="btn primary sm" @click="createOpen = true">＋ 创建群聊</button>
        </div>
      </div>

      <div v-if="viewMode === 'dm'" class="conv-list">
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

      <div v-else class="conv-list">
        <div v-if="!groups.length && !gLoading" class="conv-empty">
          暂无群聊<br /><span>点击上方创建群聊</span>
        </div>
        <div
          v-for="g in groups"
          :key="g.id"
          class="conv-item"
          :class="{ active: activeGroup && activeGroup.id === g.id }"
          @click="openGroup(g)"
        >
          <span class="c-avatar g-avatar" title="群聊">👥</span>
          <div class="c-main">
            <div class="c-top">
              <b class="c-name">{{ g.name }}</b>
              <span class="c-time">{{ fmtListTime(g.last_message_at || g.created_time) }}</span>
            </div>
            <div class="c-last">
              <span class="c-text">{{ groupLastText(g) }}</span>
              <span class="g-count">{{ g.member_count }} 人</span>
              <span v-if="g.unread > 0" class="c-unread">{{ g.unread > 99 ? '99+' : g.unread }}</span>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- ===== 私信聊天窗 ===== -->
    <section v-if="viewMode === 'dm' && active" class="chat-pane">
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
        <div v-for="m in msgs" :key="m.id" class="msg-row" :class="{ mine: m.sender_id === me.uid, bot: m.sender_id === BOT_UID }">
          <div class="bubble" :class="{ recalled: m.status === 'recalled', removed: m.status === 'removed' }">
            <template v-if="m.status === 'recalled'">
              <span class="recalled-text">{{ m.sender_id === me.uid ? '你撤回了一条消息' : '对方撤回了一条消息' }}</span>
            </template>
            <template v-else-if="m.status === 'removed'">
              <span class="recalled-text">该消息已被管理员删除</span>
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
        <input ref="imgInput" type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden @change="onImage" />
        <textarea v-model="draft" rows="2" maxlength="4000" placeholder="输入消息…（Enter 发送，Shift+Enter 换行）" @keydown.enter.exact.prevent="sendText"></textarea>
        <button class="btn primary" :disabled="sending || !draft.trim()" @click="sendText">发送</button>
      </div>
    </section>

    <!-- ===== 群聊天窗 ===== -->
    <section v-else-if="viewMode === 'group' && activeGroup" class="chat-pane">
      <header class="chat-head">
        <button class="back-btn" @click="closeGroupChat" title="返回列表">←</button>
        <span class="c-avatar g-avatar" title="群聊">👥</span>
        <div class="ch-info">
          <b>{{ activeGroup.name }}</b>
          <span class="ch-sub">{{ activeGroup.member_count }} 人 · {{ roleLabel(activeGroup.my_role) }}<template v-if="activeGroup.announcement"> · 公告：{{ truncate(activeGroup.announcement, 24) }}</template></span>
        </div>
        <div class="ch-actions">
          <span class="ws-state" :class="wsState">{{ wsLabel }}</span>
          <button class="btn ghost sm" @click="loadGroupDetail">群设置</button>
        </div>
      </header>
      <div class="msg-area" @contextmenu.prevent @copy.prevent @dragstart.prevent>
        <div v-if="gLoadingMsgs" class="msg-hint">加载中…</div>
        <button v-else-if="gHasMore" class="load-more" @click="loadGOlder">加载更早消息</button>
        <div v-for="m in gmsgs" :key="m.id" class="msg-row" :class="{ mine: m.sender_id === me.uid }">
          <div class="bubble" :class="{ recalled: m.status === 'recalled', removed: m.status === 'removed' }">
            <template v-if="m.status === 'recalled'">
              <span class="recalled-text">{{ m.sender_id === me.uid ? '你撤回了一条消息' : senderName(m.sender_id) + ' 撤回了一条消息' }}</span>
            </template>
            <template v-else-if="m.status === 'removed'">
              <span class="recalled-text">该消息已被管理员删除</span>
            </template>
            <template v-else>
              <div v-if="m.sender_id !== me.uid" class="g-sender">{{ senderName(m.sender_id) }}</div>
              <div v-if="m.kind === 'image'" class="msg-img">
                <img :src="m.content" alt="图片消息" @click="previewUrl = m.content" />
              </div>
              <div v-else class="msg-text" v-html="mdHtml(m)"></div>
              <span class="zw-mark" aria-hidden="true">{{ zwFor(m) }}</span>
            </template>
            <div class="msg-meta">
              <span class="m-time">{{ fmtMsgTime(m.created_time) }}</span>
              <button v-if="canRecall(m)" class="m-recall" @click="recallGroupMsg(m)">撤回</button>
              <button v-if="m.sender_id !== me.uid && m.status === 'active'" class="m-recall" @click="reportGroupMsg(m)">举报</button>
              <button v-if="m.status === 'active'" class="m-copy" @click="copyMsg(m)" title="复制消息（含溯源水印）">复制</button>
            </div>
          </div>
        </div>
      </div>
      <div class="composer">
        <button class="img-btn" title="发送图片（≤5MB）" @click="gImgInput.click()">🖼</button>
        <input ref="gImgInput" type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden @change="onGroupImage" />
        <textarea v-model="gDraft" rows="2" maxlength="4000" placeholder="发送到群聊…（Enter 发送，Shift+Enter 换行）" @keydown.enter.exact.prevent="sendGroupText"></textarea>
        <button class="btn primary" :disabled="gSending || !gDraft.trim()" @click="sendGroupText">发送</button>
      </div>
    </section>

    <section v-else class="chat-empty">
      <div class="ce-inner">
        <div class="ce-icon">💬</div>
        <p>{{ viewMode === 'dm' ? '选择左侧会话，或搜索用户发起私信' : '选择左侧群聊，或创建新群' }}</p>
        <p class="ce-sub">消息页已启用明水印 + 文本溯源水印，截图/复制均可追溯</p>
      </div>
    </section>

    <!-- ===== 群设置模态 ===== -->
    <div v-if="groupInfoOpen" class="modal-mask" @click.self="groupInfoOpen = false">
      <div class="modal-panel ginfo">
        <div class="panel-title">群设置
          <button class="x" @click="groupInfoOpen = false">✕</button>
        </div>
        <div class="ginfo-section" v-if="canManageGroup">
          <label class="field"><span>群名</span><input v-model="gEditName" maxlength="64" /></label>
          <label class="field"><span>群公告</span><textarea v-model="gEditAnnouncement" rows="2" maxlength="2000"></textarea></label>
          <button class="btn sm" :disabled="gSavingInfo" @click="saveGroupInfo">{{ gSavingInfo ? '保存中…' : '保存' }}</button>
        </div>
        <div class="ginfo-members">
          <div v-for="m in gDetail.members" :key="m.user.uid" class="gmember">
            <img v-if="m.user.avatar" :src="m.user.avatar" class="s-avatar" alt="" />
            <span v-else class="s-avatar">{{ (m.user.nickname || m.user.username)[0] }}</span>
            <span class="gm-name">{{ m.user.nickname || m.user.username }}
              <span class="gm-role" :class="m.role">{{ roleLabel(m.role) }}</span>
              <span v-if="m.user.uid === me.uid" class="gm-me">（我）</span>
            </span>
            <template v-if="canManageGroup && m.user.uid !== me.uid && m.role !== 'owner'">
              <button class="btn ghost sm" @click="kickUser(m)">踢出</button>
              <button v-if="activeGroup.my_role === 'owner'" class="btn ghost sm" @click="transferOwner(m)">转让</button>
            </template>
          </div>
        </div>
        <div class="ginfo-actions">
          <button class="btn sm" @click="inviteOpen = true">邀请成员</button>
          <button v-if="activeGroup.my_role !== 'owner'" class="btn ghost sm danger" @click="leaveGroup">退出群聊</button>
          <button v-if="activeGroup.my_role === 'owner'" class="btn ghost sm danger" @click="disbandGroup">解散群</button>
        </div>
      </div>
    </div>

    <!-- ===== 创建群模态 ===== -->
    <div v-if="createOpen" class="modal-mask" @click.self="createOpen = false">
      <div class="modal-panel">
        <div class="panel-title">创建群聊
          <button class="x" @click="createOpen = false">✕</button>
        </div>
        <label class="field"><span>群名称</span><input v-model="gName" maxlength="64" placeholder="群名称" /></label>
        <div class="invite-search">
          <input v-model="inviteQ" placeholder="搜索用户添加成员（可多选）" @input="onInviteSearch" />
          <div v-if="inviteResults.length" class="search-results">
            <div v-for="u in inviteResults" :key="u.uid" class="search-item" @mousedown.prevent="togglePick(u)">
              <img v-if="u.avatar" :src="u.avatar" class="s-avatar" alt="" />
              <span v-else class="s-avatar">{{ (u.nickname || u.username)[0] }}</span>
              <span class="s-name">{{ u.nickname || u.username }}</span>
              <span class="s-uname">@{{ u.username }}</span>
              <span v-if="picked.some((p) => p.uid === u.uid)" class="picked">✓</span>
            </div>
          </div>
        </div>
        <div v-if="picked.length" class="picked-list">
          <span v-for="p in picked" :key="p.uid" class="pick-chip">
            {{ p.nickname || p.username }} <b @click="unpick(p)">×</b>
          </span>
        </div>
        <div class="actions">
          <button class="btn primary" :disabled="!gName.trim() || gCreating" @click="createGroup">{{ gCreating ? '创建中…' : '创建' }}</button>
        </div>
      </div>
    </div>

    <!-- ===== 邀请成员模态 ===== -->
    <div v-if="inviteOpen" class="modal-mask" @click.self="inviteOpen = false">
      <div class="modal-panel">
        <div class="panel-title">邀请成员加入「{{ activeGroup ? activeGroup.name : '' }}」
          <button class="x" @click="inviteOpen = false">✕</button>
        </div>
        <div class="invite-search">
          <input v-model="inviteQ" placeholder="搜索用户（可多选）" @input="onInviteSearch" />
          <div v-if="inviteResults.length" class="search-results">
            <div v-for="u in inviteResults" :key="u.uid" class="search-item" @mousedown.prevent="togglePick(u)">
              <img v-if="u.avatar" :src="u.avatar" class="s-avatar" alt="" />
              <span v-else class="s-avatar">{{ (u.nickname || u.username)[0] }}</span>
              <span class="s-name">{{ u.nickname || u.username }}</span>
              <span class="s-uname">@{{ u.username }}</span>
              <span v-if="picked.some((p) => p.uid === u.uid)" class="picked">✓</span>
            </div>
          </div>
        </div>
        <div v-if="picked.length" class="picked-list">
          <span v-for="p in picked" :key="p.uid" class="pick-chip">
            {{ p.nickname || p.username }} <b @click="unpick(p)">×</b>
          </span>
        </div>
        <div class="actions">
          <button class="btn primary" :disabled="!picked.length || gInviting" @click="doInvite">{{ gInviting ? '邀请中…' : '邀请' }}</button>
        </div>
      </div>
    </div>

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

// ===== 模式切换（私信 / 群聊） =====
const viewMode = ref('dm')

function switchMode(m) {
  viewMode.value = m
  if (m === 'group') {
    loadGroups()
  }
}

// ===== 私信：会话列表 =====
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
  if (lm.status === 'removed') return '该消息已被管理员删除'
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

function truncate(s, n) {
  if (!s) return ''
  return s.length > n ? s.slice(0, n) + '…' : s
}

// ===== 私信：用户搜索 =====
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

// ===== 群聊：列表 =====
const groups = ref([])
const gLoading = ref(false)
const activeGroup = ref(null)
const gmsgs = ref([])
const gHasMore = ref(false)
const gLoadingMsgs = ref(false)
const gDraft = ref('')
const gSending = ref(false)
const gImgInput = ref(null)
const gSenderNames = new Map()

async function loadGroups() {
  gLoading.value = true
  try {
    const { data } = await api.get('/im/groups')
    groups.value = data.items || []
    if (activeGroup.value) {
      const upd = groups.value.find((g) => g.id === activeGroup.value.id)
      if (upd) {
        activeGroup.value.member_count = upd.member_count
        activeGroup.value.unread = upd.unread
        activeGroup.value.last_message_at = upd.last_message_at
        activeGroup.value.last_message = upd.last_message
        activeGroup.value.announcement = upd.announcement
      }
    }
  } catch {
    /* ignore */
  } finally {
    gLoading.value = false
  }
}

async function openGroup(g) {
  activeGroup.value = g
  await Promise.all([loadGMsgs(g), markGroupRead(g)])
  joinGroupRoom(g.id)
}

async function closeGroupChat() {
  if (activeGroup.value) leaveGroupRoom(activeGroup.value.id)
  activeGroup.value = null
  gmsgs.value = []
  gSenderNames.clear()
}

async function loadGMsgs(g) {
  gLoadingMsgs.value = true
  try {
    const { data } = await api.get('/im/groups/' + g.id + '/messages?limit=50')
    gmsgs.value = (data.items || []).slice().reverse()
    gHasMore.value = data.has_more
    buildSenderNames()
    await nextTick()
    scrollBottom(true)
  } catch {
    /* ignore */
  } finally {
    gLoadingMsgs.value = false
  }
}

async function loadGOlder() {
  if (!activeGroup.value || !gmsgs.value.length) return
  const before = gmsgs.value[0].created_time
  try {
    const { data } = await api.get(
      '/im/groups/' + activeGroup.value.id + '/messages?limit=50&before=' + encodeURIComponent(before)
    )
    const older = (data.items || []).slice().reverse()
    const known = new Set(gmsgs.value.map((m) => m.id))
    gmsgs.value = older.filter((m) => !known.has(m.id)).concat(gmsgs.value)
    gHasMore.value = data.has_more
  } catch {
    /* ignore */
  }
}

async function markGroupRead(g) {
  try {
    await api.post('/im/groups/' + g.id + '/read')
    g.unread = 0
  } catch {
    /* ignore */
  }
}

async function sendGroupText() {
  const text = gDraft.value.trim()
  if (!text || gSending.value || !activeGroup.value) return
  gSending.value = true
  try {
    const { data } = await api.post('/im/groups/' + activeGroup.value.id + '/messages', {
      kind: 'text',
      content: text,
    })
    gDraft.value = ''
    upsertGMsg(data)
    touchGroup(data)
  } catch (e) {
    alert(e.response?.data?.detail || '发送失败')
  } finally {
    gSending.value = false
  }
}

async function onGroupImage(ev) {
  const file = ev.target.files?.[0]
  ev.target.value = ''
  if (!file || !activeGroup.value) return
  if (file.size > 5 * 1024 * 1024) {
    alert('图片不能超过 5MB')
    return
  }
  const fd = new FormData()
  fd.append('file', file)
  gSending.value = true
  try {
    const up = await api.post('/im/upload', fd)
    const { data } = await api.post('/im/groups/' + activeGroup.value.id + '/messages', {
      kind: 'image',
      content: up.data.url,
    })
    upsertGMsg(data)
    touchGroup(data)
  } catch (e) {
    alert(e.response?.data?.detail || '图片发送失败')
  } finally {
    gSending.value = false
  }
}

async function recallGroupMsg(m) {
  if (!confirm('确定撤回这条消息？')) return
  try {
    await api.post('/im/group-messages/' + m.id + '/recall')
    m.status = 'recalled'
    const g = groups.value.find((x) => x.id === activeGroup.value?.id)
    if (g && g.last_message && g.last_message.id === m.id) g.last_message.status = 'recalled'
  } catch (e) {
    alert(e.response?.data?.detail || '撤回失败')
  }
}

async function reportGroupMsg(m) {
  const reason = prompt('举报原因（100 字内，将进入管理员审核队列）：')
  if (!reason) return
  try {
    await api.post('/im/group-messages/' + m.id + '/report', { reason: reason.slice(0, 200) })
    alert('已提交举报，管理员将尽快处理')
  } catch (e) {
    alert(e.response?.data?.detail || '举报失败')
  }
}

function upsertGMsg(m) {
  if (!gmsgs.value.some((x) => x.id === m.id)) gmsgs.value.push(m)
}

function touchGroup(m) {
  const g = groups.value.find((x) => x.id === activeGroup.value?.id)
  if (g) {
    g.last_message = m
    g.last_message_at = m.created_time
    groups.value = [g].concat(groups.value.filter((x) => x.id !== g.id))
  }
}

function groupLastText(g) {
  const lm = g.last_message
  if (!lm) return '暂无消息'
  if (lm.status === 'recalled') return '已撤回一条消息'
  if (lm.status === 'removed') return '该消息已被管理员删除'
  if (lm.kind === 'image') return '[图片]'
  const s = lm.content.replace(/\n/g, ' ')
  return s.length > 24 ? s.slice(0, 24) + '…' : s
}

function roleLabel(r) {
  if (r === 'owner') return '群主'
  if (r === 'admin') return '管理员'
  return '成员'
}

function buildSenderNames() {
  gSenderNames.clear()
  const d = gDetail.value
  if (d && d.members) {
    for (const m of d.members) gSenderNames.set(m.user.uid, m.user.nickname || m.user.username)
  }
}

function senderName(uid) {
  return gSenderNames.get(uid) || '群成员'
}

// ===== 群聊：设置 / 成员管理 =====
const groupInfoOpen = ref(false)
const gDetail = ref({ members: [] })
const gEditName = ref('')
const gEditAnnouncement = ref('')
const gSavingInfo = ref(false)

const myRole = computed(() => activeGroup.value?.my_role || 'member')
const canManageGroup = computed(() => myRole.value === 'owner' || myRole.value === 'admin')

async function loadGroupDetail() {
  if (!activeGroup.value) return
  try {
    const { data } = await api.get('/im/groups/' + activeGroup.value.id)
    gDetail.value = data
    gEditName.value = data.name
    gEditAnnouncement.value = data.announcement || ''
    buildSenderNames()
    groupInfoOpen.value = true
  } catch (e) {
    alert(e.response?.data?.detail || '加载群信息失败')
  }
}

async function saveGroupInfo() {
  gSavingInfo.value = true
  try {
    const payload = {}
    if (gEditName.value.trim() && gEditName.value.trim() !== gDetail.value.name) {
      payload.name = gEditName.value.trim()
    }
    if (gEditAnnouncement.value !== (gDetail.value.announcement || '')) {
      payload.announcement = gEditAnnouncement.value
    }
    if (Object.keys(payload).length) {
      const { data } = await api.put('/im/groups/' + activeGroup.value.id, payload)
      activeGroup.value.name = data.name
      activeGroup.value.announcement = data.announcement
      const g = groups.value.find((x) => x.id === activeGroup.value.id)
      if (g) {
        g.name = data.name
        g.announcement = data.announcement
      }
      alert('已保存')
    }
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  } finally {
    gSavingInfo.value = false
  }
}

async function kickUser(m) {
  if (!confirm('将 ' + (m.user.nickname || m.user.username) + ' 踢出群聊？')) return
  try {
    const { data } = await api.post('/im/groups/' + activeGroup.value.id + '/kick', { user_id: m.user.uid })
    gDetail.value = data
    loadGroups()
    alert('已踢出')
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

async function transferOwner(m) {
  if (!confirm('将群主转让给 ' + (m.user.nickname || m.user.username) + '？转让后你将变为管理员。')) return
  try {
    const { data } = await api.post('/im/groups/' + activeGroup.value.id + '/transfer', { user_id: m.user.uid })
    gDetail.value = data
    activeGroup.value.my_role = 'admin'
    const g = groups.value.find((x) => x.id === activeGroup.value.id)
    if (g) g.my_role = 'admin'
    loadGroups()
    alert('已转让')
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

async function leaveGroup() {
  if (!confirm('确定退出群聊「' + activeGroup.value.name + '」？')) return
  try {
    await api.post('/im/groups/' + activeGroup.value.id + '/leave')
    groups.value = groups.value.filter((g) => g.id !== activeGroup.value.id)
    groupInfoOpen.value = false
    closeGroupChat()
    alert('已退出群聊')
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

async function disbandGroup() {
  if (!confirm('解散群「' + activeGroup.value.name + '」将删除全部群消息且不可恢复，确定？')) return
  try {
    await api.delete('/im/groups/' + activeGroup.value.id)
    groups.value = groups.value.filter((g) => g.id !== activeGroup.value.id)
    groupInfoOpen.value = false
    closeGroupChat()
    alert('群已解散')
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

// ===== 创建群 / 邀请（共用搜索多选） =====
const createOpen = ref(false)
const inviteOpen = ref(false)
const gName = ref('')
const gCreating = ref(false)
const gInviting = ref(false)
const inviteQ = ref('')
const inviteResults = ref([])
const picked = ref([])
let inviteTimer = null

function onInviteSearch() {
  clearTimeout(inviteTimer)
  const q = inviteQ.value.trim()
  if (!q) {
    inviteResults.value = []
    return
  }
  inviteTimer = setTimeout(async () => {
    try {
      const { data } = await api.get('/im/users?q=' + encodeURIComponent(q))
      inviteResults.value = (data.items || []).filter((u) => !gDetail.value.members?.some((m) => m.user.uid === u.uid))
    } catch {
      inviteResults.value = []
    }
  }, 300)
}

function togglePick(u) {
  const i = picked.value.findIndex((p) => p.uid === u.uid)
  if (i >= 0) {
    picked.value.splice(i, 1)
  } else {
    picked.value.push(u)
  }
}

function unpick(p) {
  picked.value = picked.value.filter((x) => x.uid !== p.uid)
}

async function createGroup() {
  gCreating.value = true
  try {
    const { data } = await api.post('/im/groups', {
      name: gName.value.trim(),
      member_uids: picked.value.map((p) => p.uid),
    })
    createOpen.value = false
    gName.value = ''
    picked.value = []
    inviteQ.value = ''
    await loadGroups()
    openGroup(data)
    alert('群「' + data.name + '」创建成功')
  } catch (e) {
    alert(e.response?.data?.detail || '创建失败')
  } finally {
    gCreating.value = false
  }
}

async function doInvite() {
  gInviting.value = true
  try {
    const { data } = await api.post('/im/groups/' + activeGroup.value.id + '/invite', {
      user_ids: picked.value.map((p) => p.uid),
    })
    gDetail.value = data
    inviteOpen.value = false
    picked.value = []
    inviteQ.value = ''
    loadGroups()
    alert('邀请成功')
  } catch (e) {
    alert(e.response?.data?.detail || '邀请失败')
  } finally {
    gInviting.value = false
  }
}

// ===== WebSocket 实时通道 =====
const wsState = ref('closed')
const ws = ref(null)
let wsTimer = null
let wsPingTimer = null
let retry = 0
let joinedCid = null
let joinedGid = null
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
    clearInterval(wsPingTimer)
    wsPingTimer = setInterval(() => {
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        ws.value.send(JSON.stringify({ type: 'ping' }))
      }
    }, 25000)
    if (active.value) joinRoom(active.value.id)
    if (activeGroup.value) joinGroupRoom(activeGroup.value.id)
    loadConvs()
    loadGroups()
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
    joinedGid = null
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

function joinGroupRoom(gid) {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    if (joinedGid && joinedGid !== gid) leaveGroupRoom(joinedGid)
    ws.value.send(JSON.stringify({ type: 'join', group_id: gid }))
    joinedGid = gid
  }
}

function leaveGroupRoom(gid) {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({ type: 'leave', group_id: gid }))
  }
  if (joinedGid === gid) joinedGid = null
}

function handleWsEvent(e) {
  if (e.type === 'im.message') {
    const cid = e.conversation_id
    if (viewMode.value === 'dm' && active.value && cid === active.value.id) {
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
    if (m) m.status = 'recalled'
    const c = convs.value.find((x) => x.id === e.conversation_id)
    if (c && c.last_message && c.last_message.id === e.message_id) c.last_message.status = 'recalled'
  } else if (e.type === 'im.read') {
    if (active.value && e.conversation_id === active.value.id) {
      active.value.other_last_read_at = new Date().toISOString()
    }
  } else if (e.type === 'im.conv_update') {
    clearTimeout(reloadTimer)
    reloadTimer = setTimeout(loadConvs, 500)
  } else if (e.type === 'im.group_message') {
    const gid = e.group_id
    if (viewMode.value === 'group' && activeGroup.value && gid === activeGroup.value.id) {
      if (!gmsgs.value.some((m) => m.id === e.message.id)) {
        gmsgs.value.push(e.message)
        scrollBottom(false)
      }
      markGroupRead(activeGroup.value)
    } else {
      const g = groups.value.find((x) => x.id === gid)
      if (g) {
        g.unread += 1
        g.last_message = e.message
        g.last_message_at = e.message.created_time
        groups.value = [g].concat(groups.value.filter((x) => x.id !== g.id))
      } else {
        loadGroups()
      }
    }
  } else if (e.type === 'im.group_recalled') {
    const m = gmsgs.value.find((x) => x.id === e.message_id)
    if (m) m.status = 'recalled'
    const g = groups.value.find((x) => x.id === e.group_id)
    if (g && g.last_message && g.last_message.id === e.message_id) g.last_message.status = 'recalled'
  } else if (e.type === 'im.group_update') {
    clearTimeout(reloadTimer)
    reloadTimer = setTimeout(loadGroups, 500)
  } else if (e.type === 'im.group_invited') {
    loadGroups()
  } else if (e.type === 'im.group_kicked' || e.type === 'im.group_disbanded') {
    if (activeGroup.value && e.group_id === activeGroup.value.id) {
      groupInfoOpen.value = false
      closeGroupChat()
    }
    groups.value = groups.value.filter((g) => g.id !== e.group_id)
    alert(e.type === 'im.group_kicked' ? '你已被移出群聊' : '群聊已解散')
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

.mode-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.mode-tabs button {
  flex: 1;
  padding: 7px 0;
  border: 1px solid var(--border-color, #e5e7eb);
  background: var(--bg-secondary, #f1f3f5);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  color: var(--text-secondary, #666);
}

.mode-tabs button.on {
  background: var(--primary-color, #2b6de9);
  color: #fff;
  border-color: transparent;
}

.group-create-bar {
  display: flex;
}

.group-create-bar .btn {
  flex: 1;
}

.search-box {
  position: relative;
}

.search-box input,
.invite-search input {
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

.g-avatar {
  background: linear-gradient(135deg, #7b5cd6, #4a9de9);
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

.picked {
  color: var(--success, #30a46c);
  font-weight: 700;
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
  flex: 1;
}

.g-count {
  color: var(--text-muted, #888);
  font-size: 11px;
  flex: none;
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

.bubble.recalled,
.bubble.removed {
  background: var(--bg-secondary, #f1f3f5);
  color: var(--text-muted, #888);
  font-size: 12.5px;
  border-style: dashed;
}

.g-sender {
  font-size: 11px;
  color: var(--text-muted, #888);
  margin-bottom: 3px;
  font-weight: 600;
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

/* ===== 模态 ===== */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.modal-panel {
  background: var(--bg-card, #fff);
  border-radius: 14px;
  padding: 18px;
  width: min(440px, 92vw);
  max-height: 80vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel-title {
  font-size: 15px;
  font-weight: 700;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title .x {
  border: none;
  background: none;
  font-size: 15px;
  cursor: pointer;
  color: var(--text-muted, #888);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field > span {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted, #888);
}

.field input,
.field textarea,
.modal-panel > input {
  padding: 8px 12px;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  font-size: 13.5px;
  background: var(--bg-secondary, #f1f3f5);
  color: var(--text-primary, #111);
  font-family: inherit;
  outline: none;
  resize: vertical;
}

.ginfo-members {
  border-top: 1px solid var(--border-color, #e5e7eb);
  padding-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
}

.gmember {
  display: flex;
  align-items: center;
  gap: 10px;
}

.gm-name {
  flex: 1;
  font-size: 13.5px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gm-role {
  font-size: 10.5px;
  border-radius: 8px;
  padding: 1px 7px;
  margin-left: 6px;
  background: var(--bg-secondary, #f1f3f5);
  color: var(--text-muted, #888);
}

.gm-role.owner {
  background: #ffe9c7;
  color: #b36b00;
}

.gm-role.admin {
  background: #dbeafe;
  color: #1d4ed8;
}

.gm-me {
  color: var(--text-muted, #888);
  font-size: 11px;
}

.ginfo-actions {
  border-top: 1px solid var(--border-color, #e5e7eb);
  padding-top: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.invite-search {
  position: relative;
}

.picked-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pick-chip {
  background: var(--bg-active, #e8f0fe);
  border-radius: 12px;
  padding: 3px 10px;
  font-size: 12px;
}

.pick-chip b {
  cursor: pointer;
  margin-left: 4px;
  color: var(--text-muted, #888);
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
