<template>
  <div class="landing">
    <SiteNav />

    <!-- ===== 已登录：个人控制中心 ===== -->
    <div v-if="user" class="home-shell">
      <section class="welcome">
        <h1>欢迎回来，{{ user.nickname || user.username }}</h1>
        <p class="welcome-sub">继续你的智能体验</p>
      </section>

      <div class="quick-grid">
        <router-link to="/ai" class="quick-card ai">
          <div class="q-icon">✦</div>
          <div>
            <b>AI 助手</b>
            <span>继续对话</span>
          </div>
          <span class="q-arrow">→</span>
        </router-link>
        <router-link to="/demo" class="quick-card demo">
          <div class="q-icon">◫</div>
          <div>
            <b>Demo 实验室</b>
            <span>探索实验</span>
          </div>
          <span class="q-arrow">→</span>
        </router-link>
        <router-link to="/iot" class="quick-card iot">
          <div class="q-icon">◎</div>
          <div>
            <b>IoT 平台</b>
            <span>设备接入</span>
          </div>
          <span class="q-arrow">→</span>
        </router-link>
        <router-link to="/settings" class="quick-card settings">
          <div class="q-icon">⚙</div>
          <div>
            <b>安全设置</b>
            <span>账号管理</span>
          </div>
          <span class="q-arrow">→</span>
        </router-link>
      </div>

      <section class="panel-row">
        <div class="panel-card">
          <h3>我的 AI</h3>
          <p class="panel-num">—</p>
          <p class="panel-sub">对话统计接入中</p>
        </div>
        <div class="panel-card">
          <h3>我的设备</h3>
          <p class="panel-num">0</p>
          <p class="panel-sub">IoT 设备管理</p>
        </div>
        <div class="panel-card">
          <h3>平台状态</h3>
          <p class="panel-num"><span class="live-dot"></span></p>
          <p class="panel-sub">服务运行正常</p>
        </div>
      </section>
    </div>

    <!-- ===== 未登录：营销首页 ===== -->
    <template v-else>
      <!-- Hero -->
      <section class="hero">
        <div class="hero-bg" aria-hidden="true">
          <div class="grid-layer"></div>
          <div class="glow glow-1"></div>
          <div class="glow glow-2"></div>
        </div>
        <div class="hero-content">
          <div class="hero-badge">
            <span class="badge-dot"></span>
            持续进化的智能服务平台
          </div>
          <h1 class="hero-title">
            Harness
            <span class="hero-sub-title">连接 AI · IoT · 数字服务</span>
          </h1>
          <p class="hero-desc">
            Connect AI, Devices and Digital Experiences.
            <br />
            一个平台，承载你的智能能力与创意实验。
          </p>
          <div class="hero-actions">
            <router-link to="/register" class="btn dark lg">开始体验 →</router-link>
            <router-link to="/demo" class="btn outline lg">进入 Demo 实验室</router-link>
          </div>
          <div class="hero-flow">
            <span class="flow-node ai">AI</span>
            <span class="flow-line"></span>
            <span class="flow-node api">API</span>
            <span class="flow-line"></span>
            <span class="flow-node data">DATA</span>
            <span class="flow-line"></span>
            <span class="flow-node dev">DEVICE</span>
          </div>
        </div>
      </section>

      <!-- 快速入口 -->
      <section class="section quick">
        <div class="quick-grid">
          <router-link to="/ai" class="quick-card ai">
            <div class="q-icon">✦</div>
            <div><b>AI</b><span>智能助手 · 多模型对话</span></div>
            <span class="q-arrow">→</span>
          </router-link>
          <router-link to="/iot" class="quick-card iot">
            <div class="q-icon">◎</div>
            <div><b>IoT</b><span>设备接入 · 实时数据</span></div>
            <span class="q-arrow">→</span>
          </router-link>
          <router-link to="/demo" class="quick-card demo">
            <div class="q-icon">◫</div>
            <div><b>Demo</b><span>实验展示 · 技术试验场</span></div>
            <span class="q-arrow">→</span>
          </router-link>
        </div>
      </section>

      <!-- AI 模块 -->
      <section class="module">
        <div class="module-text">
          <span class="module-tag">AI ASSISTANT</span>
          <h2>让信息处理更简单</h2>
          <p class="module-desc">接入主流大模型，支持对话历史与多模型切换。为你的每个问题，找到答案。</p>
          <ul class="module-feats">
            <li>✓ 多模型支持</li>
            <li>✓ 对话历史</li>
            <li>✓ 个性化助手</li>
          </ul>
          <router-link to="/ai" class="btn dark">进入 AI →</router-link>
        </div>
        <div class="module-visual">
          <div class="chat-demo">
            <div class="chat-line user">如何监控设备温度？</div>
            <div class="chat-line ai">可通过 MQTT 接入传感器，实时上报数据到平台，即可在 Dashboard 查看温度曲线与告警。</div>
            <div class="chat-line user">明白了，谢谢！</div>
          </div>
        </div>
      </section>

      <!-- IoT 模块 -->
      <section class="module reverse">
        <div class="module-text">
          <span class="module-tag">IOT PLATFORM</span>
          <h2>连接现实世界</h2>
          <p class="module-desc">通过传感器、设备与数据，构建智能应用。专为智能测控与工业互联网场景设计。</p>
          <ul class="module-feats">
            <li>✓ 设备接入管理</li>
            <li>✓ 实时数据采集</li>
            <li>✓ 可视化仪表盘</li>
          </ul>
          <router-link to="/iot" class="btn dark">进入 IoT →</router-link>
        </div>
        <div class="module-visual">
          <div class="device-demo">
            <div class="dev-head"><span class="live-dot"></span> 设备状态</div>
            <div class="dev-grid">
              <div class="dev-metric"><span>温度</span><b>26.5<small>℃</small></b></div>
              <div class="dev-metric"><span>湿度</span><b>60<small>%</small></b></div>
              <div class="dev-metric"><span>在线</span><b class="ok">🟢</b></div>
            </div>
          </div>
        </div>
      </section>

      <!-- Demo 实验室 -->
      <section class="section lab">
        <div class="lab-head">
          <span class="module-tag">DEMO LABORATORY</span>
          <h2>实验展示 · 技术试验场</h2>
        </div>
        <div class="lab-grid">
          <component
            :is="d.link ? 'router-link' : 'div'"
            v-for="d in demos"
            :key="d.name"
            :to="d.link || undefined"
            class="lab-card"
            :class="d.state"
          >
            <div class="lab-icon">{{ d.icon }}</div>
            <b>{{ d.name }}</b>
            <span>{{ d.desc }}</span>
            <span class="lab-state">{{ d.state === 'active' ? '已上线 →' : '规划中' }}</span>
          </component>
        </div>
        <div class="lab-cta">
          <router-link to="/demo" class="btn outline">进入实验室 →</router-link>
        </div>
      </section>

      <!-- 开发者区域 -->
      <section class="module reverse">
        <div class="module-text">
          <span class="module-tag">DEVELOPER</span>
          <h2>API First Architecture</h2>
          <p class="module-desc">RESTful API 设计，统一鉴权与版本管理。开放、可扩展，为未来的开放平台与 SDK 做好准备。</p>
          <ul class="module-feats">
            <li>✓ REST API /api/v1</li>
            <li>✓ JWT + RBAC</li>
            <li>✓ 版本化演进</li>
          </ul>
          <router-link to="/docs" class="btn dark">查看文档 →</router-link>
        </div>
        <div class="module-visual">
          <div class="code-demo">
            <div class="code-line"><span class="c-k">POST</span> <span class="c-u">/api/v1/ai/chat</span></div>
            <div class="code-line"><span class="c-k">Authorization:</span> <span class="c-v">Bearer</span> eyJ...</div>
            <div class="code-line br"></div>
            <div class="code-line"><span class="c-p">{</span></div>
            <div class="code-line">&nbsp;&nbsp;<span class="c-k">"question"</span>: <span class="c-v">"你好"</span>,</div>
            <div class="code-line">&nbsp;&nbsp;<span class="c-k">"model"</span>: <span class="c-v">"deepseek-chat"</span></div>
            <div class="code-line"><span class="c-p">}</span></div>
          </div>
        </div>
      </section>

      <!-- 技术栈 -->
      <section class="section trust">
        <p class="trust-label">POWERED BY</p>
        <div class="trust-row">
          <span v-for="t in stack" :key="t" class="trust-chip">{{ t }}</span>
        </div>
      </section>
    </template>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <b>Harness Platform</b>
          <span>AI · IoT · Digital Services</span>
        </div>
        <div class="footer-cols">
          <div class="footer-col">
            <b>产品</b>
            <router-link to="/ai">AI</router-link>
            <router-link to="/demo">Demo</router-link>
            <router-link to="/iot">IoT</router-link>
          </div>
          <div class="footer-col">
            <b>开发者</b>
            <router-link to="/docs">API 文档</router-link>
            <a href="https://github.com/3128771573/project-harness" target="_blank" rel="noopener">GitHub</a>
          </div>
          <div class="footer-col">
            <b>账号</b>
            <router-link to="/login">登录</router-link>
            <router-link to="/register">注册</router-link>
          </div>
        </div>
      </div>
      <div class="footer-bottom">© 2026 Harness Platform · 个人智能服务平台</div>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SiteNav from '../components/SiteNav.vue'

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('harness_user') || 'null')
  } catch {
    return null
  }
})

const stack = ['Vue 3', 'FastAPI', 'PostgreSQL', 'Docker', 'Nginx', 'Linux']

const demos = [
  { icon: '🦓', name: '图灵斑图', desc: '反应扩散实时模拟 · GPU 加速', link: '/demo/turing', state: 'active' },
  { icon: '💳', name: '支付 Demo', desc: '订单 · 支付流程模拟' },
  { icon: '🎬', name: '视频播放器', desc: '媒体播放组件' },
  { icon: '🎵', name: '音乐播放器', desc: '在线音频体验' },
  { icon: '🧠', name: 'AI 组件', desc: '对话式交互组件' },
  { icon: '🧩', name: '交互组件', desc: 'UI 实验集合' },
  { icon: '📈', name: '数据可视化', desc: '图表与曲线' },
]
</script>

<style scoped>
.landing {
  min-height: 100vh;
  background: #fff;
  color: #111827;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ===== 已登录控制中心 ===== */
.home-shell {
  max-width: 1120px;
  margin: 0 auto;
  padding: 64px 28px;
}

.welcome h1 {
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.welcome-sub {
  color: #6b7280;
  margin-top: 8px;
  font-size: 15px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin: 32px 0;
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px;
  border: 1px solid #eef0f5;
  border-radius: 16px;
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
}

.quick-card:hover {
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  transform: translateY(-2px);
  border-color: #e2e8f0;
}

.q-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.quick-card.ai .q-icon { background: #eef2ff; color: #4338ca; }
.quick-card.iot .q-icon { background: #ecfdf5; color: #059669; }
.quick-card.demo .q-icon { background: #f5f3ff; color: #7c3aed; }
.quick-card.settings .q-icon { background: #fffbeb; color: #b45309; }

.quick-card b {
  font-size: 15px;
  font-weight: 700;
  display: block;
}

.quick-card span {
  font-size: 12.5px;
  color: #6b7280;
}

.q-arrow {
  margin-left: auto;
  color: #9ca3af;
  font-size: 16px;
}

.panel-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.panel-card {
  border: 1px solid #eef0f5;
  border-radius: 16px;
  padding: 22px;
}

.panel-card h3 {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
}

.panel-num {
  font-size: 28px;
  font-weight: 800;
  margin: 10px 0 4px;
}

.panel-sub {
  font-size: 12.5px;
  color: #9ca3af;
}

.live-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.2);
}

/* ===== Hero ===== */
.hero {
  position: relative;
  overflow: hidden;
  background: #fafbfd;
  min-height: 620px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.hero-bg {
  position: absolute;
  inset: 0;
}

.grid-layer {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(15, 23, 42, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(15, 23, 42, 0.035) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, #000 30%, transparent 75%);
  -webkit-mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, #000 30%, transparent 75%);
}

.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.35;
}

.glow-1 {
  width: 480px;
  height: 480px;
  background: #2b6de9;
  top: -160px;
  left: -120px;
}

.glow-2 {
  width: 420px;
  height: 420px;
  background: #8b5cf6;
  bottom: -180px;
  right: -100px;
}

.hero-content {
  position: relative;
  z-index: 2;
  padding: 80px 28px;
  max-width: 780px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #4b5563;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 7px 16px;
  margin-bottom: 28px;
}

.badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #22c55e;
}

.hero-title {
  font-size: 64px;
  font-weight: 800;
  letter-spacing: -0.035em;
  line-height: 1.05;
  margin-bottom: 18px;
}

.hero-sub-title {
  display: block;
  font-size: 30px;
  font-weight: 600;
  background: linear-gradient(135deg, #2b6de9, #8b5cf6);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-top: 10px;
  letter-spacing: -0.02em;
}

.hero-desc {
  font-size: 17px;
  color: #6b7280;
  line-height: 1.75;
  margin-bottom: 34px;
}

.hero-actions {
  display: flex;
  gap: 14px;
  justify-content: center;
  margin-bottom: 48px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.btn.lg {
  padding: 14px 30px;
  font-size: 15px;
}

.btn.dark {
  background: #111827;
  color: #fff;
}

.btn.dark:hover {
  background: #1f2937;
  transform: translateY(-1px);
}

.btn.outline {
  background: transparent;
  color: #111827;
  border-color: #d1d5db;
}

.btn.outline:hover {
  border-color: #111827;
}

.hero-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}

.flow-node {
  font-size: 12.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: rgba(255, 255, 255, 0.7);
}

.flow-node.ai { color: #4338ca; }
.flow-node.api { color: #059669; }
.flow-node.data { color: #b45309; }
.flow-node.dev { color: #7c3aed; }

.flow-line {
  width: 36px;
  height: 1px;
  background: #d1d5db;
  position: relative;
}

.flow-line::after {
  content: '';
  position: absolute;
  right: 0;
  top: -2px;
  border: 3px solid transparent;
  border-left-color: #d1d5db;
}

/* ===== 通用 section ===== */
.section {
  max-width: 1120px;
  margin: 0 auto;
  padding: 80px 28px;
}

.module {
  max-width: 1120px;
  margin: 0 auto;
  padding: 72px 28px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 56px;
  align-items: center;
}

.module.reverse {
  direction: rtl;
}

.module.reverse > * {
  direction: ltr;
}

.module-tag {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: #2b6de9;
}

.module-text h2 {
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 14px 0 16px;
}

.module-desc {
  font-size: 15.5px;
  color: #6b7280;
  line-height: 1.75;
  margin-bottom: 22px;
}

.module-feats {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 28px;
}

.module-feats li {
  font-size: 14.5px;
  color: #374151;
  font-weight: 500;
}

.module-feats li::first-letter {
  color: #059669;
}

/* AI 对话 demo */
.chat-demo {
  background: #fff;
  border: 1px solid #eef0f5;
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-line {
  max-width: 82%;
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 13.5px;
  line-height: 1.6;
}

.chat-line.user {
  align-self: flex-end;
  background: #111827;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-line.ai {
  align-self: flex-start;
  background: #f3f4f6;
  color: #374151;
  border-bottom-left-radius: 4px;
}

/* IoT 设备 demo */
.device-demo {
  background: #111827;
  border-radius: 18px;
  padding: 24px;
  color: #fff;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.25);
}

.dev-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #9ca3af;
  margin-bottom: 18px;
}

.dev-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.dev-metric {
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}

.dev-metric span {
  display: block;
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 6px;
}

.dev-metric b {
  font-size: 22px;
  font-weight: 700;
}

.dev-metric b small {
  font-size: 13px;
  font-weight: 500;
  color: #9ca3af;
}

.dev-metric b.ok {
  font-size: 18px;
}

/* 代码 demo */
.code-demo {
  background: #111827;
  border-radius: 18px;
  padding: 26px;
  font-family: 'SF Mono', Consolas, monospace;
  font-size: 13px;
  line-height: 2;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.25);
}

.code-line .c-k { color: #7aa5f0; }
.code-line .c-u { color: #93c5fd; }
.code-line .c-v { color: #6ee7b7; }
.code-line .c-p { color: #f0abfc; }
.code-line.br { height: 4px; }

/* Demo 实验室 */
.lab {
  text-align: center;
}

.lab-head {
  margin-bottom: 36px;
}

.lab-head h2 {
  font-size: 32px;
  font-weight: 800;
  margin-top: 10px;
}

.lab-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.lab-card {
  border: 1px solid #eef0f5;
  border-radius: 16px;
  padding: 26px 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
}

.lab-card:hover {
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  transform: translateY(-3px);
}

.lab-icon {
  font-size: 30px;
}

.lab-card b {
  font-size: 15px;
  color: inherit;
}

.lab-card span {
  font-size: 12.5px;
  color: #6b7280;
}

/* 已上线 demo 卡片：醒目强调 */
.lab-card.active {
  border: 1.5px solid #2b6de9;
  background: linear-gradient(160deg, #f0f4ff, #ffffff);
  box-shadow: 0 8px 26px rgba(43, 109, 233, 0.14);
}

.lab-card.active:hover {
  border-color: #8b5cf6;
  box-shadow: 0 14px 38px rgba(43, 109, 233, 0.22);
  transform: translateY(-3px);
}

.lab-state {
  font-size: 11.5px !important;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 4px 12px;
  border-radius: 999px;
  background: #eef0f5;
  color: #6b7280 !important;
}

.lab-card.active .lab-state {
  background: linear-gradient(135deg, #2b6de9, #8b5cf6);
  color: #fff !important;
}

.lab-cta {
  margin-top: 36px;
}

/* 技术栈 */
.trust {
  text-align: center;
  padding-top: 40px;
  padding-bottom: 72px;
}

.trust-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: #9ca3af;
  margin-bottom: 20px;
}

.trust-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.trust-chip {
  font-size: 13px;
  font-weight: 600;
  color: #4b5563;
  padding: 8px 18px;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  background: #fafbfd;
}

/* Footer */
.footer {
  background: #0f1117;
  color: #d1d5db;
  padding: 56px 28px 24px;
}

.footer-inner {
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  gap: 40px;
  flex-wrap: wrap;
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.footer-brand b {
  font-size: 16px;
  color: #fff;
}

.footer-brand span {
  font-size: 13px;
  color: #6b7280;
}

.footer-cols {
  display: flex;
  gap: 60px;
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.footer-col b {
  font-size: 13px;
  color: #9ca3af;
  margin-bottom: 4px;
}

.footer-col a {
  font-size: 13.5px;
  color: #d1d5db;
  text-decoration: none;
}

.footer-col a:hover {
  color: #fff;
}

.footer-bottom {
  max-width: 1120px;
  margin: 40px auto 0;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 12.5px;
  color: #6b7280;
}

@media (max-width: 860px) {
  .hero-title { font-size: 44px; }
  .hero-sub-title { font-size: 22px; }
  .module, .module.reverse { grid-template-columns: 1fr; gap: 32px; }
  .footer-inner { flex-direction: column; }
}
</style>