// PBKDF2-SHA256 비밀번호 해싱 (Workers Web Crypto 네이티브)
// bcrypt가 Workers에서 호환·성능 이슈가 있어 Web Crypto 표준 사용.

const ITERATIONS = 100_000;
const KEY_LENGTH = 32;
const SALT_LENGTH = 16;

const enc = new TextEncoder();

function bytesToBase64(bytes) {
  let binary = '';
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary);
}

function base64ToBytes(b64) {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

// 비밀번호 → 저장용 해시 문자열
// 형식: pbkdf2-sha256$<iterations>$<saltB64>$<hashB64>
export async function hashPassword(password) {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_LENGTH));
  const keyMaterial = await crypto.subtle.importKey(
    'raw', enc.encode(password), { name: 'PBKDF2' }, false, ['deriveBits']
  );
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations: ITERATIONS, hash: 'SHA-256' },
    keyMaterial, KEY_LENGTH * 8
  );
  const hash = new Uint8Array(bits);
  return `pbkdf2-sha256$${ITERATIONS}$${bytesToBase64(salt)}$${bytesToBase64(hash)}`;
}

// 비밀번호 검증 (상수 시간 비교)
export async function verifyPassword(password, stored) {
  if (!stored || !stored.startsWith('pbkdf2-sha256$')) return false;
  const [, iterStr, saltB64, hashB64] = stored.split('$');
  const iterations = parseInt(iterStr, 10);
  const salt = base64ToBytes(saltB64);
  const expected = base64ToBytes(hashB64);
  const keyMaterial = await crypto.subtle.importKey(
    'raw', enc.encode(password), { name: 'PBKDF2' }, false, ['deriveBits']
  );
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt, iterations, hash: 'SHA-256' },
    keyMaterial, expected.length * 8
  );
  const actual = new Uint8Array(bits);
  if (actual.length !== expected.length) return false;
  let diff = 0;
  for (let i = 0; i < actual.length; i++) diff |= actual[i] ^ expected[i];
  return diff === 0;
}

// SHA-256 해시 (refresh token 검증용 — salt 불필요한 이미 랜덤한 secret용)
export async function hashToken(token) {
  const digest = await crypto.subtle.digest('SHA-256', enc.encode(token));
  return bytesToBase64(new Uint8Array(digest));
}

// URL-safe 랜덤 토큰 생성 (이메일 인증 토큰·refresh token·OAuth state 등)
export function generateToken(byteLength = 32) {
  const bytes = crypto.getRandomValues(new Uint8Array(byteLength));
  return bytesToBase64(bytes)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}
