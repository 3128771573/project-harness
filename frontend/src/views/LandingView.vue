<template>
  <div class="turing-page">
    <SiteNav />

    <div class="turing-stage">
      <canvas ref="canvasRef" class="turing-canvas"></canvas>

      <!-- 中央品牌区 -->
      <div class="hero" v-if="!infoCollapsed">
        <span class="hero-badge">REACTION · DIFFUSION · LIVE</span>
        <h1 class="hero-title">Project Harness</h1>
        <p class="hero-sub">AI 对话 · IoT 接入 · 图灵斑图实时演示<br class="br-mobile" />——自然界的算法，跑在你的浏览器里</p>
        <div class="hero-actions">
          <router-link to="/demo" class="hero-btn primary">
            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
            进入 Demo 实验室
          </router-link>
          <router-link to="/login" class="hero-btn ghost">开始使用</router-link>
        </div>
      </div>

      <!-- 功能入口 -->
      <div class="feature-row" v-if="!infoCollapsed">
        <router-link to="/ai" class="feature-card">
          <span class="fc-icon">🧠</span>
          <span class="fc-name">AI 对话</span>
          <span class="fc-desc">流式输出 · 多模型</span>
        </router-link>
        <router-link to="/iot" class="feature-card">
          <span class="fc-icon">📡</span>
          <span class="fc-name">IoT 接入</span>
          <span class="fc-desc">设备连接 · 实时监控</span>
        </router-link>
        <router-link to="/guestbook" class="feature-card">
          <span class="fc-icon">💬</span>
          <span class="fc-name">留言板</span>
          <span class="fc-desc">档案号 · 多轮回复</span>
        </router-link>
        <router-link to="/demo" class="feature-card">
          <span class="fc-icon">🧪</span>
          <span class="fc-name">Demo 实验室</span>
          <span class="fc-desc">技术实验 · 组件展示</span>
        </router-link>
      </div>

      <!-- 介绍面板（半透明，不遮挡主体） -->
      <div class="info-panel" :class="{ collapsed: infoCollapsed }">
        <button class="info-toggle" @click="infoCollapsed = !infoCollapsed">{{ infoCollapsed ? '☰' : '✕' }}</button>
        <template v-if="!infoCollapsed">
          <h1>图灵斑图<span class="en">Turing Pattern</span></h1>
          <p class="intro">
            1952 年，艾伦·图灵提出<b>反应扩散机制</b>（Reaction-Diffusion）来解释生物体表的图案形成：
            两种化学物质——<b>激活剂</b>与<b>抑制剂</b>——相互扩散与反应，自发涌现出斑点、条纹、迷宫等结构。
          </p>
          <p class="intro">
            自然界中斑马的黑白条纹、豹的金黄斑点、箱鲀的蓝白六边形、苏眉鱼的青蓝迷宫，
            都可以用这一模型在 GPU 上实时模拟出来（Gray-Scott 方程）。
          </p>
          <p class="hint">当前图案：<b class="animal-name">{{ currentName }}</b> · 按键盘 <b>1-{{ ANIMALS.length }}</b> 或点击下方按钮切换 · 刷新页面随机展示</p>
        </template>
      </div>

      <!-- 动物切换按钮 -->
      <div class="animal-bar">
        <button
          v-for="(a, i) in ANIMALS"
          :key="a.id"
          class="animal-btn"
          :class="{ on: current === i }"
          @click="switchAnimal(i)"
        >
          <span class="ab-key">{{ i + 1 }}</span>
          {{ a.name }}
        </button>
      </div>

      <!-- 合规链接（右下角小字） -->
      <div class="legal-links">
        <router-link to="/terms">用户协议</router-link>
        <router-link to="/privacy">隐私政策</router-link>
      </div>

      <!-- 不支持提示 -->
      <div v-if="error" class="gl-error">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import SiteNav from '../components/SiteNav.vue'
import { ANIMALS, createTuring } from '../utils/turing'

const canvasRef = ref(null)
const infoCollapsed = ref(false)
const current = ref(0)
const error = ref('')

let engine = null
let raf = 0

const currentName = computed(() => (engine ? engine.getAnimal().name : ANIMALS[current.value].name))

function resizeCanvas() {
  if (!engine || !canvasRef.value) return
  engine.resize(window.innerWidth, window.innerHeight - 60)
}

function loop() {
  if (!engine) return
  engine.step()
  engine.draw()
  raf = requestAnimationFrame(loop)
}

function switchAnimal(i) {
  if (!engine) return
  current.value = i % ANIMALS.length
  engine.setAnimal(current.value)
}

function onKey(ev) {
  const n = parseInt(ev.key, 10)
  if (n >= 1 && n <= ANIMALS.length) {
    switchAnimal(n - 1)
  }
}

onMounted(() => {
  const res = createTuring(canvasRef.value)
  if (!res.ok) {
    error.value = res.reason + '，图案演示不可用'
    return
  }
  engine = res
  // 随机选择动物（每次刷新新鲜感）
  current.value = Math.floor(Math.random() * ANIMALS.length)
  engine.setAnimal(current.value)
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
  window.addEventListener('keydown', onKey)
  raf = requestAnimationFrame(loop)
})

onUnmounted(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', resizeCanvas)
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.turing-page {
  min-height: 100vh;
  background: #0a0c10;
}

.turing-stage {
  position: relative;
  height: calc(100vh - 60px);
  overflow: hidden;
}

.turing-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
}

/* 中央品牌区 */
.hero {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -56%);
  text-align: center;
  z-index: 9;
  pointer-events: none;
  max-width: 92vw;
}

.hero-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.28em;
  color: rgba(255, 255, 255, 0.72);
  background: rgba(10, 12, 16, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 999px;
  padding: 6px 16px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  margin-bottom: 18px;
}

.hero-title {
  margin: 0;
  font-size: clamp(34px, 6vw, 60px);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #fff;
  text-shadow: 0 2px 24px rgba(0, 0, 0, 0.55);
  line-height: 1.1;
}

.hero-sub {
  margin: 14px auto 24px;
  font-size: clamp(13px, 1.7vw, 16.5px);
  color: rgba(238, 242, 247, 0.85);
  text-shadow: 0 1px 12px rgba(0, 0, 0, 0.6);
  line-height: 1.8;
  max-width: 620px;
}

.hero-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  pointer-events: auto;
}

.hero-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 999px;
  font-size: 14.5px;
  font-weight: 600;
  padding: 12px 26px;
  text-decoration: none;
  transition: all 0.2s ease;
}

.hero-btn svg {
  width: 16px;
  height: 16px;
  fill: currentColor;
}

.hero-btn.primary {
  background: linear-gradient(135deg, #ffd27a, #f5a623);
  color: #1a1408;
  box-shadow: 0 6px 24px rgba(245, 166, 35, 0.35);
}

.hero-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 32px rgba(245, 166, 35, 0.45);
}

.hero-btn.ghost {
  background: rgba(10, 12, 16, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.28);
  color: #eef2f7;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.hero-btn.ghost:hover {
  background: rgba(255, 255, 255, 0.14);
}

/* 功能入口 */
.feature-row {
  position: absolute;
  bottom: 74px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10px;
  z-index: 9;
  pointer-events: none;
  max-width: 94vw;
}

.feature-card {
  pointer-events: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 132px;
  padding: 14px 16px;
  border-radius: 16px;
  text-decoration: none;
  background: rgba(10, 12, 16, 0.48);
  border: 1px solid rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: all 0.22s ease;
}

.feature-card:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.32);
  transform: translateY(-4px);
}

.fc-icon {
  font-size: 22px;
}

.fc-name {
  font-size: 13.5px;
  font-weight: 600;
  color: #f2f5f9;
}

.fc-desc {
  font-size: 11px;
  color: rgba(238, 242, 247, 0.6);
}

/* 介绍面板：半透明、左上角、不遮挡主体 */
.info-panel {
  position: absolute;
  top: 16px;
  left: 16px;
  max-width: 340px;
  background: rgba(10, 12, 16, 0.55);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 14px;
  padding: 16px 18px;
  color: #eef2f7;
  z-index: 10;
}

.info-panel.collapsed {
  padding: 0;
  background: rgba(10, 12, 16, 0.4);
  border: none;
}

.info-toggle {
  position: absolute;
  top: 8px;
  right: 10px;
  border: none;
  background: rgba(255, 255, 255, 0.12);
  color: #eef2f7;
  border-radius: 8px;
  width: 26px;
  height: 26px;
  cursor: pointer;
  font-size: 13px;
  line-height: 1;
}

.info-panel.collapsed .info-toggle {
  position: static;
  display: block;
  margin: 8px;
}

.info-panel h1 {
  margin: 0 0 10px;
  font-size: 20px;
  letter-spacing: 0.02em;
}

.info-panel h1 .en {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: rgba(238, 242, 247, 0.55);
  letter-spacing: 0.18em;
  margin-top: 2px;
}

.intro {
  font-size: 12.5px;
  line-height: 1.75;
  color: rgba(238, 242, 247, 0.82);
  margin: 0 0 8px;
}

.intro b {
  color: #fff;
}

.hint {
  font-size: 11.5px;
  color: rgba(238, 242, 247, 0.6);
  margin: 6px 0 0;
}

.animal-name {
  color: #ffd27a;
}

/* 切换按钮：底部居中 */
.animal-bar {
  position: absolute;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 92vw;
}

.animal-btn {
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(10, 12, 16, 0.5);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: #eef2f7;
  border-radius: 999px;
  padding: 7px 14px;
  font-size: 12.5px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.animal-btn:hover {
  background: rgba(255, 255, 255, 0.16);
}

.animal-btn.on {
  background: rgba(255, 210, 122, 0.85);
  color: #1a1408;
  border-color: transparent;
  font-weight: 600;
}

.ab-key {
  opacity: 0.6;
  font-size: 11px;
  margin-right: 4px;
}

/* 合规链接 */
.legal-links {
  position: absolute;
  right: 14px;
  bottom: 14px;
  display: flex;
  gap: 12px;
  z-index: 10;
}

.legal-links a {
  color: rgba(238, 242, 247, 0.5);
  font-size: 11px;
  text-decoration: none;
}

.legal-links a:hover {
  color: rgba(238, 242, 247, 0.9);
}

.gl-error {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #eef2f7;
  background: #101318;
  font-size: 14px;
  z-index: 5;
}

@media (max-width: 640px) {
  .hero {
    top: 42%;
    transform: translate(-50%, -50%);
  }
  .hero-actions {
    flex-direction: column;
    align-items: center;
    gap: 10px;
  }
  .hero-btn {
    padding: 11px 22px;
    font-size: 13.5px;
  }
  .feature-row {
    bottom: 64px;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .feature-card {
    min-width: 0;
    flex: 1 1 42%;
    max-width: 170px;
    padding: 10px 12px;
  }
  .info-panel {
    max-width: 78vw;
    padding: 12px 14px;
  }
  .info-panel h1 {
    font-size: 16px;
  }
  .animal-bar {
    bottom: 12px;
    gap: 6px;
  }
  .animal-btn {
    padding: 6px 10px;
    font-size: 11.5px;
  }
}
</style>
