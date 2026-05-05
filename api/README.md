# Q렌즈 v2.0 인증 API — 셋업 가이드

Cloudflare Workers + D1 기반 인증·세션 API. `q-bot.kr/api/*` 경로로 라우팅.

---

## 폴더 구조

```
api/
├── wrangler.toml           # Worker 설정 (D1 binding, vars, routes 주석)
├── package.json            # wrangler 스크립트
├── migrations/
│   └── 0001_init.sql       # D1 스키마 (users, game_records, game_states, auth_tokens, sessions)
└── src/
    ├── index.js            # 라우터 + 8개 엔드포인트
    └── lib/
        ├── crypto.js       # PBKDF2 비밀번호 해싱
        ├── jwt.js          # HS256 JWT
        ├── google.js       # Google OAuth
        └── email.js        # Resend (stub 동작 가능)
```

---

## 셋업 순서

### 1. 프로젝트 위치

기존 `q-bot-site` repo 안 `/api` 폴더에 그대로 두는 모노레포 권장.

```bash
cd /path/to/q-bot-site
# 받은 파일들을 ./api/ 하위에 그대로 복사
cd api
```

### 2. 의존성 설치

```bash
npm install
```

### 3. Wrangler 로그인 (이미 했으면 생략)

```bash
npx wrangler login
```

### 4. Secrets 등록 (3개)

#### 4-1. JWT_SECRET 생성·등록

```bash
# 안전한 랜덤 32바이트 base64 생성
openssl rand -base64 32

# 위 출력값을 복사해서 등록
npx wrangler secret put JWT_SECRET
# (프롬프트가 뜨면 위 값 붙여넣고 Enter)
```

#### 4-2. GOOGLE_CLIENT_SECRET 등록

```bash
npx wrangler secret put GOOGLE_CLIENT_SECRET
# (Google Cloud Console에서 발급받은 클라이언트 보안 비밀번호 붙여넣기)
```

#### 4-3. RESEND_API_KEY 등록 (옵션)

Resend 가입 전엔 생략 가능. 미등록 시 이메일은 콘솔 로그로만 출력됨 (개발 단계 OK, 운영 전 등록 필수).

```bash
npx wrangler secret put RESEND_API_KEY
```

### 5. D1 스키마 적용

```bash
npm run db:migrate
# === wrangler d1 execute qlens-db --remote --file=migrations/0001_init.sql
```

성공 시 `Executed N commands` 출력. 확인:

```bash
npm run db:console -- "SELECT name FROM sqlite_master WHERE type='table'"
# users, game_records, game_states, auth_tokens, sessions 5개 테이블 출력
```

### 6. 배포

```bash
npm run deploy
# === wrangler deploy
```

성공 시 `Published qlens-api` + `https://qlens-api.heyqbot.workers.dev` 출력.

### 7. Routes 설정 (q-bot.kr/api/* → Worker 연결)

Cloudflare 대시보드:
1. **Workers & Pages** → **qlens-api** 클릭
2. **Settings** → **Triggers** 탭 → **Routes** 섹션
3. **Add route**:
   - Pattern: `q-bot.kr/api/*`
   - Zone: `q-bot.kr`
4. Save

설정 후 1~2분 내 활성화. 확인:

```bash
curl -i https://q-bot.kr/api/me
# HTTP/1.1 401 Unauthorized + {"error":"Unauthorized"} 가 돌아오면 성공 (인증 안 했으니 401이 정상)
```

---

## 동작 테스트

### 회원가입

```bash
curl -X POST https://q-bot.kr/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","nickname":"테스터"}'
```

성공 시: `{"ok":true,"message":"인증 메일을 발송했습니다..."}`

`wrangler tail`을 다른 터미널에서 띄워두면 이메일 stub 출력이 보입니다 (RESEND_API_KEY 미등록 시).

```bash
npm run tail
```

콘솔 로그에 인증 URL이 찍히면 그 URL을 브라우저에 붙여 인증 완료 → DB의 `users.email_verified` = 1 변경 확인.

### 로그인

```bash
curl -X POST https://q-bot.kr/api/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

성공 시: `{"access_token":"eyJ...","expires_in":900,"user":{...}}` + cookies.txt에 `refresh_token` 저장.

### /me 호출

```bash
curl https://q-bot.kr/api/me \
  -H "Authorization: Bearer <access_token>"
```

### Google OAuth 로그인 (브라우저)

`https://q-bot.kr/api/auth/google` 접속 → Google 동의 화면 → 콜백 → `https://q-bot.kr/auth/callback#access_token=...` 로 리다이렉트.

> **사이트 측 작업 필요:** `/auth/callback` 페이지에서 URL fragment(`#access_token=...`)를 파싱해 sessionStorage·메모리에 저장하고 메인으로 이동. 그리고 `/auth/verified` 페이지(이메일 인증 완료) 안내 페이지. 이 두 페이지는 다음 턴에 PO·지수가 정적 HTML로 추가합니다.

---

## 엔드포인트 명세

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/api/auth/signup` | `{email, password, nickname}` → 인증 메일 발송 |
| GET | `/api/auth/verify-email?token=…` | 이메일 인증 → `/auth/verified` 리다이렉트 |
| POST | `/api/auth/login` | `{email, password}` → access_token + refresh cookie |
| GET | `/api/auth/google` | Google 동의 화면 리다이렉트 |
| GET | `/api/auth/google/callback?code=…&state=…` | 토큰 교환 → `/auth/callback#access_token=…` 리다이렉트 |
| POST | `/api/auth/refresh` | refresh cookie → 새 access_token |
| POST | `/api/auth/logout` | 세션 삭제 + cookie 클리어 |
| GET | `/api/me` | Authorization 헤더 → 현재 사용자 정보 |

토큰 정책:
- access_token: 15분, JSON 응답, `Authorization: Bearer …`로 전달
- refresh_token: 30일, HTTP-only Secure SameSite=Lax cookie, D1 sessions 테이블에 SHA-256 해시 저장

---

## 다음 단계 (Phase 1.5 / Phase 2)

- 비밀번호 재설정 (`/api/auth/forgot-password`, `/reset-password`)
- 닉네임 변경·계정 삭제 엔드포인트
- 게임 기록 API (`/api/games/:type/record`, `/api/games/:type/leaderboard`)
- 커뮤니티 API (Phase 2)
- Rate limiting (Cloudflare Rate Limiting Rules — 브루트포스 방지)
- 이메일 발송 큐 (Cloudflare Queues — 회원가입 응답 속도 개선)

---

## 트러블슈팅

**`wrangler d1 execute` 가 `database not found` 에러:**
- `wrangler.toml`의 `database_id`가 정확한지 확인 (`9fee7d6a-47cc-4198-88b9-29c97d16465d`)
- Cloudflare Account가 같은지 확인 (`wrangler whoami`)

**배포 후 `q-bot.kr/api/...` 가 GitHub Pages 404를 반환:**
- Routes 설정이 안 됐거나 1~2분 대기 필요
- `qlens-api.heyqbot.workers.dev/api/...`로 직접 호출하면 동작하는지 먼저 확인

**Google OAuth 콜백에서 `redirect_uri_mismatch`:**
- Google Cloud Console의 승인된 리디렉션 URI가 정확히 `https://q-bot.kr/api/auth/google/callback`인지 확인 (트레일링 슬래시 X)

**`Invalid OAuth state`:**
- 콜백까지 시간이 길어 cookie가 만료됐거나 (10분 제한), 다른 브라우저·시크릿창 등 cookie 분리 환경
