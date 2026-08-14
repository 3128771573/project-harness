# Project Harness · AI 接盘提示词（Handoff Document）

> 你是 Project Harness 项目的新接任 AI 助手。以下信息确保你能**无缝继续**所有工作：SSH 连接、代码状态、部署架构、待办事项全部可用。

---

## 一、项目一句话定位

**Project Harness** 是一个长期迭代的个人智能服务平台：AI 对话 + IoT 扩展 + 用户系统 + Admin 运营后台，技术栈 Vue 3 + FastAPI + PostgreSQL，当前已部署到国内云服务器（HTTPS + 域名）。

---

## 二、环境拓扑（三台机器）

```
[Windows 本机]  ←SSH(askpass)→  [X230 Ubuntu 10.166.245.50]  ←SSH(密钥)→  [云服务器 124.222.140.57]
   工作区 D:\ds harness         x230user                        ubuntu       生产环境 + HTTPS + 域名
```

### 连接信息（关键！）

| 目标 | 地址 | 用户 | 认证 | 说明 |
|------|------|------|------|------|
| X230 | 10.166.245.50:22 | x230user | 密码 `3128771573` | 开发/中继机 |
| 云服务器 | 124.222.140.57:22 | ubuntu | 密码 `19825626980Zz`（或 X230 密钥） | 生产机 |
| GitHub | 3128771573/project-harness | SSH 密钥 | X230 上 `~/.ssh/id_ed25519_github` | 代码仓库 |

### SSH 连接规范（本机 Windows 必须用 askpass 机制）

```powershell
# 连 X230（askpass.exe 输出 X230 密码）
$env:SSH_ASKPASS = "D:\ds harness\askpass.exe"
$env:SSH_ASKPASS_REQUIRE = "force"
ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password -o StrictHostKeyChecking=accept-new x230user@10.166.245.50 "命令"

# 从 X230 连云服务器（密钥，绝对路径）
ssh -i /home/x230user/.ssh/id_ed25519_cloud -o StrictHostKeyChecking=accept-new ubuntu@124.222.140.57 "命令"

# 连 GitHub（X230 上）
ssh -i /home/x230user/.ssh/id_ed25519_github -T git@github.com
```

**⚠️ 重要经验（避免踩坑）**：
1. **本机无法直连云服务器**（网络路由不通），所有云端操作必须经 X230 中转
2. **PowerShell 引号转义是最大坑**：含 `|`、`$(...)`、`&&`、引号嵌套的命令会被 PowerShell 解析破坏。**正确做法**：本地用 write 工具写好 .sh 脚本 → `scp` 到 X230 `/tmp/` → `ssh x230user@... "bash /tmp/xxx.sh"` 执行。脚本内再嵌套 ssh 到云服务器时同样用脚本文件模式，或单行绝对路径密钥。
3. 云服务器上 `sudo` 免密可用（ubuntu 用户），但嵌套 ssh 时加 `sudo -n` 更稳
4. X230 的 `~/.ssh/config` 只有 GitHub 条目，勿动

---

## 三、代码与版本状态

- **GitHub 仓库**：`github.com/3128771573/project-harness`（main 分支）
- **最新提交**：`08366e6`（v0.10.1，友好错误提示 + 确认密码）
- **版本 tag**：v0.6-user-ai → v0.7-admin → v0.8-ops → v0.9-security → v0.9.1-landing → v0.9.2-product → v0.9.3-ai → v0.9.4-theme → v0.9.5-ui → v0.10-email-code
- **云服务器代码**：`/app/harness`（git clone，注意：云上 git pull 有时因网络不稳定失败，临时文件同步用 scp + cp）
- **X230 代码**：`~/projects/harness`（也是 git 仓库，本地修改后 commit + push）

### 目录结构（前端）
```
frontend/src/
├── api/client.js        # axios + 401 自动刷新 token
├── assets/              # 样式（main.css / auth.css / dashboard.css / chat.css / admin.css）
├── components/          # BrandLogo / SiteNav / ThemeSwitcher / CountUp
├── layouts/             # AuthLayout / AdminLayout
├── router/index.js      # 路由 + 页面访问上报(节流2s sendBeacon)
├── stores/theme.js      # Pinia 主题（light/dark/system + localStorage）
├── styles/              # theme.css + light.css + dark.css（CSS 变量主题系统）
├── utils/markdown.js    # marked + KaTeX + highlight.js 渲染
└── views/               # Landing/Login/Register/Forgot/Dashboard/Chat/Iot/Demo/Docs/Pricing/Status/Settings
    └── admin/           # Dashboard/Users/Roles/AiConfig/Usage/System/Audit/Security/Visits/Settings
```

### 后端结构
```
backend/app/
├── main.py              # FastAPI 入口 + 校验异常处理器
├── errors.py            # 友好中文错误提示（422 → detail 中文）
├── middleware.py        # 访问日志中间件（记录 API 请求）
├── models.py            # users/roles/permissions/refresh_tokens/ai_history/app_settings/login_logs/audit_logs/password_resets/visit_logs/email_codes
├── schemas.py / security.py / deps.py / config.py
├── routers/             # auth / user / security / ai / admin / system
└── services/            # monitor(系统监控) / settings(动态配置) / loginlog / audit / visitlog / mailer / emailcode
```

---

## 四、云服务器部署细节（生产环境）

```
域名: www.platformharness.ltd + platformharness.ltd → 124.222.140.57
HTTPS: Let's Encrypt（certbot webroot，证书 /etc/letsencrypt/live/www.platformharness.ltd/）
```

- 部署目录：`/app/harness`，**docker-compose.yml = docker-compose.prod.yml**（80/443 端口）
- 数据卷：`/data/harness/pgdata`（PostgreSQL）、`/data/harness/uploads`
- 容器：harness-db / harness-backend / harness-frontend（Nginx 含 SSL + /api 反代 + /uploads）
- `.env` 在 `/app/harness/.env`（含 POSTGRES_PASSWORD、JWT_SECRET、CORS_ORIGINS=https://www.platformharness.ltd 等，**SMTP 未配置**）
- Docker 镜像加速：`/etc/docker/daemon.json` 配了 1panel/rat.dev；pip 用阿里源（backend/Dockerfile 内）；npm 用 npmmirror（frontend/Dockerfile 内）
- 防火墙：ufw 放行 22/80/443

### 常用运维命令（经 X230 中转）
```bash
# 查看容器
ssh -i /home/x230user/.ssh/id_ed25519_cloud ubuntu@124.222.140.57 'sudo docker ps --format "{{.Names}} {{.Status}}"'
# 后端日志
ssh -i /home/x230user/.ssh/id_ed25519_cloud ubuntu@124.222.140.57 'sudo docker logs harness-backend --tail 30'
# 重建（代码同步后）
ssh -i /home/x230user/.ssh/id_ed25519_cloud ubuntu@124.222.140.57 'cd /app/harness && sudo docker compose up -d --build'
# 健康检查
curl -sk https://www.platformharness.ltd/api/v1/health
```

---

## 五、已完成功能清单

| 版本 | 功能 |
|------|------|
| v0.6 | 用户系统：注册/登录/JWT 双 token/RBAC(user/admin/super_admin)/资料/头像 |
| v0.7 | Admin 后台：用户管理/禁用/改角色(super_admin 保护)/统计/系统监控/审计日志/pytest+CI/docs |
| v0.8 | /hdd 备份体系(backup.sh)/数据卷迁移/AI 配置管理/用量统计/token 管理 |
| v0.9 | 首页 Landing/用户安全(改密/忘记密码/登录日志/会话管理)/Admin 运营中心(权限/审计/安全/设置) |
| v0.9.x | 主题系统(light/dark/system)/AI 流式输出+深度思考+Markdown/LaTeX 渲染/Indigo UI 重构/Inter 字体 |
| v0.10 | 邮箱验证码(注册强制/验证码登录/验证码重置)——**SMTP 未配置，当前开发模式页面直接显示验证码** |
| v0.10.1 | 友好中文错误提示 + 注册页确认密码 |

### 关键账号
- 云端 superadmin：`superadmin@platformharness.ltd` / `SuAdmin@2026Cloud`（**建议提醒用户改密码**）
- 云端已有普通测试用户若干（验证码测试产生的）

---

## 六、当前待办 / 下一步建议（按优先级）

1. **配置 SMTP 邮件发送**（用户正在准备 QQ 邮箱授权码）：
   - 在云 `/app/harness/.env` 加 `SMTP_HOST=smtp.qq.com / SMTP_PORT=465 / SMTP_USER / SMTP_PASSWORD(16位授权码) / SMTP_FROM`
   - 重启 backend，测试真实发信（注册页获取验证码 → 邮箱收到）
2. **验证证书自动续期**：`sudo certbot renew --dry-run`（之前超时未完成确认；certbot 已装 cron）
3. **SSH 安全加固**（未做）：云服务器禁用密码登录只留密钥、fail2ban 已装未配
4. **superadmin 改密码提醒**（发给用户）
5. **v1.0 IoT Demo**（项目规划下一阶段：MQTT + 传感器模拟 + 实时仪表盘）
6. 页面访问上报在未登录时 sendBeacon 不带 token，属于正常设计（后端可选用户）

---

## 七、给接手 AI 的纪律提醒

1. **所有云服务器操作经 X230 中转**，脚本文件模式（write → scp → bash）避免引号坑
2. **修改前端后**：本地 → scp 到 X230 仓库 → git commit+push → scp 到云 `/app/harness` 对应路径 → `docker compose up -d --build`（前端要 rebuild，后端改了代码也要 rebuild）
3. **数据库结构变更**：create_all 只建新表不加列，需要手动 ALTER（参考 v0.9 迁移经验）；改表前先 `bash scripts/backup.sh` 备份到 /hdd
4. **测试账号密码**：superadmin 密码勿在公共日志明文输出
5. GitHub push 偶尔网络失败 → 重试或改用 scp 同步文件
6. 沙箱限制：本机 ssh 读工作区外文件受限（.ssh 密钥），X230 上的密钥用绝对路径
