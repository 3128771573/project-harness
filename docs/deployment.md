# 部署文档

> Project Harness v0.7 · X230 Ubuntu + Docker

## 1. 前置要求

- Ubuntu + Docker Engine + Docker Compose v2
- Git
- （可选）ZeroTier 内网访问

## 2. 首次部署

```bash
# 克隆代码
git clone git@github.com:3128771573/project-harness.git
cd project-harness

# 配置环境变量
cp .env.example .env
# 编辑 .env: 必填 POSTGRES_PASSWORD / JWT_SECRET；可选 AI_API_KEY

# 启动（首次构建镜像，耗时几分钟）
docker compose up -d --build

# 验证
curl http://localhost:8080/api/v1/health
# {"status":"ok","service":"harness-backend","version":"0.7.0"}
```

## 3. 日常运维

```bash
docker compose ps            # 查看状态
docker compose logs -f backend   # 后端日志
docker compose logs -f frontend  # 前端日志
docker compose up -d --build     # 更新后重建
docker compose down              # 停止（保留数据）
docker compose down -v           # 停止并清空数据卷（慎用！）
```

## 4. 环境变量说明

| 变量 | 必填 | 默认 | 说明 |
|------|------|------|------|
| POSTGRES_PASSWORD | ✅ | - | 数据库密码（强随机） |
| JWT_SECRET | ✅ | - | JWT 签名密钥（openssl rand -hex 32） |
| ACCESS_TOKEN_EXPIRE_MINUTES | | 15 | access token 有效期 |
| REFRESH_TOKEN_EXPIRE_DAYS | | 30 | refresh token 有效期 |
| CORS_ORIGINS | | localhost:8080 | 允许的前端来源（逗号分隔） |
| AI_API_KEY | | 空 | AI 服务密钥（空=mock 模式） |
| AI_BASE_URL | | api.deepseek.com/v1 | OpenAI 兼容接口地址 |
| AI_MODEL | | deepseek-chat | 模型名 |

## 5. 数据备份

```bash
# 备份数据库
docker exec harness-db pg_dump -U harness harness > backup_$(date +%F).sql

# 恢复
cat backup_xxx.sql | docker exec -i harness-db psql -U harness harness

# 用户上传文件（uploads 卷）
docker run --rm -v harness_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads_$(date +%F).tar.gz -C /data .
```

## 6. 更新流程

```bash
git pull                    # 拉取新代码
docker compose up -d --build  # 重建变更的服务
```

## 7. 迁移云服务器（未来）

1. 安装 Docker，克隆代码，配置 .env
2. 映射端口：`8080:80` 改为 `80:80`（或经 Nginx 反代）
3. 域名 DNS 指向服务器，配置 HTTPS（certbot / Cloudflare）
4. 迁移数据库：pg_dump + psql 导入
5. 迁移 uploads 卷

## 8. CI/CD（GitHub Actions）

`.github/workflows/ci.yml` 已配置：

- 每次 push/PR 自动运行
- 步骤：后端 pytest（含注册/登录/refresh/RBAC/AI 接口测试）→ 前端构建
- 状态徽章可在仓库 README 展示
