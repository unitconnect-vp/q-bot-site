// HS256 JWT — access_token 발급·검증
// access_token: 15분 짧은 수명. 만료 시 refresh_token으로 재발급.

const enc = new TextEncoder();
const dec = new TextDecoder();

function base64UrlEncode(bytes) {
  let binary = '';
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function base64UrlDecode(str) {
  let s = str.replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  const binary = atob(s);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function getKey(secret) {
  return crypto.subtle.importKey(
    'raw', enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false, ['sign', 'verify']
  );
}

export async function signJWT(payload, secret, expiresInSec = 900) {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: 'HS256', typ: 'JWT' };
  const fullPayload = { ...payload, iat: now, exp: now + expiresInSec };
  const headerB64 = base64UrlEncode(enc.encode(JSON.stringify(header)));
  const payloadB64 = base64UrlEncode(enc.encode(JSON.stringify(fullPayload)));
  const data = `${headerB64}.${payloadB64}`;
  const key = await getKey(secret);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(data));
  const sigB64 = base64UrlEncode(new Uint8Array(sig));
  return `${data}.${sigB64}`;
}

export async function verifyJWT(token, secret) {
  if (!token) return null;
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const [headerB64, payloadB64, sigB64] = parts;
  const data = `${headerB64}.${payloadB64}`;
  const key = await getKey(secret);
  const sig = base64UrlDecode(sigB64);
  const valid = await crypto.subtle.verify('HMAC', key, sig, enc.encode(data));
  if (!valid) return null;
  let payload;
  try {
    payload = JSON.parse(dec.decode(base64UrlDecode(payloadB64)));
  } catch {
    return null;
  }
  if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null;
  return payload;
}
