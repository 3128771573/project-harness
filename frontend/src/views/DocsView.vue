<template>
  <div class="page">
    <SiteNav />
    <div class="page-inner">
      <header class="page-head">
        <span class="page-tag">DEVELOPER</span>
        <h1>开发者文档</h1>
        <p>API First Architecture · 统一鉴权 · 版本化演进</p>
      </header>

      <div class="docs-grid">
        <a href="/docs" class="doc-card">
          <div class="doc-icon">🚀</div>
          <b>快速开始</b>
          <span>注册账号，获取 Token，调用第一个 API</span>
        </a>
        <a href="/docs" class="doc-card">
          <div class="doc-icon">🔐</div>
          <b>认证鉴权</b>
          <span>JWT Access/Refresh 双 Token 机制</span>
        </a>
        <a href="/docs" class="doc-card">
          <div class="doc-icon">🧩</div>
          <b>API 参考</b>
          <span>auth / user / ai / admin 模块接口</span>
        </a>
        <a href="/docs" class="doc-card">
          <div class="doc-icon">⚙️</div>
          <b>部署运维</b>
          <span>Docker Compose 一键部署 · /hdd 备份</span>
        </a>
      </div>

      <section class="api-preview">
        <h3>快速示例</h3>
        <div class="code-block">
          <div class="code-line"><span class="c-c"># 登录获取 Token</span></div>
          <div class="code-line"><span class="c-k">POST</span> <span class="c-u">/api/v1/auth/login</span></div>
          <div class="code-line br"></div>
          <div class="code-line"><span class="c-p">{</span> <span class="c-k">"email"</span>: <span class="c-v">"user@example.com"</span>, <span class="c-k">"password"</span>: <span class="c-v">"***"</span> <span class="c-p">}</span></div>
          <div class="code-line br"></div>
          <div class="code-line"><span class="c-c"># 调用 AI 对话</span></div>
          <div class="code-line"><span class="c-k">POST</span> <span class="c-u">/api/v1/ai/chat</span></div>
          <div class="code-line"><span class="c-k">Authorization:</span> <span class="c-v">Bearer</span> &lt;access_token&gt;</div>
        </div>
        <p class="doc-hint">完整文档见仓库 <code>docs/</code> 目录 · <a href="https://github.com/3128771573/project-harness" target="_blank" rel="noopener">GitHub ↗</a></p>
      </section>
    </div>
  </div>
</template>

<script setup>
import SiteNav from '../components/SiteNav.vue'
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--bg-card);
}

.page-inner {
  max-width: 860px;
  margin: 0 auto;
  padding: 72px 28px;
}

.page-head {
  text-align: center;
  margin-bottom: 48px;
}

.page-tag {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: #2b6de9;
}

.page-head h1 {
  font-size: 38px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 12px 0 10px;
}

.page-head p {
  color: var(--text-muted);
  font-size: 15px;
}

.docs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 48px;
}

.doc-card {
  border-color: var(--border-light);
  border-radius: 16px;
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.2s, transform 0.2s;
}

.doc-card:hover {
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  transform: translateY(-3px);
}

.doc-icon {
  font-size: 26px;
  margin-bottom: 6px;
}

.doc-card b {
  font-size: 15px;
}

.doc-card span {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.6;
}

.api-preview h3 {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
}

.code-block {
  background: var(--brand-block);
  border-radius: 16px;
  padding: 24px;
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 13px;
  line-height: 2;
  overflow-x: auto;
}

.code-line .c-k { color: #7aa5f0; }
.code-line .c-u { color: #93c5fd; }
.code-line .c-v { color: #6ee7b7; }
.code-line .c-p { color: #f0abfc; }
.code-line .c-c { color: var(--text-muted); }
.code-line.br { height: 4px; }

.doc-hint {
  margin-top: 16px;
  font-size: 13px;
  color: var(--text-muted);
}

.doc-hint code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 5px;
  font-size: 12px;
}

.doc-hint a {
  color: #2b6de9;
  text-decoration: none;
}
</style>
