<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">H</div>
      <nav>
        <router-link to="/dashboard" class="nav-item">仪表盘</router-link>
        <router-link to="/ai" class="nav-item">AI 对话</router-link>
        <router-link to="/settings" class="nav-item active">安全设置</router-link>
        <router-link v-if="isAdmin" to="/admin/dashboard" class="nav-item">管理后台</router-link>
      </nav>
      <button class="logout" @click="logout">退出登录</button>
    </aside>

    <main class="main" style="max-width: 760px">
      <header class="topbar">
        <h1>安全设置</h1>
      </header>

      <!-- 个人资料 -->
      <section class="panel">
        <div class="panel-head"><h3>个人资料</h3></div>
        <p class="sub">昵称、简介与头像会展示在平台各处</p>
        <form @submit.prevent="saveProfile" class="profile-form">
          <div class="avatar-row">
            <img v-if="profile.avatar" :src="profile.avatar" class="profile-avatar" alt="头像" />
            <div v-else class="profile-avatar placeholder">{{ initial }}</div>
            <div>
              <label class="avatar-upload">
                上传头像
                <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" hidden @change="onAvatarChange" />
              </label>
              <p class="upload-msg" v-if="uploadMsg">{{ uploadMsg }}</p>
            </div>
          </div>
          <label class="field">
            <span>昵称</span>
            <input v-model.trim="profile.nickname" maxlength="64" placeholder="你的昵称" />
          </label>
          <label class="field">
            <span>简介</span>
            <textarea v-model.trim="profile.bio" maxlength="2000" rows="3" placeholder="一句话介绍自己"></textarea>
          </label>
          <p v-if="profileMsg" :class="['msg', profileMsgOk ? 'ok' : 'err']">{{ profileMsg }}</p>
          <button type="submit" class="btn small" :disabled="profileSaving">{{ profileSaving ? '保存中…' : '保存资料' }}</button>
        </form>
      </section>

      <!-- 主题设置 -->
      <section class="panel">
        <div class="panel-head">
          <h3>外观主题</h3>
        </div>
        <p class="sub">选择全局主题，整个网站自动适配</p>
        <ThemeSwitcher />
      </section>

      <!-- 修改密码 -->
      <section class="panel">
        <h3>修改密码</h3>
        <p class="sub">修改后所有设备将强制下线，需要重新登录</p>
        <form @submit.prevent="changePwd" class="form-stack">
          <label class="field">
            <span>旧密码</span>
            <input v-model="pwd.old_password" type="password" required autocomplete="current-password" />
          </label>
          <label class="field">
            <span>新密码</span>
            <input v-model="pwd.new_password" type="password" required autocomplete="new-password" placeholder="至少8位，含大小写/数字/符号中3类" />
          </label>
          <label class="field">
            <span>确认新密码</span>
            <input v-model="pwd.confirm" type="password" required autocomplete="new-password" />
          </label>
          <p v-if="pwdMsg" :class="['msg', pwdMsgOk ? 'ok' : 'err']">{{ pwdMsg }}</p>
          <button type="submit" class="btn small" :disabled="pwdSaving">{{ pwdSaving ? '提交中…' : '修改密码' }}</button>
        </form>
      </section>

      <!-- 两步验证 -->
      <section class="panel">
        <div class="panel-head">
          <h3>两步验证（TOTP）</h3>
          <span v-if="twofa.enabled" class="badge ok">已开启</span>
        </div>
        <p class="sub">使用 iPhone 密码本 / Google Authenticator 等应用扫码绑定，登录时额外输入 6 位动态验证码</p>

        <div v-if="!twofa.enabled">
          <button class="btn small" :disabled="twofaLoading" @click="start2faSetup">
            {{ twofaLoading ? '处理中…' : '开启两步验证' }}
          </button>
        </div>
        <div v-else>
          <button class="btn tiny danger" :disabled="twofaLoading" @click="disable2fa">关闭两步验证</button>
        </div>

        <!-- 设置向导 -->
        <div v-if="setupState" class="twofa-setup">
          <img :src="setupState.qr_data_uri" alt="两步验证二维码" class="twofa-qr" />
          <p class="muted small">无法扫码？手动输入密钥：<code class="twofa-secret">{{ setupState.secret }}</code></p>
          <form @submit.prevent="confirm2fa" class="form-stack">
            <label class="field">
              <span>输入验证码确认绑定</span>
              <input
                v-model.trim="twofaCode"
                placeholder="6 位动态验证码"
                maxlength="8"
                required
                inputmode="numeric"
                autocomplete="one-time-code"
              />
            </label>
            <p v-if="twofaMsg" :class="['msg', twofaMsgOk ? 'ok' : 'err']">{{ twofaMsg }}</p>
            <button type="submit" class="btn small" :disabled="twofaLoading">{{ twofaLoading ? '验证中…' : '验证并开启' }}</button>
          </form>
        </div>
      </section>

      <!-- 登录设备 -->
      <section class="panel">
        <div class="panel-head">
          <h3>登录设备</h3>
          <button class="btn tiny danger" @click="logoutAll">退出所有设备</button>
        </div>
        <p class="sub">当前活跃会话（refresh token）</p>
        <div v-if="sessions.length === 0" class="muted empty">暂无会话记录</div>
        <div v-for="s in sessions" :key="s.id" class="session-row">
          <div class="session-info">
            <b>{{ s.device || '未知设备' }}</b>
            <span class="muted small">{{ s.ip || '—' }} · {{ fmtTime(s.created_time) }}</span>
          </div>
          <span v-if="s.revoked" class="badge disabled">已下线</span>
          <button v-else class="btn tiny" @click="revokeSession(s.id)">下线</button>
        </div>
      </section>

      <!-- 登录记录 -->
      <section class="panel">
        <h3>最近登录记录</h3>
        <div v-if="logs.length === 0" class="muted empty">暂无记录</div>
        <div v-for="l in logs" :key="l.id" class="session-row">
          <div class="session-info">
            <b>{{ l.device || '未知设备' }}</b>
            <span class="muted small">
              {{ l.ip || '—' }}<template v-if="l.ip_location"> · {{ l.ip_location }}</template> · {{ fmtTime(l.created_time) }}
            </span>
          </div>
          <span class="badge new" v-if="l.success && l.is_new_device" title="此前 30 天内未在该设备/IP 登录">新设备</span>
          <span :class="['badge', l.success ? 'ok' : 'disabled']">
            {{ l.success ? '成功' : (l.reason || '失败') }}
          </span>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'
import ThemeSwitcher from '../components/ThemeSwitcher.vue'

const router = useRouter()
const isAdmin = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('harness_user') || 'null')
    return ['admin', 'super_admin'].includes(u?.role)
  } catch {
    return false
  }
})

const pwd = reactive({ old_password: '', new_password: '', confirm: '' })
const pwdMsg = ref('')
const pwdMsgOk = ref(false)
const pwdSaving = ref(false)
const sessions = ref([])
const logs = ref([])

// ===== 两步验证（TOTP） =====
const twofa = ref({ enabled: false })
const setupState = ref(null)
const twofaCode = ref('')
const twofaMsg = ref('')
const twofaMsgOk = ref(false)
const twofaLoading = ref(false)

async function loadTwofa() {
  try {
    const { data } = await api.get('/user/2fa/status')
    twofa.value = data
  } catch { /* ignore */ }
}

async function start2faSetup() {
  const password = prompt('请输入当前密码以开启两步验证')
  if (!password) return
  twofaLoading.value = true
  try {
    const { data } = await api.post('/user/2fa/setup', { password })
    setupState.value = data
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  } finally {
    twofaLoading.value = false
  }
}

async function confirm2fa() {
  if (!twofaCode.value) return
  twofaLoading.value = true
  twofaMsg.value = ''
  try {
    const { data } = await api.post('/user/2fa/verify', { code: twofaCode.value })
    twofa.value = data
    setupState.value = null
    twofaCode.value = ''
    twofaMsgOk.value = true
    twofaMsg.value = '两步验证已开启 ✓'
  } catch (e) {
    twofaMsgOk.value = false
    twofaMsg.value = e.response?.data?.detail || '验证失败'
  } finally {
    twofaLoading.value = false
  }
}

async function disable2fa() {
  const password = prompt('请输入当前密码')
  if (!password) return
  const code = prompt('请输入当前动态验证码')
  if (!code) return
  twofaLoading.value = true
  try {
    const { data } = await api.post('/user/2fa/disable', { password, code })
    twofa.value = data
    alert('两步验证已关闭')
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  } finally {
    twofaLoading.value = false
  }
}

// ===== 个人资料 =====
const profile = reactive({ nickname: '', bio: '', avatar: '' })
const profileMsg = ref('')
const profileMsgOk = ref(false)
const profileSaving = ref(false)
const uploadMsg = ref('')

const initial = computed(() => {
  try {
    const u = JSON.parse(localStorage.getItem('harness_user') || 'null')
    return (u?.nickname || u?.username || u?.email || '?')[0].toUpperCase()
  } catch {
    return '?'
  }
})

function syncUser(data) {
  try {
    const u = JSON.parse(localStorage.getItem('harness_user') || 'null') || {}
    u.nickname = data.nickname
    u.avatar = data.avatar
    u.bio = data.bio
    localStorage.setItem('harness_user', JSON.stringify(u))
  } catch { /* ignore */ }
}

async function loadProfile() {
  try {
    const { data } = await api.get('/user/profile')
    profile.nickname = data.nickname || ''
    profile.bio = data.bio || ''
    profile.avatar = data.avatar || ''
  } catch { /* ignore */ }
}

async function saveProfile() {
  profileMsg.value = ''
  profileSaving.value = true
  try {
    const { data } = await api.put('/user/profile', {
      nickname: profile.nickname || null,
      bio: profile.bio || null,
    })
    profileMsgOk.value = true
    profileMsg.value = '资料已保存'
    syncUser(data)
  } catch (e) {
    profileMsgOk.value = false
    profileMsg.value = e.response?.data?.detail || '保存失败'
  } finally {
    profileSaving.value = false
  }
}

async function onAvatarChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    uploadMsg.value = '头像不能超过 2MB'
    e.target.value = ''
    return
  }
  uploadMsg.value = ''
  const fd = new FormData()
  fd.append('file', file)
  try {
    const { data } = await api.post('/user/avatar', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    profile.avatar = data.avatar
    uploadMsg.value = '头像已更新 ✓'
    syncUser(data)
  } catch (err) {
    uploadMsg.value = err.response?.data?.detail || '上传失败'
  } finally {
    e.target.value = ''
  }
}

function fmtTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

async function changePwd() {
  pwdMsg.value = ''
  if (pwd.new_password !== pwd.confirm) {
    pwdMsgOk.value = false
    pwdMsg.value = '两次输入的新密码不一致'
    return
  }
  pwdSaving.value = true
  try {
    const { data } = await api.put('/user/password', {
      old_password: pwd.old_password,
      new_password: pwd.new_password,
    })
    pwdMsgOk.value = true
    pwdMsg.value = data.message
    pwd.old_password = pwd.new_password = pwd.confirm = ''
    // 密码已修改，强制重新登录
    setTimeout(() => {
      localStorage.removeItem('harness_access')
      localStorage.removeItem('harness_refresh')
      localStorage.removeItem('harness_user')
      router.push('/login')
    }, 1500)
  } catch (e) {
    pwdMsgOk.value = false
    pwdMsg.value = e.response?.data?.detail || '修改失败'
  } finally {
    pwdSaving.value = false
  }
}

async function loadSessions() {
  try {
    const { data } = await api.get('/user/sessions')
    sessions.value = data
  } catch { /* ignore */ }
}

async function loadLogs() {
  try {
    const { data } = await api.get('/user/login-logs')
    logs.value = data.items
  } catch { /* ignore */ }
}

async function revokeSession(id) {
  try {
    await api.delete(`/user/sessions/${id}`)
    await loadSessions()
  } catch { /* ignore */ }
}

async function logoutAll() {
  try {
    await api.delete('/user/sessions')
    // 本会话也会失效，直接跳登录
    localStorage.removeItem('harness_access')
    localStorage.removeItem('harness_refresh')
    localStorage.removeItem('harness_user')
    router.push('/login')
  } catch { /* ignore */ }
}

function logout() {
  localStorage.removeItem('harness_access')
  localStorage.removeItem('harness_refresh')
  localStorage.removeItem('harness_user')
  router.push('/login')
}

onMounted(() => {
  loadProfile()
  loadTwofa()
  loadSessions()
  loadLogs()
})
</script>

<style scoped src="../assets/dashboard.css"></style>
<style scoped>
.panel {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 22px;
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}

.panel h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 6px;
}

.panel .sub {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 16px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.form-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 420px;
}

.profile-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--border);
}

.profile-avatar.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary), #7aa5f0);
  color: #fff;
  border: none;
}

/* 两步验证 */
.twofa-setup {
  margin-top: 18px;
  padding: 18px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.twofa-qr {
  width: 180px;
  height: 180px;
  background: #fff;
  border-radius: 10px;
  padding: 8px;
}

.twofa-secret {
  font-family: var(--font-mono);
  font-size: 12px;
  background: color-mix(in srgb, var(--text-primary) 8%, transparent);
  padding: 1px 6px;
  border-radius: 5px;
  word-break: break-all;
}

.twofa-setup .form-stack {
  width: 100%;
  max-width: 320px;
}

.badge.new {
  background: color-mix(in srgb, var(--warning) 15%, transparent);
  color: var(--warning);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field span {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
}

.field input {
  padding: 11px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 14px;
  background: var(--bg-input);
  font-family: inherit;
}

.field input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(45, 108, 223, 0.15);
  background: var(--bg-card);
}

.btn.small {
  width: fit-content;
  padding: 10px 22px;
  font-size: 14px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.btn.tiny {
  padding: 5px 12px;
  font-size: 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  cursor: pointer;
}

.btn.tiny.danger {
  color: var(--error);
  border-color: color-mix(in srgb, var(--error) 35%, transparent);
  background: color-mix(in srgb, var(--error) 10%, transparent);
}

.msg {
  font-size: 13px;
  padding: 9px 12px;
  border-radius: 8px;
}

.msg.ok { background: color-mix(in srgb, var(--success) 10%, transparent); color: var(--success); }
.msg.err { background: color-mix(in srgb, var(--error) 10%, transparent); color: var(--error); }

.session-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-light);
}

.session-row:last-child {
  border-bottom: none;
}

.session-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.badge.ok { background: #e8f7ee; color: var(--success); }
.badge.disabled { background: #feecec; color: var(--error); }

.empty {
  padding: 16px 0;
  font-size: 14px;
}

.small {
  font-size: 12px;
}
</style>
