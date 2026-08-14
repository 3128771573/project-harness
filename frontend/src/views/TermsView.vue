<template>
  <div class="page">
    <SiteNav />
    <div class="page-inner">
      <header class="page-head">
        <span class="page-tag">LEGAL</span>
        <h1>用户协议</h1>
        <p>版本 v1.1 · 生效日期 2026-08-15 · 适用于 Harness 平台全部服务（含站内消息系统）</p>
      </header>

      <article class="prose">
        <section>
          <h2>1. 服务说明</h2>
          <p>Harness 平台（以下简称"本平台"）向注册用户提供 AI 对话、IoT 设备管理、站内私信与群聊、公告通知等信息服务。使用本服务即表示您同意本协议全部条款。</p>
        </section>

        <section>
          <h2>2. 账号规则</h2>
          <ul>
            <li>注册需提供有效邮箱并完成验证码验证；用户名不得冒用他人身份或包含违法违规内容。</li>
            <li>您应妥善保管账号与密码，因保管不善造成的损失由您自行承担；发现账号异常请立即联系平台。</li>
            <li>账号仅限本人使用，禁止出租、出借、转让或出售账号。</li>
          </ul>
        </section>

        <section>
          <h2>3. 即时通讯功能条款</h2>
          <h3>3.1 消息保存期限</h3>
          <p>私信与群聊消息默认保存 365 天（平台可调整该期限并提前公告），到期由系统自动清理；被举报并处理的消息按审核流程保留必要记录。</p>
          <h3>3.2 内容审核机制</h3>
          <p>为履行网络信息内容生态治理义务，平台对消息内容进行自动审核（敏感词过滤）与人工抽查审核。命中违规内容的消息将被拦截或删除，不向接收方展示。</p>
          <h3>3.3 举报与处置</h3>
          <p>每条消息提供举报入口。平台在收到举报后审核处理（删除消息 / 警告 / 封禁账号 / 忽略），处理结果通过系统机器人私信告知举报者。对涉嫌违法犯罪的内容，平台将依法向有关部门报告。</p>
          <h3>3.4 撤回与删除规则</h3>
          <p>发送后 2 分钟内可撤回本人消息（双方视图同步标记"已撤回"，平台保留审计元数据）；删除会话仅隐藏本人视图，不删除对方记录；注销账号时，您的私信记录将被删除，群聊中您发送的消息将匿名化为"已注销用户"。</p>
          <h3>3.5 水印与溯源声明</h3>
          <p>消息页面叠加<b>可见水印</b>（昵称 + UID + 时间）与<b>不可见溯源水印</b>（像素级水印与文本级零宽字符水印）。您复制、截图或转发消息内容时，相关内容可被平台技术手段识别并追溯至您的账号。因外泄、传播平台内容引发的法律责任由行为人自行承担，平台有权依据溯源结果配合维权与执法。</p>
          <h3>3.6 禁止内容</h3>
          <p>禁止利用本平台发布、传播以下内容：违反宪法确定的基本原则的；危害国家安全、泄露国家秘密的；煽动颠覆、破坏国家统一的；宣扬恐怖主义、极端主义的；宣扬民族仇恨、民族歧视的；传播淫秽色情、赌博、毒品、诈骗信息的；侮辱、诽谤他人，侵害他人合法权益的；侵犯知识产权或商业秘密的；其他法律法规禁止的内容。</p>
          <h3>3.7 违规处理</h3>
          <p>视情节轻重，平台可采取：拦截或删除内容、警告、限制功能、封禁账号、注销账号，以及依法向有关部门举报。</p>
        </section>

        <section>
          <h2>4. 未成年人保护</h2>
          <p>本平台服务面向年满 18 周岁用户。未满 18 周岁的未成年人应在监护人同意与指导下使用，监护人应引导未成年人健康上网、防范网络风险。平台如发现未成年人未经监护人同意注册，有权限制或终止相关服务。</p>
        </section>

        <section>
          <h2>5. 免责声明</h2>
          <p>平台按"现状"提供服务，对因不可抗力、网络故障、第三方服务中断导致的损失不承担赔偿责任；用户间因消息内容产生的纠纷由双方自行解决，平台依法提供协助。</p>
        </section>

        <section>
          <h2>6. 协议变更与联系</h2>
          <p>平台可适时修订本协议并在站内公告，修订后继续使用服务视为接受。意见与投诉请联系平台管理员（站内私信「Harness 官方」）。</p>
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

.prose h3 {
  font-size: 14.5px;
  margin: 14px 0 6px;
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
</style>
