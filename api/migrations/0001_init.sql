-- Q렌즈 v2.0 D1 schema — Phase 1
-- Migration: 0001_init
-- 적용: npm run db:migrate (=== wrangler d1 execute qlens-db --remote --file=migrations/0001_init.sql)

-- 회원
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT,                      -- OAuth 회원은 NULL 허용
  nickname TEXT NOT NULL,
  oauth_provider TEXT,                     -- 'google' / NULL
  oauth_id TEXT,
  email_verified INTEGER DEFAULT 0,
  role TEXT DEFAULT 'member',              -- 'member' / 'admin'
  created_at INTEGER NOT NULL,
  last_login_at INTEGER
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_oauth
  ON users(oauth_provider, oauth_id)
  WHERE oauth_provider IS NOT NULL;

-- 게임 완료 기록
CREATE TABLE IF NOT EXISTS game_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  game_type TEXT NOT NULL,                 -- 'sudoku' / 'nemonemo'
  difficulty TEXT,                         -- 'easy' / 'medium' / 'hard'
  completion_time_sec INTEGER,
  completed INTEGER DEFAULT 0,
  played_at INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_records_user_game ON game_records(user_id, game_type);
CREATE INDEX IF NOT EXISTS idx_records_played ON game_records(played_at);

-- 진행 중 게임 (이어하기)
CREATE TABLE IF NOT EXISTS game_states (
  user_id INTEGER NOT NULL,
  game_type TEXT NOT NULL,
  state_json TEXT NOT NULL,
  updated_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, game_type),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 이메일 인증·비밀번호 재설정 토큰
CREATE TABLE IF NOT EXISTS auth_tokens (
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  purpose TEXT NOT NULL,                   -- 'email_verify' / 'password_reset'
  expires_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  used INTEGER DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens(user_id);

-- Refresh token 세션
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,                     -- UUID
  user_id INTEGER NOT NULL,
  refresh_token_hash TEXT NOT NULL,
  expires_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL,
  user_agent TEXT,
  ip TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_refresh_hash ON sessions(refresh_token_hash);
