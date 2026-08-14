#!/bin/bash
set -e
cd /home/x230user/projects/harness
echo "=== 解包 ==="
tar xzf /tmp/harness-sync.tar.gz
find backend frontend/src -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
echo "=== git 提交推送 ==="
git add -A
git commit -m "feat(im): 站内私信 P0 - 私信/撤回/已读/隐藏/图片/搜索 + 公告机器人广播 + 明水印/零宽文本水印取证 + im/ws 实时通道 + 未读角标" 2>&1 | tail -3 || echo "no changes"
git push origin main 2>&1 | tail -3
echo "=== 部署 ==="
bash /home/x230user/projects/harness/deploy-r3.sh 2>&1 | tail -50
echo "=== DEPLOY DONE ==="
