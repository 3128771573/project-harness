-- 清理 im-live 测试用户（含与机器人的会话）
DELETE FROM dm_messages WHERE conversation_id IN (
  SELECT id FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com'))
);
DELETE FROM dm_conversation_members WHERE conversation_id IN (
  SELECT id FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com'))
);
DELETE FROM dm_conversations WHERE user_a IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com')) OR user_b IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com'));
DELETE FROM blocks WHERE uid IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com')) OR blocked_uid IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com'));
DELETE FROM refresh_tokens WHERE uid IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com'));
DELETE FROM login_logs WHERE uid IN (SELECT uid FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com'));
DELETE FROM email_codes WHERE email IN ('im-live-a@example.com','im-live-b@example.com');
DELETE FROM users WHERE email IN ('im-live-a@example.com','im-live-b@example.com');
SELECT 'cleanup done' AS status;
