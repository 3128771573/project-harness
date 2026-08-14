# Project Harness - 部署与运维手册

## 环境

- X230 Ubuntu + Docker (Compose v2+)
- 前端: Vue 3 (Nginx), 后端: FastAPI (Uvicorn), 数据库: PostgreSQL 16

## 常用命令

```bash
# 启动（首次会构建镜像）
docker compose up -d --build

# 停止
docker compose down

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# 重新构建单个服务
docker compose up -d --build backend

# 完全重置（删除数据库数据卷，慎用）
docker compose down -v
```

## 访问入口

- Web: http://<host>:8080
- 后端健康检查: http://<host>:8080/api/v1/health
- 后端 API 文档: 容器内 http://backend:8000/docs（未对外暴露，可通过 `docker exec` 查看）

## 数据库操作

```bash
# 进入 psql
docker exec -it harness-db psql -U harness -d harness

# 查看用户表
docker exec harness-db psql -U harness -d harness -c "SELECT uid, username, email, created_time FROM users;"
```

## 配置（环境变量）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| POSTGRES_PASSWORD | harness_dev_pw | 数据库密码（上线前必改） |
| JWT_SECRET | change-me-in-prod-please | JWT 签名密钥（上线前必改） |
| JWT_EXPIRE_MINUTES | 1440 | Token 有效期（分钟） |
| CORS_ORIGINS | http://localhost:8080,http://10.166.245.50:8080 | 允许的前端来源 |

生产部署时建议使用 `.env` 文件覆盖默认值。

## 镜像源说明

Docker Hub 官方源在国内不可达时，已在 `/etc/docker/daemon.json` 配置镜像加速器：

```json
{
  "registry-mirrors": [
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ]
}
```

> 注意: 原配置中的 `docker.m.daocloud.io` 已失效（token 403），已移除。修改后需 `systemctl restart docker`。

## Git 流程

```bash
git add -A && git commit -m "描述" && git push   # 配置 remote 后
```

## 开发扩展

- 新 API: `backend/app/routers/` 下新增模块，在 `main.py` 注册
- 新页面: `frontend/src/views/` + `frontend/src/router/index.js`
- 新表: `backend/app/models.py` 定义模型（Phase 1 用 create_all，后续迁移 Alembic）
