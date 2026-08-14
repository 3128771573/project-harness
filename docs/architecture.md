# 系统架构文档

> Project Harness v0.7 · 最后更新: 2026-08

## 1. 总体架构

前后端分离 + 全容器化部署：

```
                        ┌─────────────────────────────┐
                        │      Client (Browser)       │
                        └──────────────┬──────────────┘
                                       │ HTTP (8080)
                        ┌──────────────▼──────────────┐
                        │      Nginx (frontend)       │
                        │  - Vue3 静态资源            │
                        │  - /api/* 反向代理          │
                        │  - /uploads/* 静态文件      │
                        └──────────────┬──────────────┘
                                       │ /api/v1/*
                        ┌──────────────▼──────────────┐
                        │   FastAPI (backend)         │
                        │  - JWT 鉴权 (access)        │
                        │  - RBAC 权限 (角色)          │
                        │  - 业务路由                 │
                        └──────────────┬──────────────┘
                                       │ SQLAlchemy (async)
                        ┌──────────────▼──────────────┐
                        │    PostgreSQL 16 (db)       │
                        │  - 持久化数据卷 pgdata      │
                        └─────────────────────────────┘
```

## 2. 模块划分（后端）

```
backend/app/
├── main.py        # FastAPI 入口 + CORS + 路由注册 + 启动初始化
├── config.py      # 配置（全部来自环境变量 .env）
├── database.py    # async SQLAlchemy engine/session
├── models.py      # ORM 模型（users/roles/permissions/refresh_tokens/ai_history）
├── schemas.py     # Pydantic 请求/响应模型
├── security.py    # 密码哈希(bcrypt) + JWT(access/refresh) + 角色常量
├── deps.py        # 依赖注入: get_current_user / require_roles (RBAC)
└── routers/
    ├── auth.py    # 注册/登录/refresh(轮换)/logout
    ├── user.py    # 资料查询/修改/头像上传
    ├── ai.py      # AI 聊天/历史/模型列表
    └── admin.py   # 管理后台（用户管理/统计/系统监控）
```

## 3. 认证与授权流程

```
登录 → POST /auth/login
  → 校验 bcrypt 密码
  → 签发 access_token (15min) + refresh_token (30d, 入库)
  → 响应双 token

请求受保护接口 → Authorization: Bearer <access_token>
  → deps.get_current_user 解码 JWT + 查库
  → 返回当前用户对象

access 过期 → 前端拦截器自动调 POST /auth/refresh
  → 校验 refresh jti 在库且未吊销
  → 吊销旧 token，签发新 token（轮换）

RBAC 角色 → require_roles("admin", "super_admin")
  → 检查 user.role.name 是否在允许列表
```

## 4. 权限矩阵

| 接口 | user | admin | super_admin |
|------|------|-------|-------------|
| /auth/* | ✅ | ✅ | ✅ |
| /user/* | ✅（本人） | ✅（本人） | ✅（本人） |
| /ai/* | ✅（本人） | ✅（本人） | ✅（本人） |
| /admin/users | ❌ | ✅ | ✅ |
| /admin/users/{uid}/role | ❌ | ⚠️ 仅能改 user | ✅ 可改 admin |
| /admin/stats, /admin/system | ❌ | ✅ | ✅ |

## 5. 部署拓扑

```
X230 (Ubuntu, ZeroTier 10.166.245.50)
├── Docker daemon
│   ├── harness-db       (postgres:16-alpine, 内部 5432)
│   ├── harness-backend  (FastAPI, 内部 8000, expose)
│   └── harness-frontend (Nginx, 宿主 8080 → 80)
├── 卷: pgdata (数据库) / uploads (头像等用户文件)
└── 外部访问: ZeroTier 内网 → 8080
```

## 6. 可扩展性设计

- API 版本前缀 `/api/v1`，未来 `/api/v2` 不破坏旧版
- 登录方式与用户解耦：`users` + 未来 `user_accounts` 表支持第三方登录
- RBAC 用 `roles`/`permissions` 表 + 关联表，可扩展细粒度权限
- AI 模块使用 OpenAI 兼容接口，可替换任何兼容提供商
- 服务全部容器化，可平滑迁移云服务器（改 compose 端口/域名即可）
