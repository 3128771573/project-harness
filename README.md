# Harness Platform

> 个人智能服务平台 · Personal AI Service Platform
>
> 连接 AI、IoT 与数字服务 · Connect AI, Devices and Digital Experiences.

一个可长期迭代的全栈智能服务平台：用户体系 → AI 服务 → 站内消息 → Admin 运营中心 → IoT 扩展 → 合规与安全加固。从内网 Demo 到云端 HTTPS 正式部署，持续演进中。

**线上地址：https://www.platformharness.ltd**

## Tech Stack

| 层 | 技术 |
|----|------|
| Frontend | Vue 3 · Vite · Vue Router · Axios · marked + KaTeX + DOMPurify |
| Backend | FastAPI · SQLAlchemy (async) · Pydantic v2 · PyJWT · Alembic |
| Database | PostgreSQL 16 |
| Auth | JWT 双 Token（access 15min + refresh 30天 轮换吊销 + **设备指纹绑定**）· bcrypt · RBAC · 邮箱验证码 · **TOTP 2FA** · **GitHub SSO** |
| Realtime | WebSocket（IoT 遥测 / IM 私信·群聊 房间广播）· MQTT（传感器接入） |
| Security | IP 限流（可信 IP 提取）· 邮箱失败锁定 · 敏感词过滤 · 上传 PIL 内容校验 · 紧急令牌 · 安全响应头 |
| UI | CSS Variables 主题系统（Light / Dark / System）· Indigo 设计语言 · Inter 字体 |
| Deploy | Docker Compose · Nginx（HTTPS + 安全头）· Let's Encrypt · **维护模式自动联动** |

## Features

### 👤 用户体系
- ✅ 注册 / 登录（密码 + 邮箱验证码 + **GitHub SSO**）/ 忘记密码
- ✅ **两步验证 2FA（TOTP）**：启用 / 停用（二次认证）/ 登录强制校验
- ✅ JWT 双 Token：refresh **轮换 + 登出吊销 + 设备指纹硬校验**（UA 变更即吊销全部会话）
- ✅ 邮箱验证码（SMTP 可配置，开发模式回显 dev_code）/ 密码策略校验
- ✅ 个人资料（昵称 / 简介 / **头像上传（PIL 校验重编码）**）
- ✅ 修改密码（吊销全部设备）/ 登录设备管理 / 登录日志（**方式 + 2FA + IP 属地**）
- ✅ **账号注销**（密码确认；私信删除、群消息匿名化、群主转让、资料清除）
- ✅ **聊天记录导出**（数据携带权）/ 用户协议 + 隐私政策（含即时通讯条款、水印溯源声明）
- ✅ RBAC 权限：`user` / `admin` / `super_admin`

### 🤖 AI 服务
- ✅ 聊天对话（**SSE 流式输出** / 打字机效果，每用户并发槽位限制）
- ✅ **深度思考（reasoning）**可开关，思考过程折叠展示
- ✅ **Markdown + LaTeX（KaTeX）+ 代码高亮**渲染（DOMPurify 消毒）
- ✅ 对话历史 / 多会话管理 / 模型切换 / 用量统计（每用户每日额度）

### 💬 站内消息系统（IM）
- ✅ **私信**：1v1 实时（WebSocket 房间推送）、已读回执、2 分钟撤回、删除会话（仅隐藏本人）、图片（≤5MB）、拉黑（双向禁止）、举报
- ✅ **群聊**：建群/邀请/踢人/退群/转让群主/解散、成员角色（owner/admin/member）、群公告、群消息实时广播、撤回、举报、未读聚合
- ✅ **公告机器人「Harness 官方」**：全量广播 / 定向私信 / 举报处理结果自动告知（审计留痕）
- ✅ **双层水印**：可见水印（昵称+UID+时间）+ 零宽字符文本水印（复制可溯源）
- ✅ **水印取证**：文本解码工具（superadmin / 授权用户，一次性/按次/长期额度，审计）
- ✅ **举报审核闭环**：Admin 审核页（删除消息/封禁/忽略 + 机器人告知）

### 📋 留言板
- ✅ 匿名留言 + 图形验证码 + IP 限流
- ✅ **档案号**（GB-日期-序号）追踪
- ✅ **多轮回复系统**：管理员回复 / 访客追问时间线、状态流转（待回复→已回复→关闭）、邮件通知、快捷回复模板
- ✅ Admin 管理：档案号列、状态筛选、关键词搜索、往来时间线、处理面板

### 🔧 维护模式（企业级）
- ✅ **四种模式**：全站维护 / 仅拦截新访客（已登录放行）/ 定时维护 / 仅管理员
- ✅ 503 + Retry-After + 防缓存；公开接口与登录链路放行，**管理员完全豁免**
- ✅ **自动恢复三级保险**：倒计时自动关闭 → 超时兜底（默认 120 分钟）→ 服务器重启遗留检测
- ✅ **定时维护**（每天/每周指定日自动开启，时长后自动恢复）
- ✅ **紧急逃生通道**：64 位紧急令牌（SHA-256 存储，`?__emergency=` 绕过，紧急关闭链接）
- ✅ 通知：站内机器人私信 / 邮件 / 钉钉 / Telegram Webhook；全操作审计
- ✅ **部署自动联动**：deploy 脚本构建期间自动开维护、完成后自动关闭
- ✅ 维护页：模式化图标 / 原因 / 实时倒计时 / 管理员登录入口

### 🛠️ Admin 运营中心（`/admin`，深色主题）
- ✅ 仪表盘（用户/AI 调用统计）/ 用户管理（搜索/禁用/改角色 + 二次密码验证）
- ✅ 权限管理 / AI 配置（**Key 环境变量管理**）/ 用量统计
- ✅ 系统监控（CPU/RAM/Disk/网络实时/温度，宿主真实数据）
- ✅ 日志审计 / 安全中心（登录记录+属地）/ 访问记录 / 公告管理（横幅 + 机器人广播）
- ✅ **举报审核** / **敏感词库管理** / **水印取证与授权** / **日志导出**（六数据源 CSV/JSON + SHA-256）/ **维护模式管理**

### 📈 运维与部署
- ✅ 云服务器 + 域名 + HTTPS（Let's Encrypt 自动续期）+ 全站 WSS
- ✅ **企业级日志导出**：审计/登录/访问/取证/举报/机器人六源，时间范围+筛选+行数预览，CSV(UTF-8 BOM)/JSON，SHA-256 完整性，导出行为审计
- ✅ /hdd 版本备份体系（代码 + 数据库快照）
- ✅ 访问日志中间件 + 页面访问上报 + IP 属地解析
- ✅ Alembic 迁移链（容器启动自动升级）

### 🔒 安全基线（渗透前防御）
- ✅ JWT 密钥 fail-fast（<32 字符拒绝启动）+ 生产关闭 API 文档
- ✅ 登录/注册/验证码 **IP 限流**（可信 IP：nginx X-Real-IP 覆盖客户端伪造）
- ✅ 邮箱失败锁定（5 次/15 分钟，轮换 IP 无效）+ 登录时序侧信道防护
- ✅ 账号枚举统一（注册/登录码/重置通用提示）
- ✅ 上传 PIL 内容校验（伪造头/HTML → 400）+ 统一转 PNG
- ✅ 敏感词过滤（私信/群聊发送拦截，词库可管理）
- ✅ 改角色/重置密码操作人二次密码验证；WS 每用户连接上限；AI 流式并发限制
- ✅ nginx：server_tokens off / client_max_body_size / CSP(含 base-uri·frame-ancestors·form-action·upgrade-insecure-requests) / Permissions-Policy / X-Frame-Options / HSTS
- ✅ 全站 ORM 无原生 SQL；XSS 双保险（模板转义 + DOMPurify）；CORS 白名单 + Bearer 鉴权

## Architecture

```
Client (Web)
    ↓ HTTPS/WSS
Nginx (SPA + API 反代 + SSL + 安全头 + 可信 IP 注入)
    ↓
FastAPI Backend (JWT / RBAC / 2FA / SSO / IM / 维护中间件 / 限流)
    ↓                                  ↓
PostgreSQL 16（数据卷持久化）      MQTT Broker ← IoT 传感器
```

```
Vue 3 → FastAPI → PostgreSQL → MQTT → Devices（IoT 扩展链路）
WebSocket：/api/v1/iot/ws（遥测推送）· /api/v1/im/ws（私信/群聊房间）
```

## Quick Start

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env: POSTGRES_PASSWORD / JWT_SECRET（≥32 字符随机值）/ AI_API_KEY(可选) / SMTP(可选)

# 2. 启动（开发环境 8080 端口）
docker compose up -d --build
```

生产部署（云服务器）：
```bash
cp docker-compose.prod.yml docker-compose.yml   # 80/443 端口 + 证书挂载
cp .env.prod.example .env                        # 生产环境变量
docker compose up -d --build
# 部署脚本自动进入维护模式（构建重启期间），完成后自动恢复
```

## API Overview

统一前缀 `/api/v1`（生产环境不开放 /docs）：

| 模块 | 端点 | 说明 |
|------|------|------|
| auth | `POST /auth/register` · `login` · `login-code` · `send-code` | 注册 / 密码登录 / 验证码登录 / 发码（IP 限流） |
| auth | `POST /auth/refresh` · `logout` | Token 刷新（轮换+设备校验）/ 登出吊销 |
| auth | `POST /auth/reset-password` · `POST /auth/totp/*` | 重置密码 / 2FA 管理 |
| oauth | `GET /auth/oauth/github/authorize` · `callback` · `exchange` | GitHub SSO |
| user | `GET/PUT /user/profile` · `POST /user/avatar` · `PUT /user/password` | 资料 / 头像 / 密码 |
| user | `GET /user/sessions` · `DELETE` | 设备管理 |
| user | `GET /user/login-logs` · `GET /user/conversations/{id}/export` | 登录日志 / 聊天导出 |
| user | `POST /user/deactivate` | 账号注销（密码确认） |
| ai | `POST /ai/chat`（stream/reasoning）· `GET /ai/history` | AI 对话 / 历史 |
| im | `POST/GET /im/conversations` · `/messages` · `/read` · `/recall` | 私信全套 |
| im | `POST/GET /im/groups` · `/groups/{id}/*` | 群聊全套 |
| im | `POST /im/blocks` · `/messages/{id}/report` · `POST /im/decode-text` | 拉黑 / 举报 / 水印取证 |
| im | `WS /im/ws` | 私信/群聊实时推送 |
| guestbook | `POST /messages` · `POST /query` · `POST /query/reply` | 留言 / 查询 / 追问 |
| system | `GET /public/maintenance` · `POST /system/visit` | 维护状态 / 访问上报 |
| admin | `GET /admin/users` · `PATCH .../role`（二次密码）· `reset-password` | 用户管理 |
| admin | `GET /admin/stats` · `usage` · `system/status` · `visits` | 统计 / 监控 |
| admin | `GET/PUT /admin/settings`（维护模式开关）· `/settings/ai` | 系统 / AI 配置 |
| admin | `GET /admin/audit-logs` · `login-logs` | 审计 / 登录日志 |
| admin | `POST/GET /admin/im/broadcast` · `/reports` · `/sensitive-words` | 机器人 / 举报 / 敏感词 |
| admin | `GET/POST /admin/maintenance/*` | 维护模式控制（四模式/定时/紧急令牌） |
| admin | `POST /admin/exports/*` | 企业级日志导出 |

## Project Structure

```
harness/
├── docker-compose.yml / docker-compose.prod.yml   # 开发 / 生产编排
├── .env.example / .env.prod.example               # 环境变量模板
├── backend/
│   ├── alembic/            # 迁移链（容器启动自动 upgrade head）
│   └── app/
│       ├── main.py         # FastAPI 入口 + 维护循环 + 重启检测
│       ├── middleware.py   # 维护模式拦截（四模式/紧急令牌）+ 访问日志
│       ├── models.py       # 30+ 张表（用户/IM/群聊/留言/水印/敏感词/维护配置…）
│       ├── security.py     # JWT / bcrypt / 密码策略 / 角色
│       ├── deps.py         # 鉴权依赖（机器人拒绝）
│       ├── routers/        # auth/user/security/ai/admin/admin_im/im/im_groups/
│       │                   # guestbook/iot/oauth/system/admin_export/admin_maintenance
│       └── services/       # ratelimit/httputil/maintenance/notify/moderation/
│                           # watermark/bot/messaging/exporter/geo/monitor/…
├── frontend/
│   └── src/
│       ├── components/     # SiteNav（私信角标）/ BrandLogo / ThemeSwitcher
│       ├── layouts/        # AuthLayout / AdminLayout
│       ├── utils/          # watermark（零宽水印）/ session（登出吊销）/ markdown
│       ├── views/          # 前台 18+ 页面 + admin/ 14+ 页面
│       └── router/         # 路由 + 维护模式守卫（登录链路豁免）
├── scripts/                # backup.sh（/hdd 备份）/ deploy-cloud.sh
├── db/init/                # 数据库初始化
└── deploy-r3.sh            # 云端部署（自动维护模式联动）
```

## Roadmap

```
v0.1-0.8   基础平台 · 用户中心 · AI 模块 · Admin 后台 · /hdd 备份   ✅
v0.9-0.10  邮箱验证码 · 2FA · GitHub SSO · IoT 真实接入 · 访问记录   ✅
v0.10.x    站内消息（私信/群聊/机器人/水印取证）· 留言板升级        ✅
v0.10.x    合规化（协议/隐私/注销/导出/敏感词/保留期）· 日志导出    ✅
v0.10.x    企业级维护模式（四模式/自动恢复/紧急令牌/通知）           ✅
v0.10.x    安全加固基线（限流/可信IP/设备绑定/上传校验/…）          ✅
v1.0       像素级暗水印 + 截图识别 · 存储加密（AES-GCM）            🔜
v1.x       Android App · 商业化 · 支付                             🔜
```

## 部署与运维

- 开发环境：`docker compose up -d --build`（8080 端口）
- 生产环境：云服务器 + Nginx + HTTPS + **部署自动维护模式**，详见 [DEPLOY.md](./DEPLOY.md)
- 版本备份：`bash scripts/backup.sh <版本号>` → /hdd（代码 + 数据库快照 + uploads）
- 完整需求：见 [REQUIREMENTS.md](./REQUIREMENTS.md)
- 安全基线：登录/注册/验证码接口 IP 限流 5 次/60s；邮箱失败 5 次/15 分钟锁定；生产关闭 API 文档；JWT 密钥 ≥32 字符（否则拒绝启动）

## License

Private / 个人项目
