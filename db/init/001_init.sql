-- Project Harness - PostgreSQL 初始化
-- 数据库/用户由 docker-compose 环境变量创建；此处为后续扩展预留
-- Phase 1 表结构由 SQLAlchemy create_all 自动创建

-- 扩展: UUID 生成 (备用)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 未来 Phase 扩展表 (占位注释，不实际创建)
-- user_accounts (第三方登录账号绑定)
-- roles / permissions (RBAC)
-- sessions
-- ai_history
-- orders / payments
-- devices (IoT)
-- logs
