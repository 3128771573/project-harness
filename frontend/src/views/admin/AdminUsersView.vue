<template>
  <div>
    <header class="page-head">
      <div>
        <h1>用户管理</h1>
        <p class="sub">共 {{ total }} 位用户</p>
      </div>
      <div class="actions">
        <div class="search-box">
          <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
          <input v-model.trim="keyword" placeholder="搜索用户名 / 邮箱" @keyup.enter="search" />
        </div>
        <button class="btn primary" @click="search">搜索</button>
      </div>
    </header>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>用户</th>
            <th>UID</th>
            <th>角色</th>
            <th>注册时间</th>
            <th>状态</th>
            <th style="text-align:right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in items" :key="u.uid">
            <td>
              <div class="user-cell">
                <span class="user-avatar">{{ initial(u.username) }}</span>
                <div>
                  <div class="name">{{ u.username }}</div>
                  <div class="email">{{ u.email }}</div>
                </div>
              </div>
            </td>
            <td>
              <span class="uid-cell" :title="u.uid">{{ shortUid(u.uid) }}</span>
            </td>
            <td>
              <span :class="['role-badge', roleClass(u.role)]">{{ u.role || 'user' }}</span>
            </td>
            <td class="muted">{{ formatTime(u.created_time) }}</td>
            <td>
              <span :class="['status-badge', u.is_active ? 'active' : 'disabled']">
                {{ u.is_active ? '正常' : '已禁用' }}
              </span>
            </td>
            <td style="text-align:right; white-space:nowrap">
              <select
                v-if="u.uid !== me?.uid"
                :value="u.role || 'user'"
                class="role-select"
                title="修改角色"
                @change="changeRole(u, $event)"
              >
                <option value="user">user</option>
                <option value="admin">admin</option>
                <option value="super_admin">super_admin</option>
              </select>
              <button
                v-if="u.uid !== me?.uid"
                class="action-btn"
                :class="u.is_active ? 'danger' : ''"
                @click="toggleStatus(u)"
              >
                {{ u.is_active ? '禁用' : '启用' }}
              </button>
              <button
                v-if="u.uid !== me?.uid"
                class="action-btn"
                title="重置该用户的密码并吊销其全部会话"
                @click="resetPwd(u)"
              >
                重置密码
              </button>
              <button
                v-if="u.uid !== me?.uid"
                class="action-btn danger"
                title="删除该用户及其全部关联数据"
                @click="deleteUser(u)"
              >
                删除
              </button>
              <span v-else class="muted" style="font-size:12.5px">当前账号</span>
            </td>
          </tr>
          <tr v-if="items.length === 0">
            <td colspan="6" style="text-align:center; padding:36px 0" class="muted">没有找到用户</td>
          </tr>
        </tbody>
      </table>

      <div v-if="error" class="error-text" style="padding:12px 18px">{{ error }}</div>

      <div class="table-footer">
        <span>第 {{ page }} / {{ totalPages }} 页</span>
        <div class="pager">
          <button class="page-btn" :disabled="page <= 1" @click="load(page - 1)">‹</button>
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <button class="page-btn" :disabled="page >= totalPages" @click="load(page + 1)">›</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../api/client'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const keyword = ref('')
const error = ref('')
const me = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('harness_user') || 'null')
  } catch {
    return null
  }
})

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function initial(name) {
  return (name || '?')[0].toUpperCase()
}

function shortUid(uid) {
  return uid ? uid.slice(0, 8) + '…' : ''
}

function roleClass(role) {
  return ['user', 'admin', 'super_admin'].includes(role) ? role : 'user'
}

function formatTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function load(p) {
  page.value = p
  error.value = ''
  try {
    const { data } = await api.get('/admin/users', {
      params: { page: p, page_size: pageSize, keyword: keyword.value || undefined },
    })
    items.value = data.items
    total.value = data.total
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  }
}

function search() {
  load(1)
}

async function toggleStatus(u) {
  try {
    const { data } = await api.patch(`/admin/users/${u.uid}/status`, { is_active: !u.is_active })
    Object.assign(u, data)
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

async function changeRole(u, e) {
  const role = e.target.value
  try {
    const { data } = await api.patch(`/admin/users/${u.uid}/role`, { role })
    Object.assign(u, data)
  } catch (err) {
    alert(err.response?.data?.detail || '修改角色失败')
  }
}

async function deleteUser(u) {
  if (!confirm(`确定删除用户「${u.username}」吗？\n\n其登录会话、AI 对话、设备、绑定等全部关联数据将被永久删除，且无法恢复！`)) return
  try {
    await api.delete(`/admin/users/${u.uid}`)
    await load(page.value)
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

async function resetPwd(u) {
  const pwd = prompt(`为 ${u.username} 设置新密码（至少 8 位，含大小写/数字/符号中 3 类）`)
  if (!pwd) return
  if (pwd.length < 8) {
    alert('密码至少 8 位')
    return
  }
  const classes = [/[a-z]/, /[A-Z]/, /\d/, /[^a-zA-Z0-9]/].filter((re) => re.test(pwd)).length
  if (classes < 3) {
    alert('密码需包含大写字母/小写字母/数字/符号中至少 3 类')
    return
  }
  if (!confirm(`确认将 ${u.username} 的密码重置为新密码？其全部会话将被吊销`)) return
  try {
    await api.post(`/admin/users/${u.uid}/reset-password`, { new_password: pwd })
    alert('密码已重置，该用户所有会话已下线')
  } catch (e) {
    alert(e.response?.data?.detail || '重置失败')
  }
}

onMounted(() => load(1))
</script>

<style scoped src="../../assets/admin.css"></style>
