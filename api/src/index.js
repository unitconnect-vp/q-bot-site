// Q렌즈 v2.0 인증 API — Cloudflare Worker
// 엔드포인트:
//   POST /api/auth/signup           이메일+비번 회원가입
//   GET  /api/auth/verify-email     이메일 인증 링크
//   POST /api/auth/login            이메일+비번 로그인
//   GET  /api/auth/google           Google OAuth 시작
//   GET  /api/auth/google/callback  Google 콜백
//   POST /api/auth/refresh          access_token 갱신
//   POST /api/auth/logout           로그아웃
//   GET  /api/me                    현재 사용자 정보

import { hashPassword, verifyPassword, generateToken, hashToken } from './lib/crypto.js';
import { signJWT, verifyJWT } from './lib/jwt.js';
import { buildGoogleAuthUrl, exchangeCodeForToken, fetchGoogleUserInfo } from './lib/google.js';
import { sendEmail, emailVerifyTemplate } from './lib/email.js';

const ACCESS_TOKEN_TTL = 900;                   // 15분
const REFRESH_TOKEN_TTL = 30 * 24 * 3600;       // 30일
const EMAIL_VERIFY_TTL = 24 * 3600;             // 24시간

const ALLOWED_ORIGINS = new Set([
  'https://q-bot.kr',
  'http://localhost:8787',
  'http://localhost:3000'
]);

// ─────── 유틸 ───────

function corsHeaders(origin) {
  const allowed = ALLOWED_ORIGINS.has(origin) ? origin : 'https://q-bot.kr';
  return {
    'Access-Control-Allow-Origin': allowed,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Credentials': 'true',
    'Vary': 'Origin'
  };
}

function json(data, status = 200, origin, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      ...corsHeaders(origin),
      ...extraHeaders
    }
  });
}

function err(message, status, origin) {
  return json({ error: message }, status, origin);
}

function getCookie(req, name) {
  const cookie = req.headers.get('Cookie') || '';
  const m = cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`));
  return m ? decodeURIComponent(m[1]) : null;
}

function setCookieHeader(name, value, maxAge) {
  return `${name}=${encodeURIComponent(value)}; Max-Age=${maxAge}; Path=/; HttpOnly; Secure; SameSite=Lax`;
}

function clearCookieHeader(name) {
  return `${name}=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Lax`;
}

function isValidEmail(s) {
  return typeof s === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s) && s.length <= 254;
}

// ─────── 라우터 ───────

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    const origin = req.headers.get('Origin') || 'https://q-bot.kr';

    if (req.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders(origin) });
    }

    try {
      const path = url.pathname;
      const m = req.method;

      if (path === '/auth/signup' && m === 'POST')          return signup(req, env, origin);
      if (path === '/auth/login' && m === 'POST')           return login(req, env, origin);
      if (path === '/auth/verify-email' && m === 'GET')     return verifyEmail(req, env);
      if (path === '/auth/google' && m === 'GET')           return googleStart(req, env);
      if (path === '/auth/google/callback' && m === 'GET')  return googleCallback(req, env);
      if (path === '/auth/refresh' && m === 'POST')         return refresh(req, env, origin);
      if (path === '/auth/logout' && m === 'POST')          return logout(req, env, origin);
      if (path === '/me' && m === 'GET')                    return getMe(req, env, origin);

      return err('Not found', 404, origin);
    } catch (e) {
      console.error('[error]', e.stack || e);
      return err('Internal error', 500, origin);
    }
  }
};

// ─────── 회원가입 ───────

async function signup(req, env, origin) {
  let body;
  try { body = await req.json(); } catch { return err('Invalid JSON', 400, origin); }
  const { email, password, nickname } = body;

  if (!isValidEmail(email)) return err('유효하지 않은 이메일 주소입니다.', 400, origin);
  if (typeof password !== 'string' || password.length < 8) {
    return err('비밀번호는 8자 이상이어야 합니다.', 400, origin);
  }
  if (typeof nickname !== 'string' || nickname.length < 2 || nickname.length > 20) {
    return err('닉네임은 2~20자여야 합니다.', 400, origin);
  }

  const exists = await env.DB.prepare('SELECT id FROM users WHERE email = ?').bind(email).first();
  if (exists) return err('이미 가입된 이메일입니다.', 409, origin);

  const passwordHash = await hashPassword(password);
  const now = Math.floor(Date.now() / 1000);

  const result = await env.DB.prepare(
    `INSERT INTO users (email, password_hash, nickname, email_verified, created_at)
     VALUES (?, ?, ?, 0, ?)`
  ).bind(email, passwordHash, nickname, now).run();

  const userId = result.meta.last_row_id;

  // 인증 토큰 생성·발송
  const verifyToken = generateToken();
  await env.DB.prepare(
    `INSERT INTO auth_tokens (token, user_id, purpose, expires_at, created_at)
     VALUES (?, ?, 'email_verify', ?, ?)`
  ).bind(verifyToken, userId, now + EMAIL_VERIFY_TTL, now).run();

  const verifyUrl = `${env.API_URL}/auth/verify-email?token=${verifyToken}`;
  try {
    await sendEmail({
      to: email,
      subject: '[Q렌즈] 가입 확인 메일',
      html: emailVerifyTemplate({ nickname, verifyUrl }),
      env
    });
  } catch (e) {
    // 이메일 발송 실패해도 가입은 유효 — 로그만 남김
    console.error('[signup] email send failed:', e);
  }

  return json({ ok: true, message: '인증 메일을 발송했습니다. 메일함을 확인해주세요.' }, 200, origin);
}

// ─────── 이메일 인증 ───────

async function verifyEmail(req, env) {
  const url = new URL(req.url);
  const token = url.searchParams.get('token');
  if (!token) return new Response('인증 토큰이 필요합니다.', { status: 400 });

  const now = Math.floor(Date.now() / 1000);
  const row = await env.DB.prepare(
    `SELECT user_id, expires_at, used FROM auth_tokens
     WHERE token = ? AND purpose = 'email_verify'`
  ).bind(token).first();

  if (!row || row.used || row.expires_at < now) {
    return new Response('인증 토큰이 만료되었거나 유효하지 않습니다.', { status: 400 });
  }

  await env.DB.batch([
    env.DB.prepare('UPDATE users SET email_verified = 1 WHERE id = ?').bind(row.user_id),
    env.DB.prepare('UPDATE auth_tokens SET used = 1 WHERE token = ?').bind(token)
  ]);

  return Response.redirect(`${env.SITE_URL}/auth/verified`, 302);
}

// ─────── 로그인 ───────

async function login(req, env, origin) {
  let body;
  try { body = await req.json(); } catch { return err('Invalid JSON', 400, origin); }
  const { email, password } = body;

  if (!isValidEmail(email) || typeof password !== 'string') {
    return err('이메일 또는 비밀번호가 일치하지 않습니다.', 401, origin);
  }

  const user = await env.DB.prepare(
    'SELECT id, password_hash, nickname, email_verified, role FROM users WHERE email = ?'
  ).bind(email).first();

  if (!user || !user.password_hash) {
    return err('이메일 또는 비밀번호가 일치하지 않습니다.', 401, origin);
  }

  const ok = await verifyPassword(password, user.password_hash);
  if (!ok) return err('이메일 또는 비밀번호가 일치하지 않습니다.', 401, origin);

  if (!user.email_verified) {
    return err('이메일 인증이 필요합니다. 메일함을 확인해주세요.', 403, origin);
  }

  return issueTokens(user, env, origin, req, false);
}

// ─────── Google OAuth 시작 ───────

async function googleStart(req, env) {
  const state = generateToken(16);
  const authUrl = buildGoogleAuthUrl(
    env.GOOGLE_CLIENT_ID,
    `${env.API_URL}/auth/google/callback`,
    state
  );
  return new Response(null, {
    status: 302,
    headers: {
      Location: authUrl,
      'Set-Cookie': `oauth_state=${state}; Max-Age=600; Path=/; HttpOnly; Secure; SameSite=Lax`
    }
  });
}

// ─────── Google OAuth 콜백 ───────

async function googleCallback(req, env) {
  const url = new URL(req.url);
  const code = url.searchParams.get('code');
  const state = url.searchParams.get('state');
  const cookieState = getCookie(req, 'oauth_state');

  if (!code || !state || state !== cookieState) {
    return new Response('Invalid OAuth state', { status: 400 });
  }

  let tokens, userinfo;
  try {
    tokens = await exchangeCodeForToken(
      code,
      env.GOOGLE_CLIENT_ID,
      env.GOOGLE_CLIENT_SECRET,
      `${env.API_URL}/auth/google/callback`
    );
    userinfo = await fetchGoogleUserInfo(tokens.access_token);
  } catch (e) {
    console.error('[google callback]', e);
    return new Response('Google 인증에 실패했습니다.', { status: 500 });
  }

  const { sub, email, name } = userinfo;
  if (!sub || !email) return new Response('Google 사용자 정보가 부족합니다.', { status: 400 });

  // 기존 사용자 조회 (oauth_id 우선)
  let user = await env.DB.prepare(
    'SELECT id, nickname, email_verified, role FROM users WHERE oauth_provider = ? AND oauth_id = ?'
  ).bind('google', sub).first();

  if (!user) {
    // 이메일 일치 사용자가 있으면 OAuth 연동
    const byEmail = await env.DB.prepare(
      'SELECT id, nickname, email_verified, role FROM users WHERE email = ?'
    ).bind(email).first();
    if (byEmail) {
      await env.DB.prepare(
        'UPDATE users SET oauth_provider = ?, oauth_id = ?, email_verified = 1 WHERE id = ?'
      ).bind('google', sub, byEmail.id).run();
      user = byEmail;
    } else {
      // 신규 회원 — Google 닉네임 사용 (충돌 시 이메일 prefix)
      const now = Math.floor(Date.now() / 1000);
      const nickname = (name || email.split('@')[0]).slice(0, 20);
      const result = await env.DB.prepare(
        `INSERT INTO users (email, nickname, oauth_provider, oauth_id, email_verified, created_at)
         VALUES (?, ?, 'google', ?, 1, ?)`
      ).bind(email, nickname, sub, now).run();
      user = { id: result.meta.last_row_id, nickname, email_verified: 1, role: 'member' };
    }
  }

  return issueTokens(user, env, null, req, true);
}

// ─────── access_token 갱신 ───────

async function refresh(req, env, origin) {
  const refreshT = getCookie(req, 'refresh_token');
  if (!refreshT) return err('리프레시 토큰이 없습니다.', 401, origin);

  const refreshHash = await hashToken(refreshT);
  const now = Math.floor(Date.now() / 1000);

  const session = await env.DB.prepare(
    `SELECT s.id, s.user_id, s.expires_at, u.nickname, u.role
     FROM sessions s JOIN users u ON s.user_id = u.id
     WHERE s.refresh_token_hash = ?`
  ).bind(refreshHash).first();

  if (!session || session.expires_at < now) {
    return err('리프레시 토큰이 만료되었습니다.', 401, origin);
  }

  const accessToken = await signJWT(
    { sub: session.user_id, nickname: session.nickname, role: session.role },
    env.JWT_SECRET,
    ACCESS_TOKEN_TTL
  );
  return json({ access_token: accessToken, expires_in: ACCESS_TOKEN_TTL }, 200, origin);
}

// ─────── 로그아웃 ───────

async function logout(req, env, origin) {
  const refreshT = getCookie(req, 'refresh_token');
  if (refreshT) {
    const hash = await hashToken(refreshT);
    await env.DB.prepare('DELETE FROM sessions WHERE refresh_token_hash = ?').bind(hash).run();
  }
  return json({ ok: true }, 200, origin, { 'Set-Cookie': clearCookieHeader('refresh_token') });
}

// ─────── /me ───────

async function getMe(req, env, origin) {
  const auth = req.headers.get('Authorization');
  if (!auth || !auth.startsWith('Bearer ')) return err('Unauthorized', 401, origin);
  const token = auth.slice(7);
  const payload = await verifyJWT(token, env.JWT_SECRET);
  if (!payload) return err('Invalid token', 401, origin);

  const user = await env.DB.prepare(
    'SELECT id, email, nickname, role, oauth_provider, created_at FROM users WHERE id = ?'
  ).bind(payload.sub).first();
  if (!user) return err('User not found', 404, origin);
  return json(user, 200, origin);
}

// ─────── 토큰 발급 (로그인·OAuth 공통) ───────

async function issueTokens(user, env, origin, req, redirect) {
  const accessToken = await signJWT(
    { sub: user.id, nickname: user.nickname, role: user.role || 'member' },
    env.JWT_SECRET,
    ACCESS_TOKEN_TTL
  );
  const refreshT = generateToken(48);
  const refreshHash = await hashToken(refreshT);
  const now = Math.floor(Date.now() / 1000);
  const sessionId = crypto.randomUUID();

  await env.DB.batch([
    env.DB.prepare(
      `INSERT INTO sessions (id, user_id, refresh_token_hash, expires_at, created_at, user_agent, ip)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      sessionId, user.id, refreshHash,
      now + REFRESH_TOKEN_TTL, now,
      (req.headers.get('User-Agent') || '').slice(0, 255),
      req.headers.get('CF-Connecting-IP') || ''
    ),
    env.DB.prepare('UPDATE users SET last_login_at = ? WHERE id = ?').bind(now, user.id)
  ]);

  const refreshCookie = setCookieHeader('refresh_token', refreshT, REFRESH_TOKEN_TTL);
  const clearOAuthState = clearCookieHeader('oauth_state');

  if (redirect) {
    // OAuth 콜백: 사이트 측 콜백 페이지로 리다이렉트. access_token은 fragment(#)로 전달 (브라우저 히스토리·서버 로그에 남지 않음).
    const target = `${env.SITE_URL}/auth/callback#access_token=${encodeURIComponent(accessToken)}&expires_in=${ACCESS_TOKEN_TTL}`;
    return new Response(null, {
      status: 302,
      headers: {
        Location: target,
        'Set-Cookie': [refreshCookie, clearOAuthState].join(', ')
      }
    });
  }
  return json(
    {
      access_token: accessToken,
      expires_in: ACCESS_TOKEN_TTL,
      user: { id: user.id, nickname: user.nickname, role: user.role || 'member' }
    },
    200, origin,
    { 'Set-Cookie': refreshCookie }
  );
}
