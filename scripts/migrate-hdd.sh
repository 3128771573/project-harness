#!/bin/bash
# 数据库 + 数据卷迁移到 /hdd（执行前确保 compose 已停止）
set -e

echo "=== 1. 创建 /hdd 目录结构 ==="
mkdir -p /hdd/harness/pgdata /hdd/harness/uploads /hdd/harness/backups
ls -ld /hdd/harness*

echo ""
echo "=== 2. 停止服务 ==="
cd ~/projects/harness
docker compose down 2>&1 | tail -3

echo ""
echo "=== 3. 迁移 pgdata 卷 → /hdd/harness/pgdata ==="
if docker volume inspect harness_pgdata > /dev/null 2>&1; then
  docker run --rm -v harness_pgdata:/from -v /hdd/harness/pgdata:/to \
    alpine sh -c "cp -a /from/. /to/ && chown -R 999:999 /to" 2>/dev/null
  echo "pgdata 迁移完成: $(du -sh /hdd/harness/pgdata | cut -f1)"
else
  echo "无 pgdata 卷（可能已是 bind mount）"
fi

echo ""
echo "=== 4. 迁移 uploads 卷 → /hdd/harness/uploads ==="
if docker volume inspect harness_uploads > /dev/null 2>&1; then
  docker run --rm -v harness_uploads:/from -v /hdd/harness/uploads:/to \
    alpine sh -c "cp -a /from/. /to/ && chown -R 1000:1000 /to" 2>/dev/null
  echo "uploads 迁移完成: $(du -sh /hdd/harness/uploads | cut -f1)"
else
  echo "无 uploads 卷"
fi

echo ""
echo "=== 5. 更新 docker-compose.yml 为 bind mount ==="
echo "（由部署脚本自动替换，或手动编辑）"
echo "DONE - 下一步: 修改 compose 后执行 docker compose up -d"
