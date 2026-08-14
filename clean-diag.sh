#!/bin/bash
set -e
sudo docker exec harness-db psql -U harness -d harness -q -c "
DELETE FROM refresh_tokens WHERE uid IN (SELECT uid FROM users WHERE email IN ('g8@example.com','g9@example.com'));
DELETE FROM login_logs WHERE uid IN (SELECT uid FROM users WHERE email IN ('g8@example.com','g9@example.com'));
DELETE FROM email_codes WHERE email IN ('g8@example.com','g9@example.com');
DELETE FROM users WHERE email IN ('g8@example.com','g9@example.com');"
echo CLEAN-DONE
