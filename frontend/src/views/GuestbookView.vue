<template>
  <div class="page">
    <SiteNav />
    <div class="page-inner">
      <header class="page-head">
        <span class="page-tag">GUESTBOOK</span>
        <h1>留言板</h1>
        <p>留下想说的话，我会看到并回复</p>
      </header>

      <div class="mode-tabs">
        <button type="button" :class="['mode-tab', tab === 'write' ? 'active' : '']" @click="tab = 'write'">留言</button>
        <button type="button" :class="['mode-tab', tab === 'query' ? 'active' : '']" @click="tab = 'query'">查询回复</button>
      </div>

      <section v-if="tab === 'write'" class="card">
        <form @submit.prevent="submit" class="form">
          <div class="field-row">
            <label class="field">
              <span>昵称（可选）</span>
              <input v-model.trim="form.nickname" maxlength="20" placeholder="你的昵称" />
            </label>
            <label class="field">
              <span>邮箱（可选，用于查询验证）</span>
              <input v-model.trim="form.email" type="email" maxlength="100" placeholder="you@example.com" />
            </label>
          </div>
          <label class="field">
            <span>留言内容（必填）</span>
            <textarea v-model.trim="form.content" rows="5" maxlength="500" required placeholder="想说的话（不超过 500 字）"></textarea>
            <small class="counter">{{ form.content.length }} / 500</small>
          </label>
          <div class="captcha-row">
            <label class="field captcha-field">
              <span>验证码（必填，4 位）</span>
              <input v-model.trim="form.captcha" maxlength="4" required placeholder="输入图片中的字符" />
            </label>
            <img :src="captchaUrl" class="captcha-img" alt="验证码" title="看不清？点击刷新" @click="refreshCaptcha" />
          </div>
          <p v-if="error" class="error">{{ error }}</p>
          <p v-if="successCode" class="success-msg">
            提交成功！您的查询码是：<b class="qcode">{{ successCode }}</b><br />
            请妥善保存，用于查看回复。
          </p>
          <button type="submit" class="btn" :disabled="submitting">{{ submitting ? '提交中…' : '提交留言' }}</button>
        </form>
      </section>

      <section v-else class="card">
        <form @submit.prevent="query" class="form">
          <label class="field">
            <span>查询码（必填）</span>
            <input v-model.trim="queryForm.code" maxlength="20" placeholder="例如 MSG-A1B2C3D4" required />
          </label>
          <label class="field">
            <span>邮箱（提交时填写过才需要）</span>
            <input v-model.trim="queryForm.email" type="email" maxlength="100" placeholder="提交留言时使用的邮箱" />
          </label>
          <p v-if="qError" class="error">{{ qError }}</p>
          <button type="submit" class="btn" :disabled="querying">{{ querying ? '查询中…' : '查询' }}</button>
        </form>

        <div v-if="result" class="result">
          <div class="result-block">
            <b class="result-label">留言内容</b>
            <p class="result-content">{{ result.content }}</p>
            <span class="muted small">{{ result.nickname ? result.nickname + ' · ' : '' }}{{ fmtTime(result.created_at) }}</span>
          </div>
          <div class="result-block" :class="{ empty: !result.reply }">
            <b class="result-label">作者回复</b>
            <p v-if="result.reply" class="result-content">{{ result.reply }}</p>
            <p v-else class="muted">暂无回复，作者看到后会尽快回复</p>
            <span v-if="result.replied_at" class="muted small">{{ fmtTime(result.replied_at) }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import SiteNav from '../components/SiteNav.vue'
import api from '../api/client'

const tab = ref('write')

// ===== 留言 =====
const form = ref({ nickname: '', email: '', content: '', captcha: '' })
const error = ref('')
const submitting = ref(false)
const successCode = ref('')
const captchaUrl = ref('')

function refreshCaptcha() {
  // 加时间戳防缓存；服务端 Set-Cookie 关联本次验证码
  captchaUrl.value = '/api/v1/captcha?t=' + Date.now()
}

function isValidEmail(v) {
  return v.indexOf('@') > 0 && v.indexOf('.') > v.indexOf('@') + 1
}

async function submit() {
  error.value = ''
  successCode.value = ''
  if (!form.value.content) {
    error.value = '请填写留言内容'
    return
  }
  if (!form.value.captcha) {
    error.value = '请填写验证码'
    return
  }
  if (form.value.email && !isValidEmail(form.value.email)) {
    error.value = '邮箱格式不正确'
    return
  }
  submitting.value = true
  try {
    const { data } = await api.post('/messages', {
      nickname: form.value.nickname || undefined,
      email: form.value.email || undefined,
      content: form.value.content,
      captcha: form.value.captcha,
    })
    successCode.value = data.query_code
    form.value = { nickname: '', email: '', content: '', captcha: '' }
    refreshCaptcha()
  } catch (e) {
    error.value = e.response?.data?.detail || '提交失败，请稍后重试'
    refreshCaptcha()
  } finally {
    submitting.value = false
  }
}

// ===== 查询 =====
const queryForm = ref({ code: '', email: '' })
const qError = ref('')
const querying = ref(false)
const result = ref(null)

async function query() {
  qError.value = ''
  result.value = null
  if (!queryForm.value.code) {
    qError.value = '请填写查询码'
    return
  }
  querying.value = true
  try {
    const { data } = await api.post('/query', {
      query_code: queryForm.value.code,
      email: queryForm.value.email || undefined,
    })
    result.value = data.data
  } catch (e) {
    qError.value = e.response?.data?.detail || '查询失败，请稍后重试'
  } finally {
    querying.value = false
  }
}

function fmtTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
}

refreshCaptcha()
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--bg-primary);
}

.page-inner {
  max-width: 640px;
  margin: 0 auto;
  padding: 64px 24px 80px;
}

.page-head {
  text-align: center;
  margin-bottom: 32px;
}

.page-tag {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: var(--success);
}

.page-head h1 {
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 12px 0 8px;
}

.page-head p {
  color: var(--text-muted);
  font-size: 14.5px;
}

.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
}

.mode-tab {
  flex: 1;
  padding: 11px 0;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.mode-tab.active {
  border-color: var(--primary-color);
  background: var(--bg-active);
  color: var(--primary-color);
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 26px;
  box-shadow: var(--shadow-sm);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field-row {
  display: flex;
  gap: 12px;
}

.field-row .field {
  flex: 1;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field > span {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
}

.field input,
.field textarea {
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  font-size: 14px;
  background: var(--bg-input);
  color: var(--text-primary);
  font-family: inherit;
  resize: vertical;
}

.field input:focus,
.field textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

.counter {
  align-self: flex-end;
  font-size: 11px;
  color: var(--text-muted);
}

.captcha-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.captcha-field {
  flex: 1;
}

.captcha-img {
  width: 130px;
  height: 44px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  cursor: pointer;
  background: #fff;
  object-fit: cover;
  flex-shrink: 0;
}

.error {
  color: var(--error);
  font-size: 13px;
}

.success-msg {
  color: var(--success);
  font-size: 13.5px;
  line-height: 1.8;
  background: color-mix(in srgb, var(--success) 8%, transparent);
  border-radius: 8px;
  padding: 10px 12px;
}

.qcode {
  font-family: var(--font-mono);
  font-size: 15px;
  letter-spacing: 0.03em;
}

.btn {
  padding: 12px 0;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
  color: #fff;
  font-size: 14.5px;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
}

.btn:disabled {
  opacity: 0.6;
}

.result {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-block {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 14px 16px;
}

.result-block.empty {
  border-style: dashed;
}

.result-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
  letter-spacing: 0.04em;
}

.result-content {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 6px;
}

.muted {
  color: var(--text-muted);
}

.small {
  font-size: 12px;
}

@media (max-width: 560px) {
  .field-row {
    flex-direction: column;
  }
}
</style>



