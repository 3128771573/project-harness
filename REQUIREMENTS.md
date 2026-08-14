# Project Harness：个人智能服务平台开发需求

> 长期项目需求说明 —— 可提供给 Codex、Claude Code、Cursor、Copilot 等 AI 编程助手作为项目背景。

## 1. 项目目标

开发一个可长期迭代的个人智能服务平台。

初期运行于：

- Lenovo ThinkPad X230
- Ubuntu Linux
- SSH 远程管理
- ZeroTier 内网访问

后续迁移：

- 云服务器
- 独立域名
- HTTPS
- Cloudflare 防护
- 正式公网部署

目标：从个人 Demo 平台逐步发展为具有 AI 服务、用户系统、数据管理、Demo 展示、IoT 扩展、商业化能力的完整 Web 平台。

## 2. 总体架构要求

采用前后端分离架构：

```
Client (Web / Android / iOS)
        |
        ↓
API Gateway
        |
        ↓
Backend Services
        |
        ↓
Database
```

要求：

- 前端不保存业务逻辑
- 后端负责权限、安全、业务判断
- API 设计可长期扩展
- 支持未来多端接入

## 3. 开发阶段规划

### Phase 1：基础平台

目标：运行在 X230 上。

实现：

#### 用户系统

功能：

- 注册
- 登录
- UID 生成
- 用户资料
- 权限管理

用户模型：

```
User
uid
username
email
password_hash
avatar
nickname
created_time
```

要求：

- 密码不能明文保存
- 使用安全哈希算法
- 后端验证所有权限

## 4. 登录体系设计

初期：邮箱 + 密码

未来扩展：微信登录、Google 登录、Apple 登录、GitHub 登录、Passkey/WebAuthn

设计：不要让登录方式绑定用户。采用：

```
User (UID)
  |
  +---- Email
  +---- Google
  +---- Apple
  +---- Passkey
```

## 5. 权限系统

设计 RBAC (Role Based Access Control)：

- 用户：`user`
- 管理员：`admin`
- 超级管理员：`super_admin`

后台必须：

- 验证身份
- 验证权限
- 禁止依赖前端权限判断

## 6. AI 模块

路径：`/ai`

功能：AI 聊天、历史记录、用户调用统计、模型切换

API：

```
/api/v1/ai/chat
/api/v1/ai/history
/api/v1/ai/models
```

## 7. Demo 实验平台

建立 `/demo`，用于展示各种技术实验。

### Pay Demo

模拟：订单生成、支付流程、支付状态

未来支持：微信支付、支付宝、Apple Pay、Google Pay、PayPal、国际银行卡

注意：初期只做 Demo。

### Media Demo

包括：视频播放、音频播放、在线组件

### IoT Demo

结合智能测控专业，模拟：

```
Sensor
  ↓
API
  ↓
Database
  ↓
Dashboard
```

展示：温度、湿度、状态、数据曲线

## 8. 管理后台

路径：`/admin`，只有授权账号可访问。

功能：

- 系统监控：CPU、RAM、Disk、Network、uptime
- 服务状态：Frontend / Backend / Database / Docker / Nginx（Running / Error）
- 用户管理：UID、注册时间、权限
- 日志：登录记录、API 调用、系统事件

## 9. API 设计规范

统一前缀：`/api/v1/`

模块化：`auth` `user` `ai` `payment` `chat` `iot` `admin`

未来：`/api/v2`，避免破坏旧版本。

## 10. 数据库设计要求

使用：PostgreSQL / MySQL

主要表：

```
users
user_accounts
roles
permissions
sessions
ai_history
orders
payments
devices
logs
```

要求：数据结构可扩展，支持未来商业化。

## 11. 聊天系统

未来支持用户私聊（User A → Encrypted Message → User B）：

- 私聊加密设计
- 消息历史
- 在线状态

同时支持客服系统：`support.example.com`，为主站提供客服入口。

## 12. 前端要求

目标：简洁、美观、不复杂。设计类似 SaaS 平台 / Apple 风格 / Dashboard。

要求：组件化（`components` / `pages` / `layouts`），方便未来大改版。

## 13. 多端规划

- 第一阶段：Web（Vue / React）
- 第二阶段：Android App
- 第三阶段：iOS App

要求：所有客户端共享统一 API、统一 UID、统一数据库，保证数据一致。

## 14. 部署要求

开发环境：

```
X230 Ubuntu + Docker + Git + SSH
```

生产环境：

```
Cloud Server + Domain + Cloudflare + Nginx + HTTPS + Docker
```

## 15. 安全要求

必须：

- 后端验证权限
- 密码哈希
- API 鉴权
- 防暴力登录
- 限流
- 日志记录

不能：

- 信任前端数据
- 前端保存敏感信息
- 明文保存密码

## 16. 开发原则

1. 先实现，再优化
2. 模块化设计
3. API 优先
4. 保持可迁移
5. 小版本持续迭代

版本规划：

```
v0.1  基础网站
v0.5  用户系统
v1.0  AI 平台
v2.0  多功能平台
v3.0  云端正式部署
```

## 当前第一步任务

不要开发全部功能。首先完成：

```
X230 Ubuntu
  ↓
Docker 环境
  ↓
Git 项目
  ↓
Vue 前端
  ↓
FastAPI 后端
  ↓
PostgreSQL
  ↓
用户注册登录
  ↓
UID 系统
```

完成后再逐步增加：AI → Demo → 管理后台 → 支付 → App → 云部署。

## 核心思想

> 构建一个可以持续几年迭代的平台，而不是一次性的网页项目。

后面每增加功能，只需要继续补充对应模块，不需要推翻架构。
