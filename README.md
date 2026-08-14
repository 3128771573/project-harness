# Harness Platform

> 个人智能服务平台 · Personal AI Service Platform
>
> 连接 AI、IoT 与数字服务 · Connect AI, Devices and Digital Experiences.

一个可长期迭代的全栈智能服务平台：用户体系 → AI 服务 → Admin 运营中心 → IoT 扩展 → 商业化。从内网 Demo 到云端 HTTPS 正式部署，持续演进中。

**线上地址：https://www.platformharness.ltd**

## Tech Stack

| 层 | 技术 |
|----|------|
| Frontend | Vue 3 · Vite · Vue Router · Pinia · Axios · marked + KaTeX |
| Backend | FastAPI · SQLAlchemy (async) · Pydantic v2 · PyJWT |
| Database | PostgreSQL 16 |
| Auth | JWT 双 Token（access 15min + refresh 30天）· bcrypt · RBAC · 邮箱验证码 |
| UI | CSS Variables 主题系统（Light / Dark / System）· Indigo 设计语言 · Inter 字体 |
| Deploy | Docker Compose · Nginx · HTTPS (Let's Encrypt) · GitHub Actions CI |

## Features

### 👤 用户体系
- ✅ 注册 / 登录（密码 + 邮箱验证码双模式）/ 忘记密码
- ✅ JWT 双 Token（access + refresh 轮换吊销）
- ✅ 邮箱验证码：注册强制验证 / 验证码登录 / 验证码重置密码（SMTP 可配置）
- ✅ 个人资料（昵称 / 简介 / 头像上传）
- ✅ 修改密码（吊销全部设备）/ 登录设备管理 / 登录日志
- ✅ RBAC 权限：`user` / `admin` / `super_admin`

### 🤖 AI 服务
- ✅ 聊天对话（**SSE 流式输出** / 打字机效果）
- ✅ **深度思考（reasoning）**可开关，思考过程折叠展示
- ✅ **Markdown + LaTeX（KaTeX）+ 代码高亮**渲染
- ✅ 对话历史 / 模型切换 / 用量统计（每用户）

### 🛠️ Admin 运营中心（`/admin`，深色主题）
- ✅ 仪表盘（用户/AI 调用统计）
- ✅ 用户管理（搜索/禁用/改角色，super_admin 保护）
- ✅ 权限管理 / AI 配置（在线改 key 无需重启）/ 用量统计
- ✅ 系统监控（CPU/RAM/Disk/网络实时/温度，宿主真实数据）
- ✅ 日志审计（操作留痕）/ 安全中心（登录记录）/ 系统设置
- ✅ **访问记录**（访客时间/IP/设备/路径追踪）

### 📈 运维与部署
- ✅ 云服务器 + 域名 + HTTPS（Let's Encrypt 自动续期）
- ✅ /hdd 版本备份体系（代码 + 数据库快照）
- ✅ 全局主题系统（Light / Dark / System，localStorage 持久化）
- ✅ 访问日志中间件 + 页面访问上报

### 🔜 规划中
- IoT 平台（MQTT + 传感器 + 实时仪表盘）
- Demo 实验平台（Pay / Media / 可视化）
- Android / iOS App
- 支付 / 商业化

## Architecture

```
Client (Web / Android / iOS)
        ↓
Nginx (Vue SPA + API 反代 + SSL 443)
        ↓
FastAPI Backend (JWT 鉴权 / RBAC / 邮箱验证码 / 访问日志)
        ↓
PostgreSQL 16（数据卷持久化）
```

```
Vue 3 → FastAPI → PostgreSQL → MQTT → Devices（IoT 扩展链路）
```

## Quick Start

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env: POSTGRES_PASSWORD / JWT_SECRET / AI_API_KEY(可选) / SMTP(可选)

# 2. 启动（开发环境 8080 端口）
docker compose up -d --build
```

生产部署（云服务器）：
```bash
cp docker-compose.prod.yml docker-compose.yml   # 80/443 端口 + 证书挂载
cp .env.prod.example .env                        # 生产环境变量
docker compose up -d --build
```

## API Overview

统一前缀 `/api/v1`：

| 模块 | 端点 | 说明 |
|------|------|------|
| auth | `POST /auth/register` | 注册（验证码 + 双 Token） |
| auth | `POST /auth/login` | 密码登录 |
| auth | `POST /auth/login-code` | 邮箱验证码登录 |
| auth | `POST /auth/send-code` | 发送验证码（register/login/reset） |
| auth | `POST /auth/refresh` / `logout` | Token 刷新（轮换）/ 登出 |
| auth | `POST /auth/reset-password` | 验证码重置密码 |
| user | `GET/PUT /user/profile` | 资料获取 / 修改 |
| user | `POST /user/avatar` | 头像上传 |
| user | `PUT /user/password` | 修改密码（吊销全部设备） |
| user | `GET /user/sessions` · `DELETE /user/sessions` | 设备管理 |
| user | `GET /user/login-logs` | 我的登录记录 |
| ai | `POST /ai/chat` | AI 对话（**支持 stream / reasoning**） |
| ai | `GET /ai/history` · `GET /ai/models` | 历史 / 模型 |
| system | `POST /system/visit` | 页面访问上报 |
| admin | `GET /admin/users` · `PATCH .../status` · `.../role` | 用户管理 |
| admin | `GET /admin/stats` · `GET /admin/usage` | 统计 / 用量 |
| admin | `GET /admin/system/status` | 系统监控（宿主机） |
| admin | `GET /admin/settings/ai` · `PUT ...` | AI 配置管理 |
| admin | `GET /admin/audit-logs` · `GET /admin/login-logs` | 审计 / 登录日志 |
| admin | `GET /admin/visits` | 访客访问记录 |

## Project Structure

```
harness/
├── docker-compose.yml / docker-compose.prod.yml   # 开发 / 生产编排
├── .env.example / .env.prod.example               # 环境变量模板
├── backend/
│   └── app/
│       ├── main.py       # FastAPI 入口 + 友好错误处理器
│       ├── errors.py     # Pydantic 校验 → 中文提示
│       ├── middleware.py # 访问日志中间件
│       ├── models.py     # 12 张表（用户/AI/日志/验证码/访问…）
│       ├── security.py   # JWT / bcrypt / 密码策略
│       ├── routers/      # auth / user / security / ai / admin / system
│       └── services/     # monitor / mailer / emailcode / visitlog…
├── frontend/
│   └── src/
│       ├── components/   # BrandLogo / SiteNav / ThemeSwitcher / CountUp
│       ├── layouts/      # AuthLayout / AdminLayout
│       ├── stores/       # Pinia（主题）
│       ├── styles/       # 主题系统（theme/light/dark.css）
│       ├── utils/        # Markdown/LaTeX 渲染
│       ├── views/        # 14 个页面 + admin/ 9 个页面
│       └── router/       # 路由 + 访问上报
├── scripts/              # backup.sh（/hdd 备份）/ deploy-cloud.sh
├── docs/                 # architecture / database / api / deployment
└── db/init/              # 数据库初始化
```

## Roadmap

```
v0.1-0.6   基础平台 · 用户中心 · AI 模块          ✅
v0.7-0.8   Admin 后台 · /hdd 备份 · 运维增强      ✅
v0.9       首页 · 用户安全 · Admin 运营中心        ✅
v0.9.x     UI 重构 · 主题系统 · AI 流式渲染        ✅
v0.10      邮箱验证码 · 访问记录 · 友好错误提示     ✅
v1.0       IoT Demo（MQTT + 传感器）              🔜
v1.x       Android App · 商业化 · 支付            🔜
```

## 部署与运维

- 开发环境：`docker compose up -d --build`（8080 端口）
- 生产环境：云服务器 + Nginx + HTTPS，详见 [DEPLOY.md](./DEPLOY.md)
- 版本备份：`bash scripts/backup.sh <版本号>` → /hdd（代码 + 数据库快照 + uploads）
- 完整需求：见 [REQUIREMENTS.md](./REQUIREMENTS.md)

## License

Private / 个人项目
