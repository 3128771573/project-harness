<template>
  <div>
    <header class="page-head">
      <div>
        <h1>系统监控</h1>
        <p class="sub">
          {{ sys?.system?.hostname || 'X230' }} · {{ sys?.system?.os || '' }}
          <span v-if="autoRefresh" class="live-badge"><span class="pulse-dot"></span>实时刷新</span>
        </p>
      </div>
      <div class="actions">
        <span class="muted" style="font-size:12px">自动刷新 5s</span>
        <button class="btn" :disabled="loading" @click="load">
          <svg viewBox="0 0 24 24" style="width:14px;height:14px;fill:currentColor"><path d="M17.65 6.35A7.95 7.95 0 0012 4a8 8 0 108 8h-2a6 6 0 11-1.76-4.24L13 11h7V4l-2.35 2.35z"/></svg>
          {{ loading ? '刷新中…' : '立即刷新' }}
        </button>
      </div>
    </header>

    <div v-if="error" class="panel"><p class="error-text">{{ error }}</p></div>

    <template v-else-if="sys">
      <!-- 系统信息 -->
      <section class="sys-grid">
        <div class="sys-card">
          <div class="sys-label">主机名</div>
          <div class="sys-value">{{ sys.system.hostname }}</div>
        </div>
        <div class="sys-card">
          <div class="sys-label">操作系统</div>
          <div class="sys-value small">{{ sys.system.os }}</div>
        </div>
        <div class="sys-card">
          <div class="sys-label">内核版本</div>
          <div class="sys-value small">{{ sys.system.kernel }} ({{ sys.system.arch }})</div>
        </div>
        <div class="sys-card">
          <div class="sys-label">运行时长</div>
          <div class="sys-value">{{ sys.system.uptime }}</div>
        </div>
        <div class="sys-card">
          <div class="sys-label">进程数</div>
          <div class="sys-value">{{ sys.system.processes }}</div>
        </div>
        <div class="sys-card">
          <div class="sys-label">IP 地址</div>
          <div class="sys-value small">{{ (sys.system.ip || []).join(', ') || '—' }}</div>
        </div>
      </section>

      <!-- CPU / 内存 / 磁盘 主仪表 -->
      <section class="meter-grid">
        <div class="meter-card">
          <div class="meter-head">
            <span class="meter-title">CPU</span>
            <span class="meter-pct" :style="{ color: pctColor(sys.cpu.percent) }">{{ sys.cpu.percent }}%</span>
          </div>
          <div class="meter big"><div class="meter-fill" :style="fillStyle(sys.cpu.percent)"></div></div>
          <div class="meter-detail">
            <span><b>{{ sys.cpu.cores }}</b> 核</span>
            <span>{{ sys.cpu.freq }}</span>
            <span>{{ sys.cpu.model }}</span>
          </div>
          <div class="meter-sub-row">
            <span>负载</span>
            <span class="load-val">{{ sys.cpu.load[0] }} / {{ sys.cpu.load[1] }} / {{ sys.cpu.load[2] }}</span>
          </div>
        </div>

        <div class="meter-card">
          <div class="meter-head">
            <span class="meter-title">内存 RAM</span>
            <span class="meter-pct" :style="{ color: pctColor(sys.memory.percent) }">{{ sys.memory.percent }}%</span>
          </div>
          <div class="meter big"><div class="meter-fill" :style="fillStyle(sys.memory.percent)"></div></div>
          <div class="meter-detail">
            <span><b>{{ sys.memory.used_gb }}</b> / {{ sys.memory.total_gb }} GB</span>
            <span>可用 {{ sys.memory.available_gb }} GB</span>
            <span>缓存 {{ sys.memory.buff_cache_gb }} GB</span>
          </div>
          <div class="meter-sub-row">
            <span>Swap</span>
            <span class="load-val">{{ sys.memory.swap_used_gb }} / {{ sys.memory.swap_total_gb }} GB</span>
          </div>
        </div>

        <div class="meter-card">
          <div class="meter-head">
            <span class="meter-title">磁盘 Disk</span>
            <span class="meter-pct" :style="{ color: pctColor(sys.disk.main.percent) }">{{ sys.disk.main.percent }}%</span>
          </div>
          <div class="meter big"><div class="meter-fill" :style="fillStyle(sys.disk.main.percent)"></div></div>
          <div class="meter-detail">
            <span><b>{{ sys.disk.main.used_gb }}</b> / {{ sys.disk.main.total_gb }} GB</span>
            <span>可用 {{ sys.disk.main.free_gb }} GB</span>
            <span>挂载 {{ sys.disk.main.mount }}</span>
          </div>
          <div class="meter-sub-row">
            <span>分区</span>
            <span class="load-val">{{ sys.disk.mounts.length }} 个</span>
          </div>
        </div>
      </section>

      <!-- 网络实时 -->
      <section class="panel">
        <div class="panel-title">网络实时流量 <span class="live-tag">LIVE</span></div>
        <p class="panel-sub">非回环网卡 · 5 秒采样速率</p>
        <div class="net-grid">
          <div class="net-card down">
            <div class="net-arrow">↓</div>
            <div class="net-info">
              <div class="net-label">下载速率</div>
              <div class="net-value">{{ fmtSpeed(sys.network.rx_kbs) }}</div>
            </div>
          </div>
          <div class="net-card up">
            <div class="net-arrow">↑</div>
            <div class="net-info">
              <div class="net-label">上传速率</div>
              <div class="net-value">{{ fmtSpeed(sys.network.tx_kbs) }}</div>
            </div>
          </div>
          <div class="net-card total">
            <div class="net-arrow">⇅</div>
            <div class="net-info">
              <div class="net-label">累计流量</div>
              <div class="net-value">{{ sys.network.rx_total_gb }} GB ↓ · {{ sys.network.tx_total_gb }} GB ↑</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 磁盘分区明细 -->
      <section class="panel">
        <div class="panel-title">磁盘分区</div>
        <div class="table-wrap" style="border:none; border-radius:0; box-shadow:none">
          <table class="table">
            <thead>
              <tr>
                <th>设备</th>
                <th>挂载点</th>
                <th>容量</th>
                <th>已用</th>
                <th>可用</th>
                <th style="width:180px">使用率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in sys.disk.mounts" :key="m.mount">
                <td class="uid-cell">{{ m.device }}</td>
                <td class="muted">{{ m.mount }}</td>
                <td>{{ m.total_gb }} GB</td>
                <td>{{ m.used_gb }} GB</td>
                <td>{{ m.free_gb }} GB</td>
                <td>
                  <div class="mini-meter">
                    <div class="mini-track"><div class="mini-fill" :style="fillStyle(m.percent)"></div></div>
                    <span class="mini-pct">{{ m.percent }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- CPU 温度 -->
      <section v-if="sys.temps.length" class="panel">
        <div class="panel-title">CPU 温度</div>
        <div class="temp-row">
          <div v-for="t in sys.temps" :key="t.name" class="temp-chip">
            <span class="temp-name">{{ t.name }}</span>
            <span class="temp-val" :style="{ color: tempColor(t.temp) }">{{ t.temp }}°C</span>
          </div>
        </div>
      </section>
    </template>

    <section v-else class="panel"><p class="muted">加载中…</p></section>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import api from '../../api/client'

const sys = ref(null)
const error = ref('')
const loading = ref(false)
const autoRefresh = ref(true)
let timer = null

function fillStyle(pct) {
  return { width: Math.min(100, pct) + '%', background: pctColor(pct) }
}

function pctColor(pct) {
  if (pct >= 85) return '#dc2626'
  if (pct >= 60) return '#d97706'
  return '#22c55e'
}

function tempColor(temp) {
  if (temp >= 85) return '#dc2626'
  if (temp >= 65) return '#d97706'
  return '#22c55e'
}

function fmtSpeed(kbs) {
  if (kbs >= 1024) return (kbs / 1024).toFixed(2) + ' MB/s'
  return kbs + ' KB/s'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/admin/system/status')
    sys.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '系统监控加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  load()
  // 自动刷新：5 秒一次
  timer = setInterval(load, 5000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped src="../../assets/admin.css"></style>
