<template>
  <div>
    <header class="page-head">
      <div>
        <h1>系统设置</h1>
        <p class="sub">全局配置，在线生效无需重启</p>
      </div>
    </header>

    <div v-if="error" class="panel"><p class="error-text">{{ error }}</p></div>

    <section class="panel" style="max-width:640px">
      <form @submit.prevent="save" class="form-stack">
        <label class="field">
          <span>网站名称</span>
          <input v-model.trim="form.site_name" placeholder="Harness Platform" />
        </label>
        <label class="field">
          <span>网站描述</span>
          <input v-model.trim="form.site_description" placeholder="个人智能服务平台" />
        </label>
        <label class="field">
          <span>默认 AI 模型</span>
          <input v-model.trim="form.default_ai_model" placeholder="deepseek-chat" />
        </label>
        <label class="field">
          <span>上传限制 (MB)</span>
          <input v-model.number="form.upload_limit_mb" type="number" min="1" max="100" />
        </label>

        <div class="toggle-row">
          <div>
            <b>开放注册</b>
            <p class="small muted">允许新用户注册账号</p>
          </div>
          <label class="switch">
            <input v-model="form.allow_register" type="checkbox" />
            <span class="slider"></span>
          </label>
        </div>

        <div class="toggle-row">
          <div>
            <b>维护模式</b>
            <p class="small muted">开启后仅管理员可访问</p>
          </div>
          <label class="switch">
            <input v-model="form.maintenance_mode" type="checkbox" />
            <span class="slider"></span>
          </label>
        </div>

        <p v-if="msg" :class="['msg', msgOk ? 'ok' : 'err']">{{ msg }}</p>
        <button type="submit" class="btn primary" :disabled="saving" style="width:fit-content">
          {{ saving ? '保存中…' : '保存设置' }}
        </button>
      </form>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from '../../api/client'

const form = reactive({
  site_name: '', site_description: '', default_ai_model: '',
  upload_limit_mb: 10, allow_register: true, maintenance_mode: false,
})
const error = ref('')
const msg = ref('')
const msgOk = ref(false)
const saving = ref(false)

async function load() {
  try {
    const { data } = await api.get('/admin/settings')
    Object.assign(form, data)
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  }
}

async function save() {
  saving.value = true
  msg.value = ''
  try {
    const { data } = await api.put('/admin/settings', form)
    Object.assign(form, data)
    msgOk.value = true
    msg.value = '✅ 设置已保存'
  } catch (e) {
    msgOk.value = false
    msg.value = '❌ ' + (e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.form-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field > span {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.field input {
  padding: 10px 14px;
  border-color: var(--border-color);
  border-radius: 9px;
  font-size: 13.5px;
  background: var(--bg-input);
  color: var(--text-secondary);
  font-family: inherit;
}

.field input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.field input::placeholder {
  color: #475569;
}

.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-color: var(--border-color);
}

.toggle-row b {
  font-size: 14px;
  color: var(--text-secondary);
}

.toggle-row .small {
  color: var(--text-muted);
}

.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: #334155;
  border-radius: 999px;
  transition: 0.2s;
}

.slider::before {
  content: '';
  position: absolute;
  height: 18px;
  width: 18px;
  left: 3px;
  top: 3px;
  background: var(--bg-card);
  border-radius: 50%;
  transition: 0.2s;
}

.switch input:checked + .slider {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
}

.switch input:checked + .slider::before {
  transform: translateX(20px);
}

.msg {
  font-size: 13px;
  padding: 9px 12px;
  border-radius: 8px;
}

.msg.ok { background: rgba(34, 197, 94, 0.1); color: #4ade80; }
.msg.err { background: rgba(239, 68, 68, 0.1); color: #f87171; }
</style>
