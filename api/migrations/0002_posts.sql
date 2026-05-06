-- Q렌즈 v2.0 D1 schema — Phase 2 게시판 MVP
-- Migration: 0002_posts
-- 적용: npx wrangler d1 execute qlens-db --remote --file=migrations/0002_posts.sql
--
-- VP 결정 (2026-05-06):
--   - MVP 범위: 글(post) CRUD만. 댓글·신고·admin 모더레이션은 다음 마이그레이션.
--   - 회원 전용 커뮤니티(읽기·쓰기 모두 로그인 필수).
--   - title 2~80자, body 5~5000자.

CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  deleted INTEGER DEFAULT 0,                 -- soft delete (1이면 목록·상세에서 제외)
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id);
