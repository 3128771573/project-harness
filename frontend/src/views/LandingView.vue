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

        <div class="hero-inner">
          <!-- 左：文案 -->
          <div class="hero-text">
            <div class="hero-badge">
              <span class="badge-dot"></span>
              AI + IoT Digital Platform
            </div>
            <h1 class="hero-title">
              Build Intelligent Systems
              <span class="grad">with AI + IoT</span>
            </h1>
            <p class="hero-desc">
              面向个人开发者的智能服务平台。连接人工智能、物联网与数字服务，从原型到产品。
            </p>
            <div class="hero-actions">
              <router-link to="/register" class="btn dark lg">Start Building →</router-link>
              <router-link to="/demo" class="btn outline lg">Explore Demo</router-link>
            </div>
            <div class="hero-stats">
              <div class="hs-item"><b>9+</b><span>版本迭代</span></div>
              <div class="hs-item"><b>20+</b><span>API 接口</span></div>
              <div class="hs-item"><b>3</b><span>核心模块</span></div>
            </div>
          </div>

          <!-- 右：产品预览图 mockup -->
          <div class="hero-visual">
            <div class="mock-window">
              <div class="mock-bar">
                <span class="mb-dot red"></span><span class="mb-dot yellow"></span><span class="mb-dot green"></span>
                <span class="mb-title">harness · workspace</span>
              </div>
              <div class="mock-body">
                <!-- AI 对话气泡 -->
                <div class="mock-ai">
                  <div class="mock-ai-head"><span class="mai-dot"></span> AI Assistant</div>
                  <div class="mock-msg ai">帮我分析今天的设备数据</div>
                  <div class="mock-msg user">温度稳定在 26.5°C，湿度 60%，无异常告警。建议继续监测。</div>
                </div>
                <!-- IoT 指标 -->
                <div class="mock-iot">
                  <div class="mi-item"><span>温度</span><b>26.5<small>°C</small></b></div>
                  <div class="mi-item"><span>湿度</span><b>60<small>%</small></b></div>
                  <div class="mi-item online"><span>在线</span><b>🟢</b></div>
                </div>
                <!-- Analytics 曲线 -->
                <div class="mock-chart">
                  <div class="mc-head"><span>Analytics</span><b class="mc-live">LIVE</b></div>
                  <svg viewBox="0 0 260 70" preserveAspectRatio="none" class="mc-svg">
                    <polyline points="0,55 30,48 60,52 90,38 120,42 150,28 180,34 210,18 240,24 260,12"
                      fill="none" stroke="url(#mcgrad)" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
                    <defs>
                      <linearGradient id="mcgrad" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0" stop-color="#6366F1"/><stop offset="1" stop-color="#8B5CF6"/>
                      </linearGradient>
                    </defs>
                  </svg>
                </div>
              </div>
            </div>
            <!-- 浮动徽章 -->
            <div class="float-chip chip-1">✦ AI 流式输出</div>
            <div class="float-chip chip-2">📡 设备在线</div>
          </div>
        </div>
      </section>

      <!-- 核心能力 -->
      <section class="section core">
        <h2 class="section-title">核心能力</h2>
        <div class="core-grid">
          <div class="core-card">
            <div class="cc-icon ai">✦</div>
            <b>AI Service</b>
            <span>多模型对话 · 历史记录 · 用量统计</span>
          </div>
          <div class="core-card">
            <div class="cc-icon iot">◎</div>
            <b>IoT Platform</b>
            <span>设备接入 · 实时数据 · 可视化</span>
          </div>
          <div class="core-card">
            <div class="cc-icon dev">⌘</div>
            <b>Developer Tools</b>
            <span>REST API · 统一鉴权 · 版本化</span>
          </div>
        </div>
      </section>

      <!-- 架构链路 -->
      <section class="section arch">
        <h2 class="section-title">全链路架构</h2>
        <p class="arch-sub">从浏览器到设备，一条完整的数据通路</p>
        <div class="arch-chain">
          <div class="arch-node" v-for="(a, i) in arch" :key="a.name">
            <div class="arch-icon">{{ a.icon }}</div>
            <b>{{ a.name }}</b>
            <span>{{ a.desc }}</span>
            <div v-if="i < arch.length - 1" class="arch-connector">
              <span class="ac-line"></span>
              <span class="ac-arrow">↓</span>
            </div>
          </div>
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
          <div class="lab-card" v-for="d in demos" :key="d.name">
            <div class="lab-icon">{{ d.icon }}</div>
            <b>{{ d.name }}</b>
            <span>{{ d.desc }}</span>
          </div>
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

const arch = [
  { icon: '⚡', name: 'Vue 3', desc: 'Web 前端 · SPA' },
  { icon: '🖥', name: 'FastAPI', desc: 'API 服务 · 鉴权' },
  { icon: '🗄', name: 'PostgreSQL', desc: '数据持久化' },
  { icon: '📡', name: 'MQTT', desc: '设备通信协议' },
  { icon: '🔌', name: 'Devices', desc: '传感器 · 智能硬件' },
]

const demos = [
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
  background: var(--bg-card);
  color: var(--text-primary);
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
  color: var(--text-muted);
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
  border: 1px solid var(--border-light);
  border-radius: 16px;
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
}

.quick-card:hover {
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  transform: translateY(-2px);
  border-color: var(--text-secondary);
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

.quick-card.ai .q-icon { background: var(--bg-active); color: #4338ca; }
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
  color: var(--text-muted);
}

.q-arrow {
  margin-left: auto;
  color: var(--text-muted);
  font-size: 16px;
}

.panel-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.panel-card {
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 22px;
}

.panel-card h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
}

.panel-num {
  font-size: 28px;
  font-weight: 800;
  margin: 10px 0 4px;
}

.panel-sub {
  font-size: 12.5px;
  color: var(--text-muted);
}

.live-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.2);
}

/* ===== Hero（左右布局） ===== */
.hero {
  position: relative;
  overflow: hidden;
  background: var(--bg-primary);
  min-height: 640px;
  display: flex;
  align-items: center;
}

.hero-bg {
  position: absolute;
  inset: 0;
}

.grid-layer {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(var(--border-light) 1px, transparent 1px),
    linear-gradient(90deg, var(--border-light) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(ellipse 80% 70% at 60% 40%, #000 20%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse 80% 70% at 60% 40%, #000 20%, transparent 70%);
}

.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(110px);
  opacity: 0.35;
  pointer-events: none;
}

.glow-1 {
  width: 520px;
  height: 520px;
  background: #6366f1;
  top: -180px;
  right: 5%;
}

.glow-2 {
  width: 440px;
  height: 440px;
  background: #8b5cf6;
  bottom: -200px;
  left: -120px;
}

.hero-inner {
  position: relative;
  z-index: 2;
  max-width: 1120px;
  margin: 0 auto;
  padding: 72px 28px;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 56px;
  align-items: center;
  width: 100%;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  padding: 7px 16px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
}

.badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.2);
}

.hero-title {
  font-size: 50px;
  font-weight: 800;
  letter-spacing: -0.035em;
  line-height: 1.12;
  margin-bottom: 20px;
  color: var(--text-primary);
}

.grad {
  display: block;
  background: var(--gradient-brand);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero-desc {
  font-size: 16.5px;
  color: var(--text-muted);
  line-height: 1.75;
  margin-bottom: 32px;
  max-width: 460px;
}

.hero-actions {
  display: flex;
  gap: 14px;
  margin-bottom: 40px;
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
  padding: 14px 28px;
  font-size: 15px;
}

.btn.dark {
  background: var(--brand-block);
  color: #fff;
  box-shadow: var(--shadow);
}

.btn.dark:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn.outline {
  background: transparent;
  color: var(--text-primary);
  border-color: var(--border-color);
}

.btn.outline:hover {
  border-color: var(--text-primary);
}

.hero-stats {
  display: flex;
  gap: 36px;
}

.hs-item {
  display: flex;
  flex-direction: column;
}

.hs-item b {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.hs-item span {
  font-size: 12.5px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* ===== 产品预览图 mockup ===== */
.hero-visual {
  position: relative;
}

.mock-window {
  background: var(--brand-block);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-color);
}

.mock-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.mb-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.mb-dot.red { background: #ef4444; }
.mb-dot.yellow { background: #f59e0b; }
.mb-dot.green { background: #10b981; }

.mb-title {
  margin-left: 8px;
  font-size: 11.5px;
  color: rgba(255, 255, 255, 0.45);
  letter-spacing: 0.02em;
}

.mock-body {
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.mock-ai {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 14px;
}

.mock-ai-head {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  font-weight: 700;
  color: #e2e8f0;
  margin-bottom: 10px;
}

.mai-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25);
}

.mock-msg {
  font-size: 12px;
  line-height: 1.6;
  border-radius: 10px;
  padding: 9px 12px;
  margin-bottom: 7px;
}

.mock-msg:last-child {
  margin-bottom: 0;
}

.mock-msg.ai {
  background: rgba(255, 255, 255, 0.07);
  color: #cbd5e1;
  border-bottom-left-radius: 3px;
}

.mock-msg.user {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  border-bottom-right-radius: 3px;
  margin-left: 30px;
}

.mock-iot {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.mi-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 12px 10px;
  text-align: center;
}

.mi-item span {
  display: block;
  font-size: 10.5px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}

.mi-item b {
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
}

.mi-item b small {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
}

.mi-item.online b {
  font-size: 14px;
}

.mock-chart {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 14px;
}

.mc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #cbd5e1;
  margin-bottom: 8px;
}

.mc-live {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: #ef4444;
  color: #fff;
  padding: 2px 7px;
  border-radius: 4px;
  animation: blink 1.5s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.mc-svg {
  width: 100%;
  height: 56px;
}

/* 浮动徽章 */
.float-chip {
  position: absolute;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  padding: 8px 16px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-secondary);
  box-shadow: var(--shadow);
  animation: floaty 4s ease-in-out infinite;
}

.chip-1 {
  top: -16px;
  left: -20px;
}

.chip-2 {
  bottom: -14px;
  right: -14px;
  animation-delay: 2s;
}

@keyframes floaty {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

@media (max-width: 900px) {
  .hero-inner {
    grid-template-columns: 1fr;
    gap: 40px;
  }
  .hero-title {
    font-size: 38px;
  }
  .hero-visual {
    max-width: 460px;
  }
}

/* ===== 通用 section ===== */
.section {
  max-width: 1120px;
  margin: 0 auto;
  padding: 80px 28px;
}

.section-title {
  font-size: 30px;
  font-weight: 800;
  text-align: center;
  letter-spacing: -0.02em;
  margin-bottom: 44px;
}

/* 核心能力 */
.core-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
}

.core-card {
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 30px 26px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: box-shadow 0.2s, transform 0.2s, border-color 0.2s;
}

.core-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-3px);
  border-color: #dbe2ee;
}

.cc-icon {
  width: 46px;
  height: 46px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 21px;
  margin-bottom: 6px;
}

.cc-icon.ai { background: var(--bg-active); color: #4338ca; }
.cc-icon.iot { background: #ecfdf5; color: #059669; }
.cc-icon.dev { background: #f5f3ff; color: #7c3aed; }

.core-card b {
  font-size: 16.5px;
  font-weight: 700;
}

.core-card span {
  font-size: 13.5px;
  color: var(--text-muted);
}

/* 架构链路 */
.arch {
  text-align: center;
}

.arch-sub {
  color: var(--text-muted);
  font-size: 14.5px;
  margin-top: -32px;
  margin-bottom: 44px;
}

.arch-chain {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 0;
  flex-wrap: wrap;
}

.arch-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 150px;
  padding: 0 10px;
}

.arch-icon {
  width: 52px;
  height: 52px;
  border-radius: 15px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.arch-node b {
  font-size: 14.5px;
  font-weight: 700;
  color: var(--text-primary);
}

.arch-node span {
  font-size: 12px;
  color: var(--text-muted);
}

.arch-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 4px;
  align-self: flex-start;
  margin-top: 20px;
}

.ac-line {
  width: 40px;
  height: 1px;
  background: var(--border-color);
}

.ac-arrow {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 2px;
}

@media (max-width: 900px) {
  .arch-chain {
    flex-direction: column;
    align-items: center;
    gap: 0;
  }
  .arch-connector {
    flex-direction: row;
    margin: 0;
    padding: 4px 0;
    transform: rotate(90deg);
  }
  .arch-node {
    width: auto;
  }
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
  color: var(--text-muted);
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
  color: var(--text-secondary);
  font-weight: 500;
}

.module-feats li::first-letter {
  color: #059669;
}

/* AI 对话 demo */
.chat-demo {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
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
  background: var(--brand-block);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-line.ai {
  align-self: flex-start;
  background: var(--bg-code);
  color: var(--text-secondary);
  border-bottom-left-radius: 4px;
}

/* IoT 设备 demo */
.device-demo {
  background: var(--brand-block);
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
  color: var(--text-muted);
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
  color: var(--text-muted);
  margin-bottom: 6px;
}

.dev-metric b {
  font-size: 22px;
  font-weight: 700;
}

.dev-metric b small {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}

.dev-metric b.ok {
  font-size: 18px;
}

/* 代码 demo */
.code-demo {
  background: var(--brand-block);
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
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 26px 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  transition: box-shadow 0.2s, transform 0.2s;
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
}

.lab-card span {
  font-size: 12.5px;
  color: var(--text-muted);
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
  color: var(--text-muted);
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
  color: var(--text-secondary);
  padding: 8px 18px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: var(--bg-input);
}

/* Footer */
.footer {
  background: var(--brand-block);
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
  color: var(--text-muted);
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
  color: var(--text-muted);
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
  color: var(--text-muted);
}

@media (max-width: 860px) {
  .hero-title { font-size: 44px; }
  .hero-sub-title { font-size: 22px; }
  .module, .module.reverse { grid-template-columns: 1fr; gap: 32px; }
  .footer-inner { flex-direction: column; }
}
</style>
