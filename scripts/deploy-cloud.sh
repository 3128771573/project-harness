#!/bin/bash
# ============================================
# Project Harness · 云服务器一键部署（ubuntu 用户版）
# 用法: bash deploy-cloud.sh <IP> <user>
# ============================================
set -e
SERVER_IP="${1:?用法: bash deploy-cloud.sh <IP> <user>}"
SERVER_USER="${2:-ubuntu}"
SSH_OPTS="-o StrictHostKeyChecking=accept-new -o ConnectTimeout=20"
S() { ssh $SSH_OPTS "$SERVER_USER@${SERVER_IP}" "$@"; }

echo "========== [1/6] 基础环境 =========="
S 'export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl git ufw fail2ban openssl > /dev/null 2>&1
sudo timedatectl set-timezone Asia/Shanghai 2>/dev/null || true
echo "基础环境 OK"'

echo "========== [2/6] 安装 Docker =========="
S 'if ! command -v docker > /dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh > /dev/null 2>&1
fi
sudo systemctl enable docker > /dev/null 2>&1
sudo systemctl start docker
sudo usermod -aG docker '$SERVER_USER' 2>/dev/null || true
docker --version 2>/dev/null || sudo docker --version
sudo docker compose version 2>/dev/null || echo "compose 插件待确认"'

echo "========== [3/6] 防火墙 =========="
S 'sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
echo "y" | sudo ufw enable > /dev/null 2>&1 || true
sudo ufw status | head -8'

echo "========== [4/6] 拉取代码 =========="
S 'mkdir -p /app && cd /app
if [ ! -d harness ]; then
  sudo git clone https://github.com/3128771573/project-harness.git harness
fi
cd /app/harness
sudo mkdir -p /data/harness/pgdata /data/harness/uploads
echo "代码就绪: $(ls | tr "\n" " ")"'

echo "========== [5/6] 配置 .env =========="
S 'cd /app/harness
if [ ! -f .env ]; then
  PG_PW=$(openssl rand -hex 16)
  JWT_SEC=$(openssl rand -hex 32)
  sudo tee .env > /dev/null <<EOF
POSTGRES_PASSWORD=${PG_PW}
JWT_SECRET=${JWT_SEC}
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
CORS_ORIGINS=http://124.222.140.57,http://localhost:8080
AI_API_KEY=
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat
UPLOAD_DIR=/app/uploads
EOF
  sudo chmod 600 .env
  echo ".env 已生成（强随机）"
else
  echo ".env 已存在，跳过"
fi'

echo "========== [6/6] 启动 =========="
S 'cd /app/harness
sudo cp docker-compose.prod.yml docker-compose.yml
sudo docker compose up -d --build 2>&1 | tail -20'
echo ""
echo "========== 部署完成！ =========="
echo "验证: curl http://${SERVER_IP}/api/v1/health"
echo "前端: http://${SERVER_IP}"
