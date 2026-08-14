#!/bin/bash
echo "=== 密码哈希验证（应为 bcrypt 格式 \$2b\$...） ==="
docker exec harness-db psql -U harness -d harness -t -c "SELECT password_hash FROM users WHERE username='testuser1';"
echo ""
echo "=== 健康检查 ==="
curl -s http://localhost:8080/api/v1/health
echo ""
echo "=== 数据库表结构 ==="
docker exec harness-db psql -U harness -d harness -c "\d users"
echo "=== 端口监听 ==="
ss -tln 2>/dev/null | grep -E '8080|:8000' | head -4
echo "DONE"
