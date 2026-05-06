// Q렌즈 v2.0 게시판 핸들러 — Phase 2 MVP
//
// 엔드포인트:
//   GET    /posts?limit=20&offset=0  목록 (Bearer)
//   POST   /posts                    생성 (Bearer)
//   GET    /posts/:id                상세 (Bearer)
//   PATCH  /posts/:id                수정 (Bearer, 소유자)
//   DELETE /posts/:id                삭제 (Bearer, 소유자 or admin) — soft delete
//
// VP 결정 (2026-05-06):
//   - 회원 전용 커뮤니티(읽기·쓰기 모두 로그인 필수)
//   - 자본시장법·공인중개사법 위반 표현 1차 시드 12건 차단

import { verifyJWT } from '../lib/jwt.js';

const TITLE_MIN = 2;
const TITLE_MAX = 80;
const BODY_MIN = 5;
const BODY_MAX = 5000;
const LIST_LIMIT_DEFAULT = 20;
const LIST_LIMIT_MAX = 100;

// 자본시장법(주식 추천 금지)·공인중개사법(매물 추천 금지) 위반 가능 표현 1차 시드.
// 운영 중 VP 회고로 확장. 매칭 방식: NFKC 정규화 + lowercase 후 includes().
const BANNED_PHRASES = [
  '매수 추천', '매도 추천', '강력 매수', '필승 종목', '단타 추천',
  '리딩방', '내부 정보', '미공개 정보', '작전 종목',
  '매물 추천', '급매 알선', '직접 거래', '미등록 중개',
];

function normalize(s) {
  return String(s || '').normalize('NFKC').toLowerCase();
}

function findBanned(...texts) {
  const blob = texts.map(normalize).join('\n');
  for (const phrase of BANNED_PHRASES) {
    if (blob.includes(normalize(phrase))) return phrase;
  }
  return null;
}

function excerpt(body, max = 120) {
  const flat = String(body || '').replace(/\s+/g, ' ').trim();
  return flat.length > max ? flat.slice(0, max) + '…' : flat;
}

async function authPayload(req, env) {
  const auth = req.headers.get('Authorization');
  if (!auth || !auth.startsWith('Bearer ')) return null;
  const token = auth.slice(7);
  return await verifyJWT(token, env.JWT_SECRET);
}

// ─────── GET /posts ───────

export async function listPosts(req, env, origin, json, err) {
  const payload = await authPayload(req, env);
  if (!payload) return err('Unauthorized', 401, origin);

  const url = new URL(req.url);
  const limitParam = parseInt(url.searchParams.get('limit') || String(LIST_LIMIT_DEFAULT), 10);
  const offsetParam = parseInt(url.searchParams.get('offset') || '0', 10);
  const limit = Math.min(Math.max(Number.isFinite(limitParam) ? limitParam : LIST_LIMIT_DEFAULT, 1), LIST_LIMIT_MAX);
  const offset = Math.max(Number.isFinite(offsetParam) ? offsetParam : 0, 0);

  const { results } = await env.DB.prepare(
    `SELECT p.id, p.title, p.body, p.created_at, p.user_id, u.nickname
     FROM posts p JOIN users u ON p.user_id = u.id
     WHERE p.deleted = 0
     ORDER BY p.created_at DESC
     LIMIT ? OFFSET ?`
  ).bind(limit, offset).all();

  const totalRow = await env.DB.prepare(
    'SELECT COUNT(*) AS c FROM posts WHERE deleted = 0'
  ).first();

  const posts = (results || []).map(r => ({
    id: r.id,
    title: r.title,
    excerpt: excerpt(r.body),
    nickname: r.nickname,
    user_id: r.user_id,
    created_at: r.created_at,
  }));

  return json({ posts, total: totalRow ? totalRow.c : 0, limit, offset }, 200, origin);
}

// ─────── POST /posts ───────

export async function createPost(req, env, origin, json, err) {
  const payload = await authPayload(req, env);
  if (!payload) return err('Unauthorized', 401, origin);

  let body;
  try { body = await req.json(); } catch { return err('Invalid JSON', 400, origin); }

  const title = typeof body.title === 'string' ? body.title.trim() : '';
  const text = typeof body.body === 'string' ? body.body : '';

  if (title.length < TITLE_MIN || title.length > TITLE_MAX) {
    return err(`제목은 ${TITLE_MIN}~${TITLE_MAX}자여야 합니다.`, 400, origin);
  }
  if (text.length < BODY_MIN || text.length > BODY_MAX) {
    return err(`본문은 ${BODY_MIN}~${BODY_MAX}자여야 합니다.`, 400, origin);
  }
  const banned = findBanned(title, text);
  if (banned) {
    return err('정책 위반 표현이 포함되어 있습니다.', 400, origin);
  }

  const now = Math.floor(Date.now() / 1000);
  const result = await env.DB.prepare(
    `INSERT INTO posts (user_id, title, body, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?)`
  ).bind(payload.sub, title, text, now, now).run();

  return json({ id: result.meta.last_row_id }, 201, origin);
}

// ─────── GET /posts/:id ───────

export async function getPost(req, env, origin, json, err, id) {
  const payload = await authPayload(req, env);
  if (!payload) return err('Unauthorized', 401, origin);

  const row = await env.DB.prepare(
    `SELECT p.id, p.title, p.body, p.created_at, p.updated_at, p.user_id, u.nickname
     FROM posts p JOIN users u ON p.user_id = u.id
     WHERE p.id = ? AND p.deleted = 0`
  ).bind(id).first();

  if (!row) return err('글을 찾을 수 없습니다.', 404, origin);

  return json({
    id: row.id,
    title: row.title,
    body: row.body,
    nickname: row.nickname,
    user_id: row.user_id,
    created_at: row.created_at,
    updated_at: row.updated_at,
    is_owner: row.user_id === payload.sub,
  }, 200, origin);
}

// ─────── PATCH /posts/:id ───────

export async function updatePost(req, env, origin, json, err, id) {
  const payload = await authPayload(req, env);
  if (!payload) return err('Unauthorized', 401, origin);

  const row = await env.DB.prepare(
    'SELECT user_id, title, body FROM posts WHERE id = ? AND deleted = 0'
  ).bind(id).first();
  if (!row) return err('글을 찾을 수 없습니다.', 404, origin);
  if (row.user_id !== payload.sub) return err('본인 글만 수정할 수 있습니다.', 403, origin);

  let body;
  try { body = await req.json(); } catch { return err('Invalid JSON', 400, origin); }

  const nextTitle = typeof body.title === 'string' ? body.title.trim() : row.title;
  const nextBody = typeof body.body === 'string' ? body.body : row.body;

  if (nextTitle.length < TITLE_MIN || nextTitle.length > TITLE_MAX) {
    return err(`제목은 ${TITLE_MIN}~${TITLE_MAX}자여야 합니다.`, 400, origin);
  }
  if (nextBody.length < BODY_MIN || nextBody.length > BODY_MAX) {
    return err(`본문은 ${BODY_MIN}~${BODY_MAX}자여야 합니다.`, 400, origin);
  }
  const banned = findBanned(nextTitle, nextBody);
  if (banned) {
    return err('정책 위반 표현이 포함되어 있습니다.', 400, origin);
  }

  const now = Math.floor(Date.now() / 1000);
  await env.DB.prepare(
    'UPDATE posts SET title = ?, body = ?, updated_at = ? WHERE id = ?'
  ).bind(nextTitle, nextBody, now, id).run();

  return json({ ok: true }, 200, origin);
}

// ─────── DELETE /posts/:id ───────

export async function deletePost(req, env, origin, json, err, id) {
  const payload = await authPayload(req, env);
  if (!payload) return err('Unauthorized', 401, origin);

  const row = await env.DB.prepare(
    'SELECT user_id FROM posts WHERE id = ? AND deleted = 0'
  ).bind(id).first();
  if (!row) return err('글을 찾을 수 없습니다.', 404, origin);

  const isOwner = row.user_id === payload.sub;
  const isAdmin = payload.role === 'admin';
  if (!isOwner && !isAdmin) return err('본인 글만 삭제할 수 있습니다.', 403, origin);

  const now = Math.floor(Date.now() / 1000);
  await env.DB.prepare(
    'UPDATE posts SET deleted = 1, updated_at = ? WHERE id = ?'
  ).bind(now, id).run();

  return json({ ok: true }, 200, origin);
}
