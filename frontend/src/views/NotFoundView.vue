<template>
  <div class="nf-page">
    <SiteNav />
    <div class="nf-inner">
      <div class="nf-code">404</div>
      <h1>页面不存在</h1>
      <p>你访问的地址不存在或已被移动。</p>
      <div class="nf-actions">
        <router-link to="/" class="btn primary">返回首页</router-link>
        <router-link to="/docs" class="btn outline">查看文档</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import SiteNav from '../components/SiteNav.vue'
</script>

<style scoped>
.nf-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.nf-inner {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 24px;
  text-align: center;
}

.nf-code {
  font-size: 96px;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
  background: var(--gradient-brand);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: nfShift 6s ease-in-out infinite alternate;
}

@keyframes nfShift {
  from { background-position: 0% 50%; }
  to { background-position: 100% 50%; }
}

.nf-inner h1 {
  font-size: 22px;
  margin: 8px 0 0;
  color: var(--text-primary);
}

.nf-inner p {
  color: var(--text-muted);
  font-size: 14px;
}

.nf-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.btn {
  padding: 10px 22px;
  border-radius: 10px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.15s;
}

.btn.primary {
  background: var(--primary-color);
  color: #fff;
}

.btn.primary:hover {
  opacity: 0.88;
}

.btn.outline {
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.btn.outline:hover {
  border-color: var(--text-primary);
}
</style>
