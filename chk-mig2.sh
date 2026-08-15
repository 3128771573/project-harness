#!/bin/bash
echo "=== 容器内迁移文件 ==="
sudo docker exec harness-backend ls /app/alembic/versions/ | sort
echo "=== 宿主机 /app/harness/backend/alembic ==="
ls /app/harness/backend/alembic/versions/ | sort
echo "=== 镜像构建时间 ==="
sudo docker inspect harness-backend --format "{{.Created}}"
echo DONE
