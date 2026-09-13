# Project Harness

> **个人智能服务平台 · Personal AI Service Platform**
> 连接 AI、IoT 与数字服务 —— Connect AI, Devices and Digital Experiences.

![status](https://img.shields.io/badge/status-%E5%B7%B2%E4%B8%8B%E7%BA%BF%20archived-lightgrey)
![version](https://img.shields.io/badge/version-0.10.1-blue)
![frontend](https://img.shields.io/badge/Vue-3-42b883)
![backend](https://img.shields.io/badge/FastAPI-async-009688)
![db](https://img.shields.io/badge/PostgreSQL-16-336791)
![deploy](https://img.shields.io/badge/Docker-Compose-2496ed)

---

## 📌 服务状态：已下线

**Project Harness 于 2026 年 9 月正式停止对外服务**（云服务器到期），官网已切换为[告别页](./farewell/index.html)。

- ✅ 全部数据（数据库 / 用户上传 / 配置 / 证书 / 代码）已**完整备份**并通过还原实测
- ✅ 源码、文档与技术沉淀**永久保留**在本仓库
- 📖 细节见 [备份与恢复](#-备份与恢复2026-09)

> 这不是结束，只是一次暂停。感谢每一位曾经使用的朋友。

---

## 项目简介

Project Harness 是一个**从零到线上**、长期迭代的个人全栈平台。它以「用户体系 → AI 服务 → 站内即时通讯 → 运营后台 → IoT 接入 → 合规与安全加固」为主线，把一名独立开发者能覆盖的工程面全部跑通一遍：前端产品化、后端异步架构、实时通信、数据库迁移、容器化部署、HTTPS 证书、运维自动化，乃至反应扩散（图灵斑图）实时渲染这类创意编程实验。

**规模概览**

| 维度 | 数据 |
|---|---|
| 数据库 | PostgreSQL 16 · **33 张表** · 迁移链 `a6b7c8d9e0f1` |
| 后端模块 | 14 个路由模块 · **21 个服务模块** |
| 前端页面 | 19 个前台页面 + 16 个 Admin 页面 + 图灵斑图演示页 |
| 容器 | db / backend / frontend / mqtt / sim 共 **5 个** |
| 运行数据 | 注册用户 30 · 私信 680 条 · 设备遥测 **129 万+** 条 · 审计日志 1,180 条 |
| 迭代周期 | v0.1 → v0.10.1，Demo → 内网 → 云端 HTTPS 正式部署 |

---

## ✨ 项目亮点

| 亮点 | 说明 |
|---|---|
| 🧠 **AI 对话** | SSE 流式输出、深度思考（reasoning）折叠、Markdown + LaTeX(KaTeX) + 代码高亮、多会话与用量额度、每用户并发槽位限制 |
| 💬 **完整 IM 系统** | 私信 + 群聊 + 公告机器人；WebSocket 房间广播、已读回执、撤回、拉黑、举报审核闭环 |
| 🔒 **双层水印溯源** | 可见水印（昵称+UID+时间）+ **零宽字符文本水印**；复制走文本也能解码溯源，含授权额度与审计 |
| 🛡️ **企业级维护模式** | 四种模式（全站 / 仅拦截新访客 / 定时 / 仅管理员）、三级自动恢复、64 位紧急令牌逃生通道、多渠道通知、部署自动联动 |
| 🎨 **图灵斑图 Demo** | WebGL2 + 浮点纹理实时跑 Gray-Scott 反应扩散方程，7 种动物纹路，见下方技术详解 |
| 📊 **企业级日志导出** | 审计 / 登录 / 访问 / 取证 / 举报 / 机器人六大数据源，筛选 + 预览 + CSV(BOM)/JSON + SHA-256 完整性校验 |
| ✅ **合规化闭环** | 用户协议 + 隐私政策（含 IM 条款、水印声明）、账号注销、聊天记录导出（数据携带权）、敏感词过滤、消息保留期清理 |
| 🐳 **一键部署** | Docker Compose + Nginx(HTTPS) + Let's Encrypt 自动续期；部署脚本自动切入/退出维护模式 |

---

## 🎨 图灵斑图（Turing Pattern）· 技术详解

1952 年图灵提出**反应扩散机制**解释生物体表图案：激活剂与抑制剂相互扩散与反应，自发涌现斑点、条纹、迷宫等结构。本项目在浏览器端实时复刻了这一过程。

**实现要点**

```
WebGL2 + RGBA32F 浮点纹理（不支持时降级 RGBA16F）
  ├─ 512 × 512 仿真网格，ping-pong FBO 双缓冲
  ├─ 9 点拉普拉斯核：中心 -1，正交 0.2，对角 0.05
  ├─ Gray-Scott 方程：
  │    u' = u + du·∇²u − u·v² + f·(1−u)
  │    v' = v + dv·∇²v + u·v² − (f+k)·v
  ├─ 5000 步预模拟（避免看到"未完成演化"的初始态）
  └─ 渲染取 u 通道（对比度强：图案区 u≈0.3 / 背景 u≈0.9）
```

**7 种动物预设**（Pearson 经典参数 + 方向性种子）

| 动物 | f / k | 种子形态 | 呈现 |
|---|---|---|---|
| 斑马 | 0.0545 / 0.062 | 竖细条 | 竖条纹 |
| 老虎 | 0.0545 / 0.062 | 横细条 | 横条纹 |
| 豹 | 0.026 / 0.058 | 随机块 | 金黄斑点 |
| 长颈鹿 | 0.026 / 0.058 | 大块 | 大块斑纹 |
| 苏眉鱼 | 0.030 / 0.062 | 随机块 | 青蓝迷宫 |
| 蝴蝶鱼 | 0.030 / 0.062 | 斜条 + 块 | 斜向纹路 |
| 箱鲀 | 0.0545 / 0.062 | 蜂窝网格 | 蓝白六边格 |

**踩过的关键坑（值得记录）**

1. **种子区域必须 `u=0, v=1`** —— 若沿用常见的 `u=1` 初始化或纯噪声种子，`u·v²` 项无法启动反应，浓度会一路衰减到全黑；
2. **方向性由种子形状引导** —— 竖长条种子 → 竖条纹，横长条种子 → 横条纹（各向同性种子只会得到迷宫）；
3. 参数先在 CPU 上用镜像实现穷举验证，再上 GPU，避免"部署后才发现是白屏"。

演示入口：`/demo/turing` · 源码：[`frontend/src/utils/turing.js`](./frontend/src/utils/turing.js)

---

## 🚀 功能特性

### 👤 用户体系
- 注册 / 登录（密码 · 邮箱验证码 · **GitHub SSO**）/ 忘记密码
- **两步验证 2FA（TOTP）**：启用 / 停用（二次认证）/ 登录强制校验
- JWT 双 Token：access 15min + refresh 30 天，**轮换 + 登出吊销 + 设备指纹硬校验**（UA 变化即吊销全部会话）
- 个人资料（昵称 / 简介 / 头像上传，PIL 校验重编码）· 修改密码（吊销全部设备）
- 登录设备管理 · 登录日志（方式 + 2FA + **IP 属地**）
- **账号注销**（密码确认；私信删除、群消息匿名化、群主转让、资料清除）
- **聊天记录导出**（数据携带权）· 用户协议 / 隐私政策（含即时通讯条款、水印溯源声明）
- RBAC：`user` / `admin` / `super_admin`

### 🤖 AI 服务
- 聊天对话（**SSE 流式输出** / 打字机效果）
- **深度思考（reasoning）** 开关，思考过程可折叠
- **Markdown + LaTeX(KaTeX) + 代码高亮**（DOMPurify 消毒）
- 对话历史 / 多会话管理 / 模型切换 / 用量统计（每日额度）
- 每用户并发流上限（防单用户占满后端）

### 💬 站内消息系统（IM）
- **私信**：1v1 实时（WebSocket 房间推送）、已读回执、2 分钟撤回、删除会话（仅隐藏本人）、图片（≤5MB）、拉黑（双向禁止）、举报
- **群聊**：建群 / 邀请 / 踢人 / 退群 / 转让群主 / 解散、成员角色（owner/admin/member）、群公告、实时广播、撤回、举报、未读聚合
- **公告机器人「Harness 官方」**：全量广播 / 定向私信 / 举报处理结果自动告知（全程审计）
- **双层水印**：可见水印 + 零宽字符文本水印（复制可溯源）
- **水印取证**：文本解码工具（superadmin / 授权用户，一次性 / 按次 / 长期额度）
- **举报审核闭环**：Admin 审核（删除消息 / 封禁 / 忽略 + 机器人告知）

### 📋 留言板
- 匿名留言 + 图形验证码 + IP 限流
- **档案号**（`GB-日期-序号`）可追踪
- **多轮回复**：管理员回复 / 访客追问时间线、状态流转（待回复→已回复→关闭）、邮件通知、快捷回复模板
- Admin：档案号列、状态筛选、关键词搜索、往来时间线、处理面板

### 🔧 维护模式（企业级）
- **四种模式**：全站维护 / 仅拦截新访客（已登录放行）/ 定时维护 / 仅管理员
- 503 + `Retry-After` + 防缓存；公开接口与登录链路放行，**管理员完全豁免**
- **三级自动恢复**：倒计时自动关闭 → 超时兜底（默认 120 分钟）→ 服务器重启遗留检测
- **定时维护**：每天 / 每周指定日自动开启，时长后自动恢复
- **紧急逃生通道**：64 位紧急令牌（SHA-256 存储，`?__emergency=` 绕过）
- 通知：站内机器人私信 / 邮件 / 钉钉 / Telegram Webhook；全操作审计
- **部署自动联动**：构建期间自动开维护，完成后自动关闭

### 🛠️ Admin 运营中心（`/admin`，深色主题）
- 仪表盘（用户 / AI 调用统计）· 用户管理（搜索 / 禁用 / 改角色 + 二次密码验证）
- 权限管理 · AI 配置（Key 走环境变量）· 用量统计
- 系统监控（CPU / RAM / Disk / 网络实时 / 温度，宿主真实数据）
- 日志审计 · 安全中心（登录记录 + 属地）· 访问记录 · 公告管理（横幅 + 机器人广播）
- **举报审核** · **敏感词库管理** · **水印取证与授权** · **日志导出** · **维护模式管理**

### 🔒 安全基线
- JWT 密钥 fail-fast（<32 字符拒绝启动）· 生产关闭 API 文档（`/docs` 精确 404）
- 登录 / 注册 / 验证码 **IP 限流**（5 次 / 60s，可信 IP 由 nginx `X-Real-IP` 覆盖客户端伪造）
- 邮箱失败锁定（5 次 / 15 分钟，轮换 IP 无效）+ 登录时序侧信道防护（等时 dummy hash）
- 账号枚举统一提示（注册 / 登录码 / 重置）
- 上传 PIL 内容校验（伪造头 / HTML → 400）并统一转 PNG
- 敏感词过滤（私信 / 群聊发送拦截，词库可管理）
- 改角色 / 重置密码需操作人二次密码验证；WS 每用户连接上限；AI 流式并发限制
- Nginx：`server_tokens off` / CSP（`base-uri`·`frame-ancestors`·`form-action`·`upgrade-insecure-requests`）/ Permissions-Policy / X-Frame-Options / HSTS
- 全站 ORM 无原生 SQL；XSS 双保险（模板转义 + DOMPurify）；CORS 白名单 + Bearer 鉴权

---

## 🧱 技术栈

| 层 | 技术 |
|---|---|
| Frontend | Vue 3 · Vite · Vue Router · Pinia · Axios · marked + KaTeX + DOMPurify · WebGL2 |
| Backend | FastAPI · SQLAlchemy(async) · Pydantic v2 · PyJWT · Alembic · Uvicorn |
| Database | PostgreSQL 16（数据卷持久化） |
| Auth | JWT 双 Token · bcrypt · RBAC · 邮箱验证码 · TOTP 2FA · GitHub SSO |
| Realtime | WebSocket（IoT 遥测 / IM 房间广播）· MQTT（传感器接入） |
| Ops | Docker Compose · Nginx（HTTPS + 安全头）· Let's Encrypt · 维护模式联动 |
| UI | CSS Variables 主题系统（Light / Dark / System）· Indigo 设计语言 · Inter 字体 |

---

## 🏗️ 架构

```
                    ┌───────────────────────────────┐
                    │        Browser (Vue 3 SPA)    │
                    └───────────────┬───────────────┘
                        HTTPS / WSS │
                    ┌───────────────▼───────────────┐
                    │  Nginx（frontend 容器）        │
                    │  SPA 静态 + /api 反代 + SSL    │
                    │  安全响应头 + 可信 IP 注入      │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  FastAPI（backend 容器）       │
                    │  JWT/RBAC/2FA/SSO · IM · 维护  │
                    │  中间件 · 限流 · 敏感词 · 导出  │
                    └──────┬─────────────────┬──────┘
                           │                 │
              ┌────────────▼─────┐   ┌───────▼────────┐
              │ PostgreSQL 16    │   │ MQTT Broker    │
              │ 33 张表 · 持久卷  │   │ ← IoT 传感器    │
              └──────────────────┘   └────────────────┘
```

**实时链路**：`/api/v1/im/ws`（私信 / 群聊房间广播）· `/api/v1/iot/ws`（设备遥测推送）

**容器编排**：`harness-db` · `harness-backend` · `harness-frontend` · `harness-mqtt` · `harness-sim`（模拟传感器，持续写入遥测）

---

## 📁 项目结构

```
harness/
├── backend/
│   ├── alembic/                     # 迁移链（容器启动自动 upgrade head）
│   └── app/
│       ├── main.py                  # FastAPI 入口 + 维护循环 + 重启检测
│       ├── middleware.py            # 维护拦截（四模式/紧急令牌）+ 访问日志
│       ├── models.py                # 33 张表
│       ├── security.py / deps.py    # JWT / bcrypt / 密码策略 / 角色 / 鉴权依赖
│       ├── routers/                 # auth user security ai admin admin_export
│       │                            # admin_im admin_maintenance guestbook
│       │                            # im im_groups iot oauth system
│       └── services/                # audit bot captcha cleanup emailcode exporter
│                                    # geo httputil iot_mqtt loginlog login_alert
│                                    # mailer maintenance moderation monitor
│                                    # notify ratelimit settings visitlog
│                                    # watermark ws_manager
├── frontend/
│   └── src/
│       ├── api/                     # Axios 客户端（401 竞态处理）
│       ├── components/              # SiteNav（私信/公告角标）BrandLogo CountUp ThemeSwitcher
│       ├── layouts/                 # AuthLayout / AdminLayout
│       ├── utils/                   # markdown · session · watermark（零宽水印）· turing
│       ├── views/                   # 19 前台页 + admin/ 16 页 + demo/TuringDemoView
│       └── router/                  # 路由 + 维护模式守卫（登录链路豁免）
├── docs/                            # api.md · architecture.md · database.md · deployment.md
├── scripts/                         # backup.sh · deploy-cloud.sh · migrate-hdd.sh
├── db/init/                         # 数据库初始化
├── docker-compose.yml               # 开发（8080）
├── docker-compose.prod.yml          # 生产（80/443 + 证书挂载）
├── deploy-r3.sh                     # 云端部署（维护模式自动联动）
└── farewell/index.html              # 下线告别页（部署为官网首页）
```

---

## ⚡ 快速开始

```bash
# 1) 环境变量
cp .env.example .env
#    必填：POSTGRES_PASSWORD / JWT_SECRET（≥32 字符随机值）
#    可选：AI_API_KEY / SMTP_* / GITHUB_OAUTH_*

# 2) 启动（开发，8080 端口）
docker compose up -d --build
```

**生产部署**
```bash
cp docker-compose.prod.yml docker-compose.yml   # 80/443 + 证书挂载
cp .env.prod.example .env                       # 生产变量
docker compose up -d --build                    # 部署脚本会自动开/关维护模式
```

详见 [DEPLOY.md](./DEPLOY.md) 与 [docs/deployment.md](./docs/deployment.md)。

---

## 🔌 API 概览

统一前缀 `/api/v1`（生产不开放 `/docs`）。完整列表见 [docs/api.md](./docs/api.md)。

| 模块 | 代表端点 | 说明 |
|---|---|---|
| auth | `/auth/register·login·login-code·send-code·refresh·logout` | 注册 / 登录 / 验证码 / 刷新 / 登出 |
| auth | `/auth/reset-password` · `/auth/totp/*` | 重置密码 / 2FA 管理 |
| oauth | `/auth/oauth/github/authorize·callback` | GitHub SSO |
| user | `/user/profile` · `/user/avatar·deactivate` | 资料 / 头像 / 注销 |
| user | `/user/sessions·login-logs` · `/user/conversations/{id}/export` | 设备 / 日志 / 聊天导出 |
| ai | `POST /ai/chat`（stream、reasoning）· `/ai/history` | AI 对话 / 历史 |
| im | `/im/conversations` · `/im/messages` · `/im/read` · `/im/recall` | 私信全套 |
| im | `/im/groups` · `/im/groups/{id}/*` | 群聊全套 |
| im | `/im/blocks` · `/im/messages/{id}/report` · `POST /im/decode-text` | 拉黑 / 举报 / 水印取证 |
| im | `WS /im/ws` | 私信 / 群聊实时推送 |
| guestbook | `POST /messages` · `POST /query` · `POST /query/reply` | 留言 / 查询 / 追问 |
| iot | `/iot/devices` · `WS /iot/ws` | 设备管理 / 遥测推送 |
| system | `/public/maintenance·notices·stats` · `POST /system/visit` | 公开信息 / 访问上报 |
| admin | `/admin/users` · `/admin/stats·usage·system/status·visits` | 用户 / 统计 / 监控 |
| admin | `/admin/audit-logs·login-logs` · `/admin/settings` | 审计 / 系统配置 |
| admin | `/admin/im/broadcast·reports·sensitive-words` | 机器人 / 举报 / 敏感词 |
| admin | `/admin/maintenance/*` · `POST /admin/exports/*` | 维护模式 / 日志导出 |

---

## 💾 备份与恢复（2026-09）

服务下线前做了**全量备份 + 还原实测**：

| 归档 | 内容 |
|---|---|
| `harness-essential-*.tar.gz`（200MB） | 数据库 dump（Fc + plain SQL）· 配置 · 代码（含 .git）· 证书 · pgdata · 元信息 |
| `harness-pgdata-*.tar.gz`（113MB） | PostgreSQL 原始数据目录快照 |
| `harness-final-*.tar.gz`（91MB） | 最新增量快照（数据库 + uploads） |

**验证方式**：在云端临时库 `harness_verify` 上用备份 dump 实际还原，逐表比对行数——`users` / `dm_messages` / `audit_logs` / `sensitive_words` / `maintenance_config` 等 15 张表**完全一致**；差异仅出现在打包后仍在写入的 `device_telemetry` / `refresh_tokens`（正常增量）；还原后 alembic 版本 `a6b7c8d9e0f1` 与线上一致。

**恢复要点**
```bash
# 数据库（自定义格式，推荐）
docker cp harness-Fc.dump restored-db:/tmp/d.dump
docker exec restored-db pg_restore -U harness -d harness --clean --if-exists /tmp/d.dump
# 或纯 SQL
gunzip -c harness-plain.sql.gz | docker exec -i restored-db psql -U harness -d harness
```

---

## 🗺️ Roadmap

```
v0.1 – v0.8   基础平台 · 用户中心 · AI 模块 · Admin 后台 · 备份体系            ✅
v0.9          邮箱验证码 · 2FA · GitHub SSO · IoT 真实接入 · 访问记录          ✅
v0.10.x       站内消息（私信/群聊/机器人/水印取证）· 留言板升级                 ✅
v0.10.x       合规化（协议/隐私/注销/导出/敏感词/保留期）· 企业级日志导出        ✅
v0.10.x       企业级维护模式（四模式/自动恢复/紧急令牌/通知）                    ✅
v0.10.x       安全加固基线（限流/可信 IP/设备绑定/上传校验/安全头）              ✅
v0.10.1       图灵斑图 Demo（WebGL2 反应扩散 · 7 种动物纹路）                   ✅
—— 2026.09 —— 服务下线 · 全量备份 · 官网转告别页                               ✅
v1.0（未实现） 像素级暗水印 + 截图识别 · 存储加密（AES-GCM）                    ⏸
v1.x（未实现） Android App · 商业化 · 支付                                     ⏸
```

---

## 📄 License

Private / 个人项目 —— 代码仅供学习与参考，未授权商业使用。

---

<div align="center">

**Project Harness** · 2026

*连接 AI、设备与数字体验 · 感谢每一次点击*

</div>
