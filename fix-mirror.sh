#!/bin/bash
# Update docker daemon.json to prioritize working mirror
set -e
PW='3128771573'

# backup
echo "$PW" | sudo -S -p '' cp /etc/docker/daemon.json /etc/docker/daemon.json.bak 2>/dev/null

# write new config
cat > /tmp/daemon.json.new <<'EOF'
{
  "registry-mirrors": [
    "https://docker.1panel.live",
    "https://hub.rat.dev",
    "https://docker.m.daocloud.io"
  ]
}
EOF

echo "$PW" | sudo -S -p '' cp /tmp/daemon.json.new /etc/docker/daemon.json 2>/dev/null
echo "=== new daemon.json ==="
cat /etc/docker/daemon.json

# restart docker
echo "$PW" | sudo -S -p '' systemctl restart docker 2>/dev/null
sleep 3
echo "=== docker status ==="
systemctl is-active docker
docker version --format 'server={{.Server.Version}}' 2>&1
echo "DONE"
