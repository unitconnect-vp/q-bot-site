-- D1 cleanup: PO test 더미 row 청소 (2026-05-05)
-- 영향 범위: po-test-*@example.com, test@example.com 등 PO 테스트 흔적

-- 관련 토큰·세션 먼저 (FK 무관하지만 안전하게)
DELETE FROM auth_tokens WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE 'po-test-%' OR email LIKE 'test%@example.com'
);
DELETE FROM sessions WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE 'po-test-%' OR email LIKE 'test%@example.com'
);
DELETE FROM game_records WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE 'po-test-%' OR email LIKE 'test%@example.com'
);
DELETE FROM game_states WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE 'po-test-%' OR email LIKE 'test%@example.com'
);

-- users 본체
DELETE FROM users WHERE email LIKE 'po-test-%' OR email LIKE 'test%@example.com';
