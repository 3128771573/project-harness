#!/bin/bash
# Project Harness 版本备份脚本
# 用法: bash backup.sh [版本标签]  例如: bash backup.sh v0.7-admin
# 备份内容: 项目代码 + 数据库快照 + 用户上传文件，全部存入 /hdd/harness/backups/
set -e

VERSION="${1:-$(date +%Y%m%d-%H%M)}"
BACKUP_ROOT="/hdd/harness/backups"
BACKUP_DIR="$BACKUP_ROOT/$VERSION"
PROJECT_DIR="$HOME/projects/harness"

mkdir -p "$BACKUP_DIR"
echo "=== 备份到: $BACKUP_DIR ==="

# 1. 项目代码（排除 .git / .env / node_modules）
echo "--- 1/4 备份项目代码 ---"
tar czf "$BACKUP_DIR/code.tar.gz" \
  --exclude='.git' --exclude='.env' --exclude='node_modules' --exclude='dist' \
  -C "$PROJECT_DIR" .

# 2. 数据库快照
echo "--- 2/4 备份数据库 ---"
docker exec harness-db pg_dump -U harness harness > "$BACKUP_DIR/database.sql"
gzip -f "$BACKUP_DIR/database.sql"
echo "    数据库: $(du -h "$BACKUP_DIR/database.sql.gz" | cut -f1)"

# 3. 用户上传文件
echo "--- 3/4 备份 uploads ---"
if docker volume inspect harness_uploads > /dev/null 2>&1; then
  docker run --rm -v harness_uploads:/data -v "$BACKUP_DIR":/backup \
    alpine tar czf /backup/uploads.tar.gz -C /data . 2>/dev/null
  echo "    uploads: $(du -h "$BACKUP_DIR/uploads.tar.gz" | cut -f1)"
else
  tar czf "$BACKUP_DIR/uploads.tar.gz" -C /hdd/harness/uploads . 2>/dev/null || echo "    (无 uploads 数据)"
fi

# 4. 版本信息
echo "--- 4/4 记录版本信息 ---"
cd "$PROJECT_DIR"
git log -1 --format="%H %s" > "$BACKUP_DIR/git-commit.txt"
git describe --tags 2>/dev/null >> "$BACKUP_DIR/git-commit.txt" || true
docker compose ps --format '{{.Name}} {{.Status}}' > "$BACKUP_DIR/containers.txt" 2>/dev/null || true
cat > "$BACKUP_DIR/README.txt" <<EOF
Project Harness 备份
版本: $VERSION
时间: $(date '+%Y-%m-%d %H:%M:%S')
内容: code.tar.gz (项目代码) / database.sql.gz (数据库) / uploads.tar.gz (用户文件)
恢复:
  1. tar xzf code.tar.gz -C 新目录
  2. gunzip database.sql.gz && cat database.sql | docker exec -i harness-db psql -U harness harness
EOF

echo ""
echo "=== 备份完成 ==="
ls -lh "$BACKUP_DIR"
echo "总大小: $(du -sh "$BACKUP_DIR" | cut -f1)"
