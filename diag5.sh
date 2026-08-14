#!/bin/bash
MIRROR="https://docker.1panel.live"
echo "=== 1. token from 1panel ==="
TOKEN=$(curl -4 -s --max-time 10 "$MIRROR/token?service=registry.docker.io&scope=repository:library/alpine:pull" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
echo "token_len=${#TOKEN}"
echo "=== 2. manifest via 1panel ==="
curl -4 -s --max-time 15 -o /dev/null -w "manifest http=%{http_code} time=%{time_total}s\n" \
  -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json" \
  "$MIRROR/v2/library/alpine/manifests/latest"
echo "=== 3. blob via 1panel ==="
BLOB="sha256:0ac33e5f5afa79e08407586964c92f98956ab8b7eb94a9b8b98d532e45d21df5"
if [ -n "$TOKEN" ]; then
  curl -4 -s -o /dev/null -w "blob http=%{http_code} speed=%{speed_download}B/s size=%{size_download} time=%{time_total}s\n" \
    --max-time 60 -H "Authorization: Bearer $TOKEN" "$MIRROR/v2/library/alpine/blobs/$BLOB"
else
  echo "no token, skip blob test"
fi
echo "DONE"
