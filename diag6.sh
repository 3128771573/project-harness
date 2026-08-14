#!/bin/bash
MIRROR="https://docker.1panel.live"
echo "=== token endpoint raw ==="
curl -4 -s --max-time 10 -w "\nHTTP=%{http_code}\n" "$MIRROR/token?service=registry.docker.io&scope=repository:library/alpine:pull" | head -c 500
echo ""
echo "=== blob without token ==="
BLOB="sha256:0ac33e5f5afa79e08407586964c92f98956ab8b7eb94a9b8b98d532e45d21df5"
curl -4 -s -o /dev/null -w "noauth blob http=%{http_code} speed=%{speed_download}B/s size=%{size_download} time=%{time_total}s\n" \
  --max-time 60 "$MIRROR/v2/library/alpine/blobs/$BLOB"
echo "=== blob with auth.docker.io token attempt ==="
TOKEN2=$(curl -4 -s --max-time 10 "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/alpine:pull" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
echo "authdocker token_len=${#TOKEN2}"
echo "DONE"
