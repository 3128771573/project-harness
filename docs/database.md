# 数据库设计文档

> Project Harness v0.7 · PostgreSQL 16

## 1. ER 总览

```
users ────────┬──< refresh_tokens
  │           └──< ai_history
  │
  └────> roles ──< role_permissions >── permissions
```

## 2. 表结构

### users（用户）

| 列 | 类型 | 约束 | 说明 |
|----|------|------|------|
| uid | varchar(36) | PK, 默认 uuid4 | 用户唯一 ID |
| username | varchar(32) | UNIQUE, INDEX | 用户名 |
| email | varchar(255) | UNIQUE, INDEX | 邮箱（登录名） |
| password_hash | varchar(128) | NOT NULL | bcrypt 哈希 |
| nickname | varchar(64) | NULL | 昵称 |
| avatar | varchar(512) | NULL | 头像 URL（/uploads/...） |
| bio | text | NULL | 个人简介 |
| role_id | varchar(36) | FK→roles.id | 角色 |
| is_active | boolean | NOT NULL, 默认 true | 是否启用（禁用后无法登录/访问） |
| created_time | timestamptz | NOT NULL, 默认 now() | 注册时间 |

### roles（角色）

| 列 | 类型 | 说明 |
|----|------|------|
| id | varchar(36) PK | 角色 ID |
| name | varchar(32) UNIQUE | user / admin / super_admin |
| description | varchar(255) | 描述 |
| created_time | timestamptz | 创建时间 |

### permissions（权限）

| 列 | 类型 | 说明 |
|----|------|------|
| id | varchar(36) PK | 权限 ID |
| code | varchar(64) UNIQUE | 权限代码（如 user:manage） |
| description | varchar(255) | 描述 |
| created_time | timestamptz | 创建时间 |

### role_permissions（角色-权限关联）

| 列 | 类型 | 说明 |
|----|------|------|
| role_id | varchar(36) PK, FK | 角色 |
| permission_id | varchar(36) PK, FK | 权限 |

### refresh_tokens（刷新令牌）

| 列 | 类型 | 说明 |
|----|------|------|
| id | varchar(36) PK | 记录 ID |
| uid | varchar(36) FK, INDEX | 用户 |
| jti | varchar(64) INDEX, UNIQUE(uid,jti) | 令牌唯一标识 |
| expires_at | timestamptz | 过期时间（30天） |
| revoked | boolean, 默认 false | 是否已吊销（轮换时置 true） |
| created_time | timestamptz | 签发时间 |

### ai_history（AI 对话历史）

| 列 | 类型 | 说明 |
|----|------|------|
| id | varchar(36) PK | 记录 ID |
| uid | varchar(36) FK, INDEX | 用户 |
| question | text | 用户问题 |
| answer | text | AI 回答 |
| model | varchar(64) | 使用的模型（mock 或真实） |
| created_time | timestamptz | 对话时间 |

## 3. 关键索引

```sql
-- users
CREATE UNIQUE INDEX ix_users_username ON users(username);
CREATE UNIQUE INDEX ix_users_email ON users(email);

-- ai_history（按用户查历史）
CREATE INDEX ix_ai_history_uid ON ai_history(uid);

-- refresh_tokens（登录态管理）
CREATE INDEX ix_refresh_tokens_uid ON refresh_tokens(uid);
CREATE UNIQUE INDEX uq_refresh_uid_jti ON refresh_tokens(uid, jti);
```

## 4. 数据初始化

- 角色种子数据在应用启动时自动创建（`seed_roles`）：user / admin / super_admin
- 表结构由 SQLAlchemy `create_all` 自动创建（Phase 1 方案，后续迁移 Alembic）
- `db/init/001_init.sql` 预留扩展（pgcrypto 等）

## 5. 未来扩展

- `user_accounts`：第三方登录账号绑定（Google/Apple/微信/GitHub/Passkey）
- `orders`/`payments`：支付商业化
- `devices`/`device_data`：IoT 设备与遥测数据
- `logs`：操作/审计日志
- `ai_quota`：会员配额（Free 10次/天、VIP 1000次/天）
