/**
 * Q렌즈 v2.0 클라이언트 인증 라이브러리
 *
 * 의존성: 없음 (vanilla JS)
 * 백엔드: https://api.q-bot.kr
 *
 * 사용:
 *   await QLensAuth.signup({email, password, nickname});
 *   await QLensAuth.login({email, password});
 *   QLensAuth.googleLoginStart();
 *   const me = await QLensAuth.getMe();
 *   await QLensAuth.logout();
 *
 * 자동 동작:
 *   - 헤더 .site-nav 끝에 "로그인" 또는 "마이" 버튼 자동 주입
 *   - access_token 만료 1분 전 자동 refresh 시도
 */
(function () {
  'use strict';

  const API = 'https://api.q-bot.kr';
  const TOKEN_KEY = 'qlens_access_token';
  const EXPIRES_KEY = 'qlens_access_expires';

  // ─────── Token 저장소 (sessionStorage) ───────

  function setToken(token, expiresInSec) {
    try {
      sessionStorage.setItem(TOKEN_KEY, token);
      sessionStorage.setItem(EXPIRES_KEY, String(Date.now() + expiresInSec * 1000));
    } catch (e) { /* private mode etc. */ }
  }

  function getToken() {
    try { return sessionStorage.getItem(TOKEN_KEY); }
    catch (e) { return null; }
  }

  function clearToken() {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(EXPIRES_KEY);
    } catch (e) {}
  }

  function tokenExpiringSoon() {
    const exp = parseInt(sessionStorage.getItem(EXPIRES_KEY) || '0', 10);
    return Date.now() > exp - 60_000; // 1분 전 만료 간주
  }

  // ─────── HTTP 헬퍼 ───────

  async function postJSON(path, body) {
    const res = await fetch(API + path, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    let data = null;
    try { data = await res.json(); } catch (e) {}
    if (!res.ok) {
      const err = new Error((data && data.error) || `HTTP ${res.status}`);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  async function authedGet(path) {
    let token = getToken();
    if (!token) return { res: { ok: false, status: 401 }, data: null };

    if (tokenExpiringSoon()) {
      try { token = await refresh(); }
      catch (e) { return { res: { ok: false, status: 401 }, data: null }; }
    }

    const res = await fetch(API + path, {
      credentials: 'include',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    let data = null;
    try { data = await res.json(); } catch (e) {}
    return { res, data };
  }

  // ─────── Public API ───────

  async function signup({ email, password, nickname }) {
    return postJSON('/auth/signup', { email, password, nickname });
  }

  async function login({ email, password }) {
    const data = await postJSON('/auth/login', { email, password });
    if (data && data.access_token) {
      setToken(data.access_token, data.expires_in);
    }
    return data;
  }

  async function logout() {
    try {
      await fetch(API + '/auth/logout', { method: 'POST', credentials: 'include' });
    } catch (e) {}
    clearToken();
  }

  async function refresh() {
    const res = await fetch(API + '/auth/refresh', {
      method: 'POST',
      credentials: 'include'
    });
    if (!res.ok) {
      clearToken();
      throw new Error('refresh failed');
    }
    const data = await res.json();
    setToken(data.access_token, data.expires_in);
    return data.access_token;
  }

  async function getMe() {
    const { res, data } = await authedGet('/me');
    if (!res.ok) return null;
    return data;
  }

  function googleLoginStart() {
    window.location.href = API + '/auth/google';
  }

  function isLoggedIn() {
    return !!getToken();
  }

  function handleOAuthCallback() {
    // /auth/callback에서 호출. URL fragment에서 토큰 파싱 후 저장
    const hash = (window.location.hash || '').replace(/^#/, '');
    const params = new URLSearchParams(hash);
    const token = params.get('access_token');
    const expiresIn = parseInt(params.get('expires_in') || '900', 10);
    if (token) {
      setToken(token, expiresIn);
      return true;
    }
    return false;
  }

  // ─────── 헤더 nav 자동 주입 ───────

  async function injectNavAuthButton() {
    const nav = document.querySelector('.site-nav');
    if (!nav) return;
    if (nav.querySelector('.nav-auth-btn')) return;

    if (isLoggedIn()) {
      // 로그인 상태로 표시. 백그라운드로 검증.
      const a = document.createElement('a');
      a.href = '/mypage/';
      a.className = 'nav-auth-btn';
      a.textContent = '마이';
      nav.appendChild(a);

      // 백그라운드 검증 — 실패 시 토큰 클리어 + 로그인 버튼으로 변경
      getMe().then(me => {
        if (!me) {
          clearToken();
          a.href = '/auth/login/';
          a.textContent = '로그인';
        }
      }).catch(() => {});
    } else {
      const a = document.createElement('a');
      a.href = '/auth/login/';
      a.className = 'nav-auth-btn';
      a.textContent = '로그인';
      nav.appendChild(a);
    }
  }

  // ─────── Export ───────

  window.QLensAuth = {
    signup, login, logout, getMe, refresh,
    googleLoginStart, isLoggedIn, getToken, clearToken,
    handleOAuthCallback,
    _injectNav: injectNavAuthButton
  };

  // ─────── 자동 nav 주입 ───────

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectNavAuthButton);
  } else {
    injectNavAuthButton();
  }
})();
