#!/bin/bash
MIRROR="https://docker.m.daocloud.io"
# 1. get token from mirror
TOKEN=$(curl -4 -s --max-time 10 "$MIRROR/token?service=registry.docker.io&scope=repository:library/alpine:pull" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])" 2>/dev/null)
echo "token_len=${#TOKEN}"
# 2. download a real blob (~3MB layer) and measure speed
BLOB="sha256:0ac33e5f5afa79e08407586964c92f98956ab8b7eb94a9b8b98d532e45d21df5"
curl -4 -s -o /dev/null -w "blob http=%{http_code} speed=%{speed_download}B/s size=%{size_download} time=%{time_total}s\n" \
  --max-time 60 -H "Authorization: Bearer $TOKEN" "$MIRROR/v2/library/alpine/blobs/$BLOB"
echo "DONE"
