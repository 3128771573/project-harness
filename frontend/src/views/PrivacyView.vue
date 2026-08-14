<template>
  <div class="page">
    <SiteNav />
    <div class="page-inner">
      <header class="page-head">
        <span class="page-tag">LEGAL</span>
        <h1>隐私政策</h1>
        <p>版本 v1.1 · 生效日期 2026-08-15 · 依据《中华人民共和国个人信息保护法》《网络安全法》《数据安全法》制定</p>
      </header>

      <article class="prose">
        <section>
          <h2>1. 我们收集的信息</h2>
          <ul>
            <li><b>注册信息</b>：邮箱、用户名、密码（加密存储）、头像与个人资料（您自愿填写）。</li>
            <li><b>登录信息</b>：登录时间、IP 地址、设备类型与浏览器（User-Agent）、登录方式（密码/验证码/第三方 SSO/2FA）。</li>
            <li><b>消息内容</b>：您发送与接收的私信、群聊消息及图片附件。</li>
            <li><b>第三方登录</b>：通过 GitHub 登录时，我们获取您在第三方平台的公开昵称、头像与账号标识。</li>
            <li><b>访问信息</b>：页面访问路径与时间（用于站点统计与安全审计）。</li>
          </ul>
        </section>

        <section>
          <h2>2. 信息的使用</h2>
          <ul>
            <li>提供与维护服务（消息投递、未读提醒、公告通知）；</li>
            <li>安全防护与审计（登录异常监测、操作审计留痕）；</li>
            <li>内容审核与合规（敏感词过滤、举报处理、配合执法）；</li>
            <li>服务优化（匿名统计，不涉及个人可识别信息）。</li>
          </ul>
          <p>我们<b>不会</b>向任何第三方出售您的个人信息。</p>
        </section>

        <section>
          <h2>3. 信息的存储与保护</h2>
          <ul>
            <li><b>传输加密</b>：全站 HTTPS，实时消息经 WSS 加密通道传输；</li>
            <li><b>存储保护</b>：密码使用加盐哈希存储；消息内容存储于受控数据库，平台将逐步升级为 AES-256-GCM 加密存储；</li>
            <li><b>访问控制</b>：消息仅发送双方（群聊为群成员）与依法授权的审核/管理员可见；越权访问一律拒绝并审计；</li>
            <li><b>密钥管理</b>：加密密钥存放于服务器环境变量，不在数据库中。</li>
          </ul>
        </section>

        <section>
          <h2>4. 数据保留期限</h2>
          <table class="tbl">
            <thead><tr><th>数据</th><th>保留期限</th></tr></thead>
            <tbody>
              <tr><td>站内消息（私信/群聊）</td><td>默认 365 天（平台可配置，到期自动清理）</td></tr>
              <tr><td>登录日志</td><td>365 天</td></tr>
              <tr><td>邮箱验证码</td><td>7 天</td></tr>
              <tr><td>设备遥测数据</td><td>90 天</td></tr>
              <tr><td>AI 对话历史</td><td>365 天</td></tr>
              <tr><td>被举报内容相关记录</td><td>按审核与合规需要保留</td></tr>
            </tbody>
          </table>
        </section>

        <section>
          <h2>5. 您的权利</h2>
          <ul>
            <li><b>访问与更正</b>：可在「设置」中查看与修改个人资料；</li>
            <li><b>删除（注销）</b>：可在「设置 - 注销账号」中自助注销；注销后私信记录被删除、群消息匿名化、账号信息清除；</li>
            <li><b>导出（数据携带权）</b>：可在私信页导出与对方的聊天记录；</li>
            <li><b>撤回同意</b>：可随时停止使用服务并注销账号。</li>
          </ul>
        </section>

        <section>
          <h2>6. 信息共享与披露</h2>
          <p>除以下情形外，我们不向第三方披露您的个人信息：获得您的明确同意；法律法规要求或行政、司法机关依法要求；为维护国家安全、社会公共利益所必需；为保障您或他人生命财产安全所必需。</p>
        </section>

        <section>
          <h2>7. Cookie 与本地存储</h2>
          <p>平台使用浏览器本地存储保存登录凭证与界面偏好（如主题、已读状态），不用于跨站追踪。</p>
        </section>

        <section>
          <h2>8. 未成年人保护</h2>
          <p>本平台主要面向成年人。我们不会主动收集未成年人个人信息；如发现误收集，将尽快删除。未成年人使用本服务应在监护人指导下进行。</p>
        </section>

        <section>
          <h2>9. 政策更新与联系</h2>
          <p>本政策更新将在站内公告；重大变更将以显著方式提示。任何隐私相关问题，请通过站内私信「Harness 官方」与我们联系。</p>
        </section>
      </article>
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
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 24px 60px;
}

.page-head {
  margin-bottom: 28px;
}

.page-tag {
  font-size: 12px;
  letter-spacing: 0.14em;
  color: var(--primary-color, #2b6de9);
  font-weight: 700;
}

.prose section {
  margin-bottom: 26px;
}

.prose h2 {
  font-size: 18px;
  margin: 0 0 10px;
  color: var(--text-primary, #111);
}

.prose p,
.prose li {
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--text-secondary, #555);
}

.prose ul {
  padding-left: 20px;
  margin: 8px 0;
}

.prose b {
  color: var(--text-primary, #111);
}

.tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin: 8px 0;
}

.tbl th,
.tbl td {
  border: 1px solid var(--border-color, #e5e7eb);
  padding: 8px 12px;
  text-align: left;
  color: var(--text-secondary, #555);
}

.tbl th {
  background: var(--bg-secondary, #f1f3f5);
  color: var(--text-primary, #111);
}
</style>
