<template>
  <div class="page">
    <SiteNav />
    <div class="page-inner">
      <header class="page-head">
        <span class="page-tag">IOT PLATFORM</span>
        <h1>IoT 设备平台</h1>
        <p>连接传感器与设备，构建智能应用</p>
      </header>

      <div class="iot-hero">
        <div class="device-card">
          <div class="dev-head"><span class="live-dot"></span> 设备状态 · 在线</div>
          <div class="dev-big">
            <span>温度</span>
            <b>26.5<small>℃</small></b>
          </div>
          <div class="dev-row">
            <div class="dev-m"><span>湿度</span><b>60%</b></div>
            <div class="dev-m"><span>设备</span><b>ESP32</b></div>
            <div class="dev-m"><span>协议</span><b>MQTT</b></div>
          </div>
        </div>
        <div class="iot-text">
          <h2>从传感器到仪表盘</h2>
          <p>数据链路：设备 → MQTT → FastAPI → PostgreSQL → Dashboard。专为智能测控与工业互联网场景设计。</p>
          <ul>
            <li>✓ 设备接入与认证</li>
            <li>✓ 实时数据采集存储</li>
            <li>✓ 可视化监控大屏</li>
            <li>✓ 告警与历史回放</li>
          </ul>
          <span class="soon">🚧 平台建设中 · v1.0 上线</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import SiteNav from '../components/SiteNav.vue'
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #fff;
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
  color: #059669;
}

.page-head h1 {
  font-size: 38px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 12px 0 10px;
}

.page-head p {
  color: #6b7280;
  font-size: 15px;
}

.iot-hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  align-items: center;
}

.device-card {
  background: #111827;
  border-radius: 20px;
  padding: 28px;
  color: #fff;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.25);
}

.dev-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #9ca3af;
  font-weight: 600;
  margin-bottom: 20px;
}

.live-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.25);
}

.dev-big {
  text-align: center;
  padding: 20px 0;
  margin-bottom: 16px;
}

.dev-big span {
  display: block;
  font-size: 13px;
  color: #9ca3af;
}

.dev-big b {
  font-size: 48px;
  font-weight: 800;
}

.dev-big small {
  font-size: 18px;
  color: #9ca3af;
  font-weight: 500;
}

.dev-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.dev-m {
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 14px;
  text-align: center;
}

.dev-m span {
  display: block;
  font-size: 11.5px;
  color: #9ca3af;
  margin-bottom: 4px;
}

.dev-m b {
  font-size: 15px;
}

.iot-text h2 {
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 14px;
}

.iot-text p {
  color: #6b7280;
  line-height: 1.75;
  font-size: 15px;
  margin-bottom: 20px;
}

.iot-text ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
}

.iot-text li {
  font-size: 14.5px;
  font-weight: 500;
  color: #374151;
}

.soon {
  display: inline-block;
  font-size: 13px;
  font-weight: 600;
  color: #b45309;
  background: #fffbeb;
  padding: 8px 16px;
  border-radius: 999px;
}

@media (max-width: 760px) {
  .iot-hero {
    grid-template-columns: 1fr;
  }
}
</style>
