# Project Harness - 个人智能服务平台

Phase 1: 基础平台（v0.1 → v0.5）
运行环境: X230 Ubuntu + Docker + ZeroTier 内网

## 结构

```
harness/
├── docker-compose.yml    # 编排: db + backend + frontend
├── backend/              # FastAPI 后端
├── frontend/             # Vue 3 前端 (Vite)
└── db/                   # 数据库初始化脚本
```

## 快速启动

```bash
docker compose up -d --build
```

- 前端: http://<host>:8080
- 后端 API: http://<host>:8000
- API 文档: http://<host>:8000/docs

## 版本规划

- v0.1 基础网站
- v0.5 用户系统（注册/登录/UID）
- v1.0 AI 平台
