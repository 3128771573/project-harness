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
            <span class="muted small">{{ l.ip || '—' }} · {{ fmtTime(l.created_time) }}</span>
          </div>
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
  loadSessions()
  loadLogs()
})
</script>

<style scoped src="../assets/dashboard.css"></style>
<style scoped>
.panel {
  background: var(--card);
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
  background: #fafbfc;
  font-family: inherit;
}

.field input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(45, 108, 223, 0.15);
  background: #fff;
}

.btn.small {
  width: fit-content;
  padding: 10px 22px;
  font-size: 14px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.btn.tiny {
  padding: 5px 12px;
  font-size: 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #fff;
  cursor: pointer;
}

.btn.tiny.danger {
  color: var(--error);
  border-color: #fecaca;
  background: #fef2f2;
}

.msg {
  font-size: 13px;
  padding: 9px 12px;
  border-radius: 8px;
}

.msg.ok { background: #ecfdf5; color: #059669; }
.msg.err { background: #fef2f2; color: #dc2626; }

.session-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f1f5;
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
