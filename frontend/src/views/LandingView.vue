<template>
  <div class="landing">
    <!-- 导航 -->
    <header class="nav">
      <div class="nav-inner">
        <div class="brand">
          <div class="brand-logo">H</div>
          <span class="brand-name">Harness</span>
        </div>
        <nav class="nav-links">
          <a href="#features">功能</a>
          <a href="#modules">模块</a>
          <a href="#roadmap">路线</a>
        </nav>
        <div class="nav-actions">
          <router-link to="/login" class="btn ghost">登录</router-link>
          <router-link to="/register" class="btn primary">免费注册</router-link>
        </div>
      </div>
    </header>

    <!-- Hero -->
    <section class="hero">
      <div class="hero-badge">🚀 个人智能服务平台</div>
      <h1>一个平台，承载你的<br /><span class="grad">AI 能力与创意 Demo</span></h1>
      <p class="hero-sub">
        从用户系统到 AI 服务，从 IoT 实验到商业化的完整链路。
        基于 Vue 3 + FastAPI + PostgreSQL，全容器化部署。
      </p>
      <div class="hero-actions">
        <router-link to="/register" class="btn primary lg">立即开始 →</router-link>
        <router-link to="/login" class="btn ghost lg">已有账号登录</router-link>
      </div>
      <div class="hero-stats">
        <div class="stat"><b>3</b><span>服务模块</span></div>
        <div class="stat"><b>7</b><span>API 模块</span></div>
        <div class="stat"><b>0.9</b><span>当前版本</span></div>
      </div>
    </section>

    <!-- 功能特性 -->
    <section id="features" class="section">
      <h2 class="section-title">核心能力</h2>
      <div class="feature-grid">
        <div class="feature-card">
          <div class="f-icon blue">🔐</div>
          <h3>完整用户体系</h3>
          <p>注册登录、JWT 双 Token、RBAC 权限、密码安全、登录日志，企业级账号系统。</p>
        </div>
        <div class="feature-card">
          <div class="f-icon violet">🤖</div>
          <h3>AI 服务</h3>
          <p>对话聊天、历史记录、模型切换、用量统计，兼容主流大模型 API。</p>
        </div>
        <div class="feature-card">
          <div class="f-icon green">📊</div>
          <h3>运营控制中心</h3>
          <p>用户管理、AI 配置、系统监控、日志审计、安全中心，一站式运维。</p>
        </div>
        <div class="feature-card">
          <div class="f-icon amber">📡</div>
          <h3>IoT 扩展</h3>
          <p>设备接入、实时数据、仪表盘展示，为智能测控专业量身设计。</p>
        </div>
      </div>
    </section>

    <!-- 技术栈 -->
    <section id="modules" class="section alt">
      <h2 class="section-title">技术架构</h2>
      <div class="stack-row">
        <div class="stack-chip" v-for="s in stack" :key="s">{{ s }}</div>
      </div>
      <div class="arch-diagram">
        <div class="arch-box">Client<br /><small>Web / App</small></div>
        <div class="arch-arrow">↓</div>
        <div class="arch-box">Nginx<br /><small>前端 + 反代</small></div>
        <div class="arch-arrow">↓</div>
        <div class="arch-box">FastAPI<br /><small>鉴权 · RBAC</small></div>
        <div class="arch-arrow">↓</div>
        <div class="arch-box">PostgreSQL<br /><small>数据持久化</small></div>
      </div>
    </section>

    <!-- 路线图 -->
    <section id="roadmap" class="section">
      <h2 class="section-title">发展路线</h2>
      <div class="roadmap">
        <div class="rm-item done"><span class="rm-dot">✅</span><b>v0.1-0.6</b> 基础平台 · 用户中心 · AI 模块</div>
        <div class="rm-item done"><span class="rm-dot">✅</span><b>v0.7-0.8</b> Admin 后台 · 运维增强 · /hdd 备份</div>
        <div class="rm-item current"><span class="rm-dot">🔨</span><b>v0.9</b> 整体优化 · 用户安全体系</div>
        <div class="rm-item"><span class="rm-dot">⬜</span><b>v1.0</b> IoT Demo · 云部署 · HTTPS</div>
        <div class="rm-item"><span class="rm-dot">⬜</span><b>v2.0</b> 多端 App · 商业化</div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta">
      <h2>准备好开始了吗？</h2>
      <p>注册账号，体验完整平台能力</p>
      <router-link to="/register" class="btn primary lg">创建账号</router-link>
    </section>

    <footer class="footer">
      <span>Project Harness · 个人智能服务平台</span>
    </footer>
  </div>
</template>

<script setup>
const stack = ['Vue 3', 'Vite', 'FastAPI', 'SQLAlchemy', 'PostgreSQL 16', 'Docker', 'Nginx', 'JWT', 'bcrypt', 'GitHub Actions']
</script>

<style scoped>
.landing {
  min-height: 100vh;
  background: #fff;
  color: #111827;
}

/* 导航 */
.nav {
  position: sticky;
  top: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #f0f1f5;
  z-index: 10;
}

.nav-inner {
  max-width: 1080px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-logo {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, #4f7cf7, #7aa5f0);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 17px;
}

.brand-name {
  font-size: 17px;
  font-weight: 700;
}

.nav-links {
  display: flex;
  gap: 28px;
}

.nav-links a {
  color: #6b7280;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}

.nav-links a:hover {
  color: #111827;
}

.nav-actions {
  display: flex;
  gap: 10px;
}

/* 按钮 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 9px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.15s;
  cursor: pointer;
  border: 1px solid transparent;
}

.btn.primary {
  background: #2b6de9;
  color: #fff;
}

.btn.primary:hover {
  background: #1f5ad0;
}

.btn.ghost {
  background: transparent;
  color: #374151;
  border-color: #e5e7eb;
}

.btn.ghost:hover {
  background: #f8f9fc;
}

.btn.lg {
  padding: 12px 26px;
  font-size: 15px;
  border-radius: 12px;
}

/* Hero */
.hero {
  max-width: 860px;
  margin: 0 auto;
  padding: 88px 24px 60px;
  text-align: center;
}

.hero-badge {
  display: inline-block;
  background: #eef2ff;
  color: #4338ca;
  font-size: 13px;
  font-weight: 600;
  padding: 6px 16px;
  border-radius: 999px;
  margin-bottom: 24px;
}

.hero h1 {
  font-size: 44px;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.2;
  margin-bottom: 20px;
}

.grad {
  background: linear-gradient(135deg, #2b6de9, #8b5cf6);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero-sub {
  font-size: 17px;
  color: #6b7280;
  line-height: 1.7;
  max-width: 560px;
  margin: 0 auto 32px;
}

.hero-actions {
  display: flex;
  gap: 14px;
  justify-content: center;
  margin-bottom: 48px;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 48px;
}

.hero-stats .stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-stats b {
  font-size: 28px;
  font-weight: 800;
  color: #111827;
}

.hero-stats span {
  font-size: 13px;
  color: #9ca3af;
  margin-top: 2px;
}

/* 区块 */
.section {
  max-width: 1080px;
  margin: 0 auto;
  padding: 64px 24px;
}

.section.alt {
  background: #f8f9fc;
  border-radius: 24px;
  max-width: 960px;
}

.section-title {
  font-size: 28px;
  font-weight: 800;
  text-align: center;
  margin-bottom: 40px;
  letter-spacing: -0.01em;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 18px;
}

.feature-card {
  border: 1px solid #f0f1f5;
  border-radius: 16px;
  padding: 26px 22px;
  transition: box-shadow 0.2s, transform 0.2s;
}

.feature-card:hover {
  box-shadow: 0 8px 28px rgba(15, 23, 42, 0.08);
  transform: translateY(-3px);
}

.f-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  margin-bottom: 16px;
}

.f-icon.blue { background: #eef2ff; }
.f-icon.violet { background: #f5f3ff; }
.f-icon.green { background: #ecfdf5; }
.f-icon.amber { background: #fffbeb; }

.feature-card h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 8px;
}

.feature-card p {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.7;
}

/* 技术栈 */
.stack-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-bottom: 36px;
}

.stack-chip {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 7px 16px;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.arch-diagram {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.arch-box {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px 20px;
  text-align: center;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}

.arch-box small {
  font-weight: 400;
  color: #9ca3af;
  font-size: 12px;
}

.arch-arrow {
  font-size: 20px;
  color: #9ca3af;
}

/* 路线 */
.roadmap {
  max-width: 520px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.rm-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border: 1px solid #f0f1f5;
  border-radius: 12px;
  font-size: 14px;
}

.rm-item.done { background: #f8faf8; }
.rm-item.current { border-color: #bfdbfe; background: #eff6ff; }

.rm-item b {
  margin-right: 8px;
}

.rm-dot {
  font-size: 16px;
}

/* CTA */
.cta {
  text-align: center;
  padding: 72px 24px;
  background: linear-gradient(135deg, #1e3a8a, #4f46e5);
  color: #fff;
}

.cta h2 {
  font-size: 30px;
  font-weight: 800;
  margin-bottom: 10px;
}

.cta p {
  opacity: 0.8;
  margin-bottom: 26px;
}

.cta .btn.primary {
  background: #fff;
  color: #1e3a8a;
}

.cta .btn.primary:hover {
  background: #f0f4ff;
}

.footer {
  text-align: center;
  padding: 24px;
  color: #9ca3af;
  font-size: 13px;
}

@media (max-width: 640px) {
  .nav-links { display: none; }
  .hero h1 { font-size: 32px; }
  .hero-stats { gap: 24px; }
}
</style>
