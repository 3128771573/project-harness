<template>
  <div>
    <header class="page-head">
      <div>
        <h1>权限管理</h1>
        <p class="sub">RBAC 角色体系</p>
      </div>
    </header>

    <div class="stat-grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))">
      <div class="stat-card" v-for="r in roles" :key="r.id">
        <div class="stat-info">
          <div class="stat-label">{{ roleDesc(r.name) }}</div>
          <div class="stat-value" style="font-size:18px">
            <span :class="['role-badge', r.name]">{{ r.name }}</span>
          </div>
        </div>
        <div class="stat-icon" :class="roleIcon(r.name)">
          <svg viewBox="0 0 24 24" style="width:19px;height:19px;fill:#fff"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>
        </div>
      </div>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr><th>角色</th><th>描述</th><th>创建时间</th><th>权限范围</th></tr>
        </thead>
        <tbody>
          <tr v-for="r in roles" :key="r.id">
            <td><span :class="['role-badge', r.name]">{{ r.name }}</span></td>
            <td class="muted">{{ roleDesc(r.name) }}</td>
            <td class="muted">{{ fmtTime(r.created_time) }}</td>
            <td class="muted">{{ scope(r.name) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../../api/client'

const roles = ref([])

function roleDesc(name) {
  return { user: '普通用户', admin: '管理员', super_admin: '超级管理员' }[name] || name
}

function roleIcon(name) {
  return name === 'user' ? 'blue' : name === 'admin' ? 'violet' : 'amber'
}

function scope(name) {
  if (name === 'super_admin') return '全部权限 + 管理管理员'
  if (name === 'admin') return '用户管理 / AI 配置 / 监控 / 日志'
  return '本人资料 / AI 对话'
}

function fmtTime(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

onMounted(async () => {
  try {
    const { data } = await api.get('/admin/roles')
    roles.value = data
  } catch { /* ignore */ }
})
</script>

<style scoped src="../../assets/admin.css"></style>
