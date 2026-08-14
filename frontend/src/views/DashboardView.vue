<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">H</div>
      <nav>
        <router-link to="/dashboard" class="nav-item">仪表盘</router-link>
        <router-link to="/ai" class="nav-item">AI 对话</router-link>
        <router-link to="/settings" class="nav-item">安全设置</router-link>
        <router-link v-if="isAdmin" to="/admin/dashboard" class="nav-item">管理后台</router-link>
      </nav>
      <button class="logout" @click="logout">退出登录</button>
    </aside>

    <main class="main">
      <header class="topbar">
        <h1>仪表盘</h1>
        <div class="user-chip">
          <img v-if="user?.avatar" :src="user.avatar" class="avatar-img" alt="avatar" />
          <span v-else class="avatar">{{ avatarChar }}</span>
          <span>{{ user?.nickname || user?.username }}</span>
        </div>
      </header>

      <section class="cards">
        <div class="card">
          <h3>UID</h3>
          <p class="big mono">{{ user?.uid }}</p>
        </div>
        <div class="card">
          <h3>用户名</h3>
          <p class="big">{{ user?.username }}</p>
        </div>
        <div class="card">
          <h3>邮箱</h3>
          <p class="big">{{ user?.email }}</p>
        </div>
        <div class="card">
          <h3>角色</h3>
          <p class="big"><span class="role-badge">{{ user?.role || 'user' }}</span></p>
        </div>
      </section>

      <section class="panel">
        <h3>个人资料</h3>
        <form @submit.prevent="saveProfile" class="profile-form">
          <label class="field">
            <span>昵称</span>
            <input v-model.trim="form.nickname" placeholder="你的昵称" maxlength="64" />
          </label>
          <label class="field">
            <span>个人简介</span>
            <textarea v-model.trim="form.bio" placeholder="介绍一下自己" rows="3" maxlength="2000"></textarea>
          </label>
          <div class="avatar-row">
            <label class="avatar-upload">
              上传头像
              <input type="file" accept="image/*" hidden @change="uploadAvatar" />
            </label>
            <span v-if="uploadMsg" class="upload-msg">{{ uploadMsg }}</span>
          </div>
          <button type="submit" class="btn small" :disabled="saving">
            {{ saving ? '保存中…' : '保存资料' }}
          </button>
        </form>
      </section>

      <section class="panel">
        <h3>Phase 状态</h3>
        <ul class="status-list">
          <li><span class="dot ok"></span>用户系统 v0.6（注册 / 登录 / 双 Token / RBAC）</li>
          <li><span class="dot ok"></span>AI 模块（聊天 + 历史记录）</li>
          <li><span class="dot soon"></span>Admin 后台 —— 接口就绪，页面规划中</li>
          <li><span class="dot soon"></span>Demo 平台 —— 规划中</li>
        </ul>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'

const router = useRouter()
const user = ref(null)
const form = reactive({ nickname: '', bio: '' })
const saving = ref(false)
const uploadMsg = ref('')

const avatarChar = computed(() => (user.value?.username?.[0] || 'U').toUpperCase())
const isAdmin = computed(() => ['admin', 'super_admin'].includes(user.value?.role))

async function loadProfile() {
  try {
    const { data } = await api.get('/user/profile')
    user.value = data
    form.nickname = data.nickname || ''
    form.bio = data.bio || ''
    localStorage.setItem('harness_user', JSON.stringify(data))
  } catch {
    /* interceptor 已处理 401 */
  }
}

async function saveProfile() {
  saving.value = true
  try {
    const { data } = await api.put('/user/profile', form)
    user.value = data
    localStorage.setItem('harness_user', JSON.stringify(data))
    uploadMsg.value = '资料已保存'
  } catch (e) {
    uploadMsg.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

async function uploadAvatar(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  try {
    const { data } = await api.post('/user/avatar', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    user.value = data
    localStorage.setItem('harness_user', JSON.stringify(data))
    uploadMsg.value = '头像已更新'
  } catch (err) {
    uploadMsg.value = err.response?.data?.detail || '头像上传失败'
  }
}

function logout() {
  localStorage.removeItem('harness_access')
  localStorage.removeItem('harness_refresh')
  localStorage.removeItem('harness_user')
  router.push('/login')
}

onMounted(loadProfile)
</script>

<style scoped src="../assets/dashboard.css"></style>
