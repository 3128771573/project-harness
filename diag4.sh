#!/bin/bash
MIRROR="https://docker.m.daocloud.io"
echo "=== token endpoint raw ==="
curl -4 -s --max-time 10 -w "\nHTTP=%{http_code}\n" "$MIRROR/token?service=registry.docker.io&scope=repository:library/alpine:pull" | head -c 600
echo ""
echo "=== try daocloud auth endpoint ==="
curl -4 -s --max-time 10 -w "\nHTTP=%{http_code}\n" "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/alpine:pull" | head -c 300
echo ""
echo "=== try 1panel mirror manifest ==="
curl -4 -s --max-time 10 -o /dev/null -w "1panel http=%{http_code}\n" -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json" "https://docker.1panel.live/v2/library/alpine/manifests/latest"
echo "=== try rat.dev mirror manifest ==="
curl -4 -s --max-time 10 -o /dev/null -w "rat http=%{http_code}\n" -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json" "https://hub.rat.dev/v2/library/alpine/manifests/latest"
echo "DONE"
