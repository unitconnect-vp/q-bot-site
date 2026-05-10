-- Q렌즈 v2.0 D1 schema — 방문자 분석 (Phase 1)
-- Migration: 0002_pageviews
-- 적용: cd api && npx wrangler d1 execute qlens-db --remote --file=migrations/0002_pageviews.sql
--      또는 .github/workflows/migrate-d1.yml 수동 트리거

-- 페이지뷰 원본 로그
-- 1행 = 1 페이지 노출. 집계는 admin/analytics 엔드포인트에서 SQL GROUP BY로 즉석 계산.
-- 한 번에 30~90일치만 보는 운영 가정. 90일 초과 행은 운영 중 주기적으로 정리.
CREATE TABLE IF NOT EXISTS pageviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL,                      -- 정규화된 URL pathname (쿼리·해시 제거, trailing slash 유지)
  referrer_host TEXT,                      -- 외부 referrer 호스트명만 보존 (예: 'google.com'). 동일 출처는 NULL.
  user_agent TEXT,                         -- 최대 255자
  country TEXT,                            -- CF-IPCountry (KR/US/JP/...)
  visitor_id TEXT NOT NULL,                -- 브라우저 first-party cookie 기반 익명 UUID (PII 아님)
  session_id TEXT NOT NULL,                -- 30분 idle session sessionStorage UUID
  user_id INTEGER,                         -- 로그인 사용자면 users.id, 아니면 NULL
  date_kr TEXT NOT NULL,                   -- KST 기준 'YYYY-MM-DD' (집계 인덱스용)
  viewed_at INTEGER NOT NULL               -- unix seconds
);

CREATE INDEX IF NOT EXISTS idx_pageviews_date_kr ON pageviews(date_kr);
CREATE INDEX IF NOT EXISTS idx_pageviews_path_date ON pageviews(path, date_kr);
CREATE INDEX IF NOT EXISTS idx_pageviews_visitor_date ON pageviews(visitor_id, date_kr);
