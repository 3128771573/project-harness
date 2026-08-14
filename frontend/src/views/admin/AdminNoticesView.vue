<template>
  <div>
    <header class="page-head">
      <div>
        <h1>公告管理</h1>
        <p class="sub">站内公告会展示在首页横幅与登录用户铃铛中</p>
      </div>
    </header>

    <div v-if="error" class="error-text" style="padding:12px 18px">{{ error }}</div>

    <section class="panel" style="max-width: 640px">
      <div class="panel-title">{{ editingId ? '编辑公告' : '新建公告' }}</div>
      <form @submit.prevent="save" class="form-stack">
        <label class="field">
          <span>标题</span>
          <input v-model.trim="form.title" maxlength="120" required placeholder="公告标题" />
        </label>
        <label class="field">
          <span>内容</span>
          <textarea v-model.trim="form.content" rows="5" required placeholder="公告内容（支持换行）"></textarea>
        </label>
        <label class="checkbox-row">
          <input v-model="form.is_published" type="checkbox" />
          <span>立即发布</span>
        </label>
        <div class="actions" style="margin-top:4px">
          <button type="submit" class="btn primary" :disabled="saving">{{ saving ? '保存中…' : '保存' }}</button>
          <button v-if="editingId" type="button" class="btn" @click="resetForm">取消编辑</button>
        </div>
      </form>
    </section>

    <section class="panel">
      <div class="panel-title">公告列表</div>
      <div v-if="items.length === 0" class="muted" style="padding:8px 0">暂无公告</div>
      <div v-for="n in items" :key="n.id" class="notice-row">
        <div class="notice-info">
          <b>{{ n.title }}</b>
          <span class="notice-meta">
            <span :class="['status-badge', n.is_published ? 'active' : 'disabled']">
              {{ n.is_published ? '已发布' : '草稿' }}
            </span>
            <span class="muted">{{ formatTime(n.created_time) }}</span>
          </span>
        </div>
        <div class="notice-actions">
          <button class="action-btn" @click="editNotice(n)">编辑</button>
          <button class="action-btn" @click="togglePublish(n)">{{ n.is_published ? '下线' : '发布' }}</button>
          <button class="action-btn danger" @click="removeNotice(n)">删除</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from '../../api/client'

const items = ref([])
const error = ref('')
const saving = ref(false)
const editingId = ref(null)
const form = reactive({ title: '', content: '', is_published: false })

async function load() {
  error.value = ''
  try {
    const { data } = await api.get('/admin/notices')
    items.value = data.items
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  }
}

function resetForm() {
  editingId.value = null
  form.title = ''
  form.content = ''
  form.is_published = false
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const payload = { title: form.title, content: form.content, is_published: form.is_published }
    if (editingId.value) {
      await api.put(`/admin/notices/${editingId.value}`, payload)
    } else {
      await api.post('/admin/notices', payload)
    }
    resetForm()
    await load()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

function editNotice(n) {
  editingId.value = n.id
  form.title = n.title
  form.content = n.content
  form.is_published = n.is_published
}

async function togglePublish(n) {
  try {
    await api.put(`/admin/notices/${n.id}`, { is_published: !n.is_published })
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '操作失败')
  }
}

async function removeNotice(n) {
  if (!confirm(`删除公告「${n.title}」？`)) return
  try {
    await api.delete(`/admin/notices/${n.id}`)
    if (editingId.value === n.id) resetForm()
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || '删除失败')
  }
}

function formatTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (x) => String(x).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(load)
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.form-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field > span {
  font-size: 13px;
  font-weight: 600;
  color: var(--admin-text-muted);
}

.field input,
.field textarea {
  padding: 10px 14px;
  border: 1px solid var(--admin-border);
  border-radius: 9px;
  font-size: 13.5px;
  background: var(--admin-card);
  color: var(--admin-text);
  font-family: inherit;
  resize: vertical;
}

.field input:focus,
.field textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--admin-text);
  cursor: pointer;
}

.actions {
  display: flex;
  gap: 10px;
}

.notice-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--admin-border);
}

.notice-row:last-child {
  border-bottom: none;
}

.notice-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.notice-info b {
  font-size: 14px;
  color: var(--admin-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}

.notice-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
</style>
