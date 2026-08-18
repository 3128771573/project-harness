<template>
  <div class="turing-page">
    <SiteNav />

    <div class="turing-stage">
      <canvas ref="canvasRef" class="turing-canvas"></canvas>

      <!-- 演示标题 -->
      <div class="demo-head" v-if="!infoCollapsed">
        <span class="demo-badge">DEMO · LIVE</span>
        <h1>图灵斑图<span class="en">Turing Pattern</span></h1>
        <p class="demo-sub">Gray-Scott 反应扩散 · GPU 实时模拟 · 每次刷新随机纹路</p>
      </div>

      <!-- 介绍面板（半透明，不遮挡主体） -->
      <div class="info-panel" :class="{ collapsed: infoCollapsed }">
        <button class="info-toggle" @click="infoCollapsed = !infoCollapsed">{{ infoCollapsed ? '☰' : '✕' }}</button>
        <template v-if="!infoCollapsed">
          <h2>关于图灵斑图</h2>
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

      <!-- 返回 demo 目录 -->
      <div class="back-link">
        <router-link to="/demo">← 返回 Demo 实验室</router-link>
      </div>

      <!-- 不支持提示 -->
      <div v-if="error" class="gl-error">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import SiteNav from '../../components/SiteNav.vue'
import { ANIMALS, createTuring } from '../../utils/turing'

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

/* 演示标题：中央偏上 */
.demo-head {
  position: absolute;
  top: 56px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  z-index: 9;
  pointer-events: none;
  max-width: 92vw;
}

.demo-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.28em;
  color: rgba(255, 255, 255, 0.75);
  background: rgba(10, 12, 16, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 999px;
  padding: 5px 14px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  margin-bottom: 14px;
}

.demo-head h1 {
  margin: 0;
  font-size: clamp(26px, 4vw, 40px);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #fff;
  text-shadow: 0 2px 20px rgba(0, 0, 0, 0.55);
  line-height: 1.15;
}

.demo-head h1 .en {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 0.22em;
  margin-top: 6px;
}

.demo-sub {
  margin: 10px auto 0;
  font-size: 13px;
  color: rgba(238, 242, 247, 0.8);
  text-shadow: 0 1px 10px rgba(0, 0, 0, 0.6);
}

/* 介绍面板：半透明、左上角 */
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

.info-panel h2 {
  margin: 0 0 10px;
  font-size: 16px;
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

/* 返回链接 */
.back-link {
  position: absolute;
  right: 16px;
  top: 16px;
  z-index: 10;
}

.back-link a {
  color: rgba(238, 242, 247, 0.7);
  font-size: 12.5px;
  text-decoration: none;
  background: rgba(10, 12, 16, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 999px;
  padding: 7px 14px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: all 0.2s;
}

.back-link a:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.14);
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
  .demo-head {
    top: 44px;
  }
  .info-panel {
    max-width: 78vw;
    padding: 12px 14px;
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
