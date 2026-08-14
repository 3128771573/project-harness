#!/bin/bash
echo "=== 1. TCP to Docker Hub CDN (v4) ==="
timeout 6 bash -c 'echo > /dev/tcp/production.cloudflare.docker.com/443' 2>/dev/null && echo "TCP_OK" || echo "TCP_FAIL"
echo "=== 2. TCP to Docker Hub CDN (v6) ==="
timeout 6 bash -c 'echo > /dev/tcp/::1/443' 2>/dev/null && echo "TCP_OK" || echo "TCP_FAIL"
echo "=== 3. curl v4 headers from CF CDN ==="
curl -4 -s -o /dev/null -w "http=%{http_code} connect=%{time_connect}s total=%{time_total}s\n" --max-time 8 https://production.cloudflare.docker.com/ 2>&1
echo "=== 4. curl v6 headers from CF CDN ==="
curl -6 -s -o /dev/null -w "http=%{http_code} connect=%{time_connect}s total=%{time_total}s\n" --max-time 8 https://production.cloudflare.docker.com/ 2>&1
echo "=== 5. actual blob download test from mirror ==="
curl -4 -s -o /dev/null -w "mirror http=%{http_code} speed=%{speed_download}B/s total=%{time_total}s\n" --max-time 20 "https://docker.m.daocloud.io/v2/library/alpine/blobs/sha256:0ac33e5f5afa79e08407586964c92f98956ab8b7eb94a9b8b98d532e45d21df5" 2>&1
echo "=== done ==="
