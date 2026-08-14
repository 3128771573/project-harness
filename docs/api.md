# API 文档

> 统一前缀: `/api/v1` · 鉴权: `Authorization: Bearer <access_token>`
> 除 auth 注册/登录外，所有接口需要登录；admin 接口需要对应角色。

## 认证 (auth)

### POST /auth/register
注册并返回双 Token。

```json
// 请求
{"username": "alice", "email": "a@x.com", "password": "pass1234"}
// 响应 201
{"access_token": "...", "refresh_token": "...", "token_type": "bearer",
 "user": {"uid": "...", "username": "alice", "email": "a@x.com",
          "role": "user", "created_time": "..."}}
```

### POST /auth/login
```json
// 请求
{"email": "a@x.com", "password": "pass1234"}
// 响应 200 同 register
// 错误: 401 邮箱或密码错误
```

### POST /auth/refresh
刷新令牌（轮换：旧 refresh 立即失效）。

```json
// 请求
{"refresh_token": "..."}
// 响应 200 新 Token 对
// 错误: 401 刷新凭证无效/已失效
```

### POST /auth/logout
吊销 refresh_token。响应 204。

## 用户 (user) — 本人数据

### GET /user/profile
返回当前用户完整资料（含 role）。

### PUT /user/profile
修改昵称/简介/头像URL。

```json
{"nickname": "Alice", "bio": "IoT 开发者"}
```

### POST /user/avatar
multipart 上传头像（jpg/png/webp/gif，≤2MB）→ 响应含 avatar URL `/uploads/avatars/...`。

## AI (ai)

### POST /ai/chat
```json
// 请求
{"question": "你好"}
// 响应 200
{"answer": "...", "model": "mock 或 deepseek-chat"}
```
自动保存到 ai_history。

### GET /ai/history?limit=20&offset=0
```json
{"items": [{"id": "...", "question": "...", "answer": "...", "model": "...", "created_time": "..."}],
 "total": 2}
```

### GET /ai/models
```json
["mock"]  // 或 ["deepseek-chat"]
```

## 管理后台 (admin) — 需 admin / super_admin

### GET /admin/ping
权限自检。返回 `{"message": "管理员访问成功", "uid": "...", "role": "admin"}`

### GET /admin/stats
平台统计：

```json
{"total_users": 100, "today_new_users": 12,
 "total_ai_calls": 356, "today_ai_calls": 15}
```

### GET /admin/users?page=1&page_size=20
用户列表（分页，按注册时间倒序）：

```json
{"items": [{"uid": "...", "username": "alice", "email": "a@x.com",
            "role": "user", "is_active": true, "created_time": "..."}],
 "total": 100, "page": 1, "page_size": 20}
```

### PATCH /admin/users/{uid}/status
禁用/启用用户。

```json
{"is_active": false}
```

### PATCH /admin/users/{uid}/role
修改角色。**super_admin 才能修改 admin 及以上角色的用户**。

```json
{"role": "admin"}
```

### GET /admin/system/status
系统监控（宿主系统指标）：

```json
{"cpu": 32, "memory": 64, "disk": 40, "uptime": "20 days"}
```

## 系统 (system)

### GET /health
```json
{"status": "ok", "service": "harness-backend", "version": "0.7.0"}
```

## 错误格式

```json
{"detail": "错误描述"}
```

| HTTP | 含义 |
|------|------|
| 400 | 请求参数错误 |
| 401 | 未登录 / 凭证无效 |
| 403 | 权限不足（RBAC 拒绝） |
| 404 | 资源不存在 |
| 409 | 冲突（如重复注册） |
| 502 | 上游服务失败（AI 调用等） |
