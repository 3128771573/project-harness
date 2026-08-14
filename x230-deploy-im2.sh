#!/bin/bash
set -e
cd /home/x230user/projects/harness
echo "=== 解包 ==="
tar xzf /tmp/harness-sync2.tar.gz
find backend frontend/src -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
echo "=== git 提交推送 ==="
git add -A
git commit -m "feat(im): 规格书补齐 - 拉黑管理端点/举报落库(reports)/WS心跳/deps机器人拒绝/消息4000 + Admin水印取证页/superadmin守卫/私信菜单入口" 2>&1 | tail -3 || echo "no changes"
git push origin main 2>&1 | tail -2
echo "=== 部署 ==="
bash /tmp/deploy-r3.sh 2>&1 | tail -40
echo "=== DEPLOY DONE ==="
