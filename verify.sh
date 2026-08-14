#!/bin/bash
BASE="http://localhost:8080/api/v1"
echo "=== 1. 注册新用户 ==="
REG=$(curl -s -X POST "$BASE/auth/register" -H "Content-Type: application/json" \
  -d '{"username":"testuser1","email":"test1@example.com","password":"TestPass123"}')
echo "$REG" | python3 -m json.tool 2>/dev/null || echo "$REG"
UID_VAL=$(echo "$REG" | python3 -c "import sys,json;print(json.load(sys.stdin)['user']['uid'])" 2>/dev/null)
TOKEN=$(echo "$REG" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
echo "UID=$UID_VAL"

echo ""
echo "=== 2. 登录（正确密码）==="
LOGIN=$(curl -s -X POST "$BASE/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"test1@example.com","password":"TestPass123"}')
echo "$LOGIN" | python3 -c "import sys,json;d=json.load(sys.stdin);print('login OK, user:', d['user']['username'], d['user']['uid'])" 2>/dev/null || echo "$LOGIN"

echo ""
echo "=== 3. 登录（错误密码，应拒绝）==="
BAD=$(curl -s -w " HTTP=%{http_code}" -X POST "$BASE/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"test1@example.com","password":"WrongPass999"}')
echo "$BAD"

echo ""
echo "=== 4. 重复注册（应 409）==="
DUP=$(curl -s -w " HTTP=%{http_code}" -X POST "$BASE/auth/register" -H "Content-Type: application/json" \
  -d '{"username":"testuser1","email":"test1@example.com","password":"TestPass123"}')
echo "$DUP"

echo ""
echo "=== 5. 用 token 获取 /user/me ==="
if [ -n "$TOKEN" ]; then
  curl -s "$BASE/user/me" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null
else
  echo "no token"
fi

echo ""
echo "=== 6. 无 token 访问（应 401）==="
curl -s -w " HTTP=%{http_code}" "$BASE/user/me"
echo ""
echo "DONE"
