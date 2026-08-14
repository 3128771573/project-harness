<template>
  <div class="page">
    <SiteNav />
    <div class="page-inner">
      <header class="page-head">
        <span class="page-tag">PRICING</span>
        <h1>简单透明的定价</h1>
        <p>从免费开始，按需升级</p>
      </header>

      <div class="price-grid">
        <div v-for="p in plans" :key="p.name" class="price-card" :class="p.featured ? 'featured' : ''">
          <div v-if="p.featured" class="featured-tag">推荐</div>
          <h3>{{ p.name }}</h3>
          <div class="price">
            <span class="cur">¥</span><b>{{ p.price }}</b><span class="period">/月</span>
          </div>
          <p class="price-desc">{{ p.desc }}</p>
          <ul>
            <li v-for="f in p.feats" :key="f">✓ {{ f }}</li>
          </ul>
          <a
            v-if="p.cta === '联系我们'"
            href="mailto:contact@platformharness.ltd"
            class="btn"
            :class="p.featured ? 'dark' : 'outline'"
          >{{ p.cta }}</a>
          <router-link
            v-else
            to="/register"
            class="btn"
            :class="p.featured ? 'dark' : 'outline'"
          >{{ p.cta }}</router-link>
        </div>
      </div>

      <p class="hint">商业化规划中 · 当前所有功能免费开放</p>
    </div>
  </div>
</template>

<script setup>
import SiteNav from '../components/SiteNav.vue'

const plans = [
  {
    name: 'Free',
    price: '0',
    desc: '体验平台基础能力',
    feats: ['AI 对话 10 次/天', 'Demo 实验室访问', '基础 IoT 设备', '社区支持'],
    cta: '注册',
    featured: false,
  },
  {
    name: 'Pro',
    price: '29',
    desc: '适合个人开发者',
    feats: ['AI 对话 1000 次/天', '多模型切换', 'IoT 设备 20 台', '用量统计', '优先支持'],
    cta: '注册',
    featured: true,
  },
  {
    name: 'Enterprise',
    price: '定制',
    desc: '团队与商业项目',
    feats: ['不限量 AI 调用', '专属 API 额度', '私有化部署', 'SLA 保障', '专属客服'],
    cta: '联系我们',
    featured: false,
  },
]
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: var(--bg-card);
}

.page-inner {
  max-width: 960px;
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
  color: #2563eb;
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

.price-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  align-items: stretch;
}

.price-card {
  border: 1px solid transparent;
  border-radius: 18px;
  padding: 30px 26px;
  display: flex;
  flex-direction: column;
  position: relative;
  background:
    linear-gradient(var(--bg-card), var(--bg-card)) padding-box,
    linear-gradient(var(--border-light), var(--border-light)) border-box;
  transition: box-shadow 0.25s cubic-bezier(0.2, 0.8, 0.2, 1), transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.price-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
  background:
    linear-gradient(var(--bg-card), var(--bg-card)) padding-box,
    linear-gradient(135deg, var(--primary-color), var(--accent-color)) border-box;
}

.price-card.featured {
  border: 1px solid var(--primary-color);
  box-shadow: 0 12px 40px rgba(37, 99, 235, 0.15);
}

.featured-tag {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  color: #fff;
  font-size: 11.5px;
  font-weight: 700;
  padding: 4px 14px;
  border-radius: 999px;
}

.price-card h3 {
  font-size: 17px;
  font-weight: 700;
}

.price {
  display: flex;
  align-items: baseline;
  margin: 14px 0 6px;
}

.price .cur {
  font-size: 16px;
  font-weight: 600;
  margin-right: 2px;
}

.price b {
  font-size: 40px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.price .period {
  font-size: 13px;
  color: var(--text-muted);
  margin-left: 4px;
}

.price-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 18px;
}

.price-card ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
  flex: 1;
}

.price-card li {
  font-size: 13.5px;
  color: var(--text-secondary);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  border-radius: 11px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  border: 1px solid transparent;
  transition: all 0.15s;
}

.btn.dark {
  background: var(--brand-block);
  color: #fff;
}

.btn.dark:hover {
  background: #1e293b;
}

.btn.outline {
  border-color: #d1d5db;
  color: var(--text-primary);
  background: transparent;
}

.btn.outline:hover {
  border-color: var(--text-primary);
}

.hint {
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
  margin-top: 36px;
}
</style>
