<template>
  <div>
    <header class="topbar">
      <h1>用户管理</h1>
      <div class="search-row">
        <input v-model.trim="keyword" placeholder="搜索用户名 / 邮箱" @keyup.enter="load(1)" />
        <button class="btn small" @click="load(1)">搜索</button>
      </div>
    </header>

    <section class="panel table-panel">
      <table class="table">
        <thead>
          <tr>
            <th>UID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>角色</th>
            <th>注册时间</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in items" :key="u.uid">
            <td class="mono uid-cell" :title="u.uid">{{ shortUid(u.uid) }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.email }}</td>
            <td>
              <select :value="u.role || 'user'" class="role-select" @change="changeRole(u, $event)">
                <option value="user">user</option>
                <option value="admin">admin</option>
                <option value="super_admin">super_admin</option>
              </select>
            </td>
            <td>{{ formatTime(u.created_time) }}</td>
            <td>
              <span :class="['badge', u.is_active ? 'ok' : 'disabled']">
                {{ u.is_active ? '正常' : '已禁用' }}
              </span>
            </td>
            <td>
              <button
                v-if="u.uid !== me?.uid"
                class="btn tiny"
                :class="u.is_active ? 'danger' : 'primary'"
                @click="toggleStatus(u)"
              >
                {{ u.is_active ? '禁用' : '启用' }}
              </button>
              <span v-else class="muted">自己</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="error" class="error-text">{{ error }}</div>

      <div class="pager">
        <button class="btn tiny" :disabled="page <= 1" @click="load(page - 1)">上一页</button>
        <span>第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 人</span>
        <button class="btn tiny" :disabled="page >= totalPages" @click="load(page + 1)">下一页</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../../api/client'

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
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

function shortUid(uid) {
  return uid ? uid.slice(0, 8) + '…' : ''
}

function formatTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
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
    // 回滚选择
    u.role = u.role || 'user'
  }
}

onMounted(() => load(1))
</script>

<style scoped src="../../assets/admin.css"></style>
