#!/bin/bash
echo "--- production.cloudflare.docker.com (v4) ---"
timeout 8 curl -4 -sI https://production.cloudflare.docker.com/ 2>&1 | head -2
echo "CF_EXIT=$?"
echo "--- ipv6 check on mirror ---"
timeout 5 curl -6 -sI https://docker.m.daocloud.io/v2/ 2>&1 | head -2
echo "IPV6_EXIT=$?"
echo "--- resolve hosts ---"
getent ahostsv4 production.cloudflare.docker.com | head -3
getent ahostsv4 docker.m.daocloud.io | head -3
echo "--- done ---"
