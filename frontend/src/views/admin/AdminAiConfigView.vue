<template>
  <div>
    <header class="page-head">
      <div>
        <h1>AI 配置</h1>
        <p class="sub">在线配置 AI 服务，无需修改 .env 或重启</p>
      </div>
    </header>

    <div v-if="error" class="panel"><p class="error-text">{{ error }}</p></div>

    <section class="panel" style="max-width:640px">
      <div class="panel-title">服务配置</div>
      <p class="panel-sub">
        当前状态：
        <span v-if="cfg?.api_key_set" class="status-badge active">已配置 API Key</span>
        <span v-else class="status-badge disabled">未配置（Mock 模式）</span>
      </p>

      <form @submit.prevent="save" class="ai-form">
        <label class="field">
          <span>API Key</span>
          <div class="key-row">
            <input
              v-model="form.api_key"
              type="password"
              placeholder="sk-...（留空表示不修改）"
              autocomplete="off"
            />
          </div>
          <small class="field-hint">留空并勾选"清除"可回到 Mock 模式；明文不会回显</small>
        </label>

        <label class="field">
          <span>Base URL</span>
          <input v-model.trim="form.base_url" placeholder="https://api.deepseek.com/v1" />
        </label>

        <label class="field">
          <span>模型</span>
          <input v-model.trim="form.model" placeholder="deepseek-chat" />
        </label>

        <label class="checkbox-row">
          <input v-model="form.clear_api_key" type="checkbox" />
          <span>清除当前 API Key（回退 Mock 模式）</span>
        </label>

        <div class="actions" style="margin-top:8px">
          <button type="submit" class="btn primary" :disabled="saving">
            {{ saving ? '保存中…' : '保存配置' }}
          </button>
          <button type="button" class="btn" :disabled="testing" @click="testConn">
            {{ testing ? '测试中…' : '测试连接' }}
          </button>
        </div>

        <p v-if="msg" :class="['test-msg', msgOk ? 'ok' : 'err']">{{ msg }}</p>
      </form>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from '../../api/client'

const cfg = ref(null)
const error = ref('')
const saving = ref(false)
const testing = ref(false)
const msg = ref('')
const msgOk = ref(true)

const form = reactive({ api_key: '', base_url: '', model: '', clear_api_key: false })

async function load() {
  try {
    const { data } = await api.get('/admin/settings/ai')
    cfg.value = data
    form.base_url = data.base_url
    form.model = data.model
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  }
}

async function save() {
  saving.value = true
  msg.value = ''
  try {
    const payload = {
      base_url: form.base_url || undefined,
      model: form.model || undefined,
      clear_api_key: form.clear_api_key,
    }
    if (form.api_key) payload.api_key = form.api_key
    const { data } = await api.put('/admin/settings/ai', payload)
    cfg.value = data
    form.api_key = ''
    form.clear_api_key = false
    msgOk.value = true
    msg.value = '✅ 配置已保存'
  } catch (e) {
    msgOk.value = false
    msg.value = '❌ ' + (e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function testConn() {
  testing.value = true
  msg.value = ''
  try {
    const { data } = await api.post('/admin/settings/ai/test')
    msgOk.value = data.ok
    msg.value = (data.ok ? '✅ ' : '❌ ') + data.message
  } catch (e) {
    msgOk.value = false
    msg.value = '❌ 测试请求失败'
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>

<style scoped src="../../assets/admin.css"></style>
<style scoped>
.ai-form {
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
  color: #cbd5e1;
}

.field input {
  padding: 10px 14px;
  border: 1px solid #1e293b;
  border-radius: 9px;
  font-size: 13.5px;
  background: #0f172a;
  color: #e2e8f0;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.field input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.field input::placeholder {
  color: #475569;
}

.field-hint {
  font-size: 12px;
  color: #64748b;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #cbd5e1;
  cursor: pointer;
}

.test-msg {
  font-size: 13px;
  padding: 10px 14px;
  border-radius: 9px;
}

.test-msg.ok {
  background: rgba(34, 197, 94, 0.1);
  color: #4ade80;
}

.test-msg.err {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
}
</style>
