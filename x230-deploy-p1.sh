#!/bin/bash
set -e
cd /home/x230user/projects/harness
echo "=== 解包 ==="
tar xzf /tmp/harness-sync3.tar.gz
find backend frontend/src -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
echo "=== git 提交推送 ==="
git add -A
git commit -m "feat(im): P1 第一批 - 群聊全套(建群/成员管理/群消息/撤回/举报/WS群房间/未读聚合) + Admin举报审核页(删除/封禁/忽略+机器人告知) + 水印取证授权体系(一次性/按次/长期+吊销+日志) + 前端群聊tab与举报/授权UI" 2>&1 | tail -3 || echo "no changes"
git push origin main 2>&1 | tail -2
echo "=== 部署 ==="
bash /tmp/deploy-r3.sh 2>&1 | tail -30
echo "=== DEPLOY DONE ==="
