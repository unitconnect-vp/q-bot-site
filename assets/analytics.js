/**
 * Q렌즈 v2.0 자체 방문자 트래커
 *
 * 의존성: 없음 (vanilla, defer 로드 가정)
 * 백엔드: POST https://api.q-bot.kr/track
 *
 * 동작:
 *   1) first-party 쿠키 qlens_vid (UUID, 365일) 발급/유지 → visitor_id
 *   2) sessionStorage qlens_sid (UUID, 30분 idle 후 재발급) → session_id
 *   3) DOMContentLoaded 시점에 1회 POST. 페이지 path/referrer 전달.
 *   4) sendBeacon 우선, 실패 시 fetch keepalive 폴백.
 *
 * 옵트아웃:
 *   - localStorage.qlens_no_track === '1' 이면 전송 안 함.
 *   - DNT(Do Not Track) 헤더가 1이면 전송 안 함.
 *   - file://, localhost, 127.0.0.1, *.test 도메인이면 전송 안 함.
 *
 * 개인정보:
 *   - IP·이메일·이름 등 PII 없음. visitor_id는 무작위 UUID.
 *   - 자세한 정책: /privacy/
 */
(function () {
  'use strict';

  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  // ─── 옵트아웃 / 개발 환경 ───
  try {
    if (navigator.doNotTrack === '1' || window.doNotTrack === '1') return;
    if (localStorage.getItem('qlens_no_track') === '1') return;
    // 관리자 본인 트래픽 차단 (마이페이지에서 me.is_admin 시 셋. 서버측에서도 한 번 더 거름)
    if (localStorage.getItem('qlens_admin') === '1') return;
  } catch (e) { /* private mode 등은 그대로 진행 */ }

  var host = location.hostname || '';
  if (!host || host === 'localhost' || host === '127.0.0.1' || /\.local$|\.test$/i.test(host)) return;
  if (location.protocol === 'file:') return;

  var API = 'https://api.q-bot.kr/track';
  var COOKIE_NAME = 'qlens_vid';
  var COOKIE_MAX_AGE = 60 * 60 * 24 * 365;       // 365일
  var SESSION_KEY = 'qlens_sid';
  var SESSION_TS_KEY = 'qlens_sid_ts';
  var SESSION_IDLE_MS = 30 * 60 * 1000;          // 30분 idle 후 재발급

  function uuid() {
    if (crypto && typeof crypto.randomUUID === 'function') return crypto.randomUUID();
    // RFC4122 v4 폴백
    var b = new Uint8Array(16);
    crypto.getRandomValues(b);
    b[6] = (b[6] & 0x0f) | 0x40;
    b[8] = (b[8] & 0x3f) | 0x80;
    var hex = '';
    for (var i = 0; i < 16; i++) hex += (b[i] + 0x100).toString(16).slice(1);
    return hex.slice(0, 8) + '-' + hex.slice(8, 12) + '-' + hex.slice(12, 16) + '-' + hex.slice(16, 20) + '-' + hex.slice(20);
  }

  function readCookie(name) {
    var m = document.cookie.match(new RegExp('(?:^|;\\s*)' + name + '=([^;]+)'));
    return m ? decodeURIComponent(m[1]) : null;
  }

  function writeCookie(name, value, maxAge) {
    var attrs = '; Max-Age=' + maxAge + '; Path=/; SameSite=Lax';
    if (location.protocol === 'https:') attrs += '; Secure';
    document.cookie = name + '=' + encodeURIComponent(value) + attrs;
  }

  function getVisitorId() {
    var v = readCookie(COOKIE_NAME);
    if (v && /^[0-9a-f-]{32,40}$/i.test(v)) return v;
    v = uuid();
    writeCookie(COOKIE_NAME, v, COOKIE_MAX_AGE);
    return v;
  }

  function getSessionId() {
    try {
      var now = Date.now();
      var sid = sessionStorage.getItem(SESSION_KEY);
      var ts = parseInt(sessionStorage.getItem(SESSION_TS_KEY) || '0', 10);
      if (!sid || !ts || now - ts > SESSION_IDLE_MS) {
        sid = uuid();
      }
      sessionStorage.setItem(SESSION_KEY, sid);
      sessionStorage.setItem(SESSION_TS_KEY, String(now));
      return sid;
    } catch (e) {
      // private mode → 페이지 단발성 ID
      return uuid();
    }
  }

  function getAccessToken() {
    try { return sessionStorage.getItem('qlens_access_token'); }
    catch (e) { return null; }
  }

  function send() {
    var path = location.pathname || '/';
    if (path.length > 256) path = path.slice(0, 256);

    var payload = {
      path: path,
      referrer: document.referrer || '',
      visitor_id: getVisitorId(),
      session_id: getSessionId()
    };

    var token = getAccessToken();
    var bodyStr = JSON.stringify(payload);

    // 로그인 토큰이 없으면 sendBeacon 우선 (Authorization 헤더 불가 — 토큰 없을 때만 적용)
    if (!token && navigator.sendBeacon) {
      try {
        var blob = new Blob([bodyStr], { type: 'application/json' });
        if (navigator.sendBeacon(API, blob)) return;
      } catch (e) { /* fallthrough */ }
    }

    try {
      var headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = 'Bearer ' + token;
      fetch(API, {
        method: 'POST',
        headers: headers,
        credentials: 'omit',
        keepalive: true,
        body: bodyStr
      }).catch(function () { /* swallow */ });
    } catch (e) { /* swallow */ }
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(send, 0);
  } else {
    document.addEventListener('DOMContentLoaded', send, { once: true });
  }
})();
