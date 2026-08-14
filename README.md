# Harness Platform

> 个人智能服务平台 · Personal AI Service Platform

一个可长期迭代的全栈 Web 平台：用户系统 → AI 服务 → Demo 实验 → 管理后台，逐步演进为完整的产品化平台。

## Tech Stack

| 层 | 技术 |
|----|------|
| Frontend | Vue 3 · Vite · Vue Router · Axios |
| Backend | FastAPI · SQLAlchemy (async) · Pydantic v2 |
| Database | PostgreSQL 16 |
| Auth | JWT (access + refresh) · bcrypt · RBAC |
| Deploy | Docker · Docker Compose · Nginx |

## Features

- ✅ **用户系统** — 注册 / 登录 / JWT 双 Token（access 15min + refresh 30天）/ bcrypt 密码哈希
- ✅ **用户中心** — 个人资料（昵称 / 简介）/ 头像上传
- ✅ **权限系统** — RBAC：`user` / `admin` / `super_admin` 角色
- ✅ **AI 服务** — 聊天对话 / 历史记录 / 模型切换（OpenAI 兼容接口，支持 mock 模式）
- 🔜 Admin 后台 — 系统监控 / 用户管理 / 日志
- 🔜 Demo 实验平台 — Pay / IoT / Media
- 🔜 移动端 — Android / iOS

## Architecture

```
Client (Web / Android / iOS)
        ↓
  Nginx (Frontend + API 反代)
        ↓
  FastAPI Backend (JWT 鉴权 / RBAC)
        ↓
  PostgreSQL
```

完整需求文档见 [REQUIREMENTS.md](./REQUIREMENTS.md)。

## Quick Start

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env: POSTGRES_PASSWORD / JWT_SECRET / AI_API_KEY(可选)

# 2. 启动
docker compose up -d --build
```

访问：`http://<host>:8080`

| 入口 | 地址 |
|------|------|
| Web 前端 | `http://<host>:8080` |
| 健康检查 | `http://<host>:8080/api/v1/health` |

## API Overview

统一前缀 `/api/v1`：

| 模块 | 端点 | 说明 |
|------|------|------|
| auth | `POST /auth/register` | 注册（返回双 Token） |
| auth | `POST /auth/login` | 登录 |
| auth | `POST /auth/refresh` | 刷新 Token（轮换） |
| auth | `POST /auth/logout` | 登出（吊销 refresh） |
| user | `GET /user/profile` | 获取资料 |
| user | `PUT /user/profile` | 修改昵称 / 简介 |
| user | `POST /user/avatar` | 上传头像 |
| ai | `POST /ai/chat` | AI 对话（自动保存历史） |
| ai | `GET /ai/history` | 历史记录（分页） |
| ai | `GET /ai/models` | 可用模型 |
| admin | `GET /admin/ping` | 管理员权限测试（RBAC） |

## Roadmap

```
Phase 1  基础平台          ✅ 完成
Phase 2  用户中心          ✅ 完成（资料 / 双Token / RBAC）
Phase 3  AI 模块           ✅ 完成（聊天 + 历史）
Phase 4  Admin 后台        🔜 规划中
Phase 5  Demo 实验平台     🔜 规划中（Pay / IoT / Media）
Phase 6  Android App       🔜
Phase 7  云服务器部署       🔜
Phase 8  支付 / 商业化      🔜
```

## Project Structure

```
harness/
├── docker-compose.yml
├── .env.example          # 环境变量模板
├── backend/
│   └── app/
│       ├── main.py       # FastAPI 入口
│       ├── config.py     # 配置（环境变量）
│       ├── models.py     # SQLAlchemy 模型
│       ├── schemas.py    # Pydantic 模型
│       ├── security.py   # JWT / bcrypt
│       ├── deps.py       # 鉴权 / RBAC 依赖
│       └── routers/      # auth / user / ai / admin
├── frontend/
│   └── src/
│       ├── views/        # 页面
│       ├── layouts/      # 布局
│       ├── api/          # Axios 客户端（含自动续期）
│       └── assets/       # 样式
└── db/init/              # 数据库初始化
```

## Deployment & Ops

见 [DEPLOY.md](./DEPLOY.md)。

## License

Private / 个人项目
