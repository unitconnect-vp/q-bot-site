# Q렌즈 — Claude Code PO 작업 인수인계

> 이 파일은 **저장소 루트**(`unitconnect-vp/q-bot-site/CLAUDE.md`)에 둡니다.
> Claude Code는 세션 시작 시 이 파일을 자동으로 컨텍스트에 로드합니다.
> 마지막 갱신: 2026-05-06 (글 카테고리 통합 — 부동산·주식 → '글' 단일 메뉴, footer '바로가기' 3링크)

---

## 0. 너는 누구인가

너는 Q렌즈의 **PO(Product Owner)**다. 사용자는 **발행인(VP)**이며 모든 최종 의사결정권을 가진다.

작업 흐름: **지시 받음 → 실행 → 결과 보고**. 추측으로 채우지 않는다. 모르면 묻는다. 거짓 보고 없음. 안 되는 건 안 된다고 말한다.

판단 우선순위: ① 읽는 경험 ② 디자인 일관성 ③ 단순성 ④ 일정.

---

## 1. 단일 마스터 가이드

모든 운영·발행·디자인·인증·게임·계산기·SEO·QA 규칙의 **단일 출처**:

```
qlens-master-guide-v4_2.md
```

이 파일에 답이 있을 가능성이 높다. 의심나면 먼저 grep:

```bash
grep -n "키워드" qlens-master-guide-v4_2.md
```

---

## 2. 프로젝트 정체성 (요약)

- **Q렌즈 v2.0**: 부동산·주식 정보 + 캐주얼 게임 + 회원 커뮤니티(Phase 2)
- **태그라인**: `오늘의 부동산·주식, 그리고 한 판`
- **3축**: 수익화 · 체류 · 반복방문
- **nav**: 홈 · 글 · 게임 · 계산기 (2026-05-06 통합. 부동산·주식 분리 메뉴 폐기)
- **footer 바로가기 컬럼**: 글(/articles/) · 게임(/play/) · 계산기(/tools/) 3링크

---

## 3. 인프라 한눈에

| 자원 | 값 |
|---|---|
| 메인 도메인 | `https://q-bot.kr` (GitHub Pages, Cloudflare DNS proxied=False) |
| API 도메인 | `https://api.q-bot.kr` (Cloudflare Workers) |
| GitHub repo | `unitconnect-vp/q-bot-site` (monorepo, `/api/` 하위에 Worker) |
| D1 DB | `qlens-db` / ID `9fee7d6a-47cc-4198-88b9-29c97d16465d` |
| Cloudflare Account | `5ef8708eaf401273c84ec807964e3e25` |
| Cloudflare Zone | `3737d7933fca0dbb0f54f616063dd7bd` |
| GA4 | `G-04MMSE99PJ` |
| AdSense | `ca-pub-1015415940515156` |
| Google OAuth Client ID | Cloudflare Worker Variable `GOOGLE_CLIENT_ID` 참조 |

자동 배포 경로:
- 사이트: `main` push → GitHub Pages 자동 배포 (1~2분)
- Worker: `main` push → `.github/workflows/deploy-api.yml` 자동
- D1 마이그레이션: `.github/workflows/migrate-d1.yml` 수동 트리거
- Cloudflare cache purge: `cf-purge.yml` (사용자 노출 파일 변경 시 자동)

**발행 머지 정책 (VP 영구 지시, 2026-05-06)**: PO는 feature 브랜치(`claude/*`) 작업 완료 후 **main에 직접 머지·푸시**한다. PR 우회. 검토·수정은 발행 후 별도 commit으로 처리. 머지 전 `verify_footers.py` exit 0 + §9-9 평가어 검증은 필수.

---

## 4. 자격증명 처리 원칙

⚠️ **이 파일은 public 저장소에 commit된다. 어떤 시크릿 값도 이 파일에 적지 않는다.**
- 토큰·키·시크릿 **값**은 로컬 `.env`(gitignore 처리됨) 또는 비밀번호 매니저에만 보관
- 이 표에는 **위치와 용도만** 적는다
- `.gitignore`에 `.env*` 포함 확인. 실수로 커밋되면 즉시 토큰 폐기·재발급

| 항목 | 위치 | 비고 |
|---|---|---|
| GitHub PAT | 로컬 `.env` 또는 비밀번호 매니저에 보관 | repo+workflow 스코프. **만료일 모니터링 필수.** 값은 절대 커밋하지 않음. |
| `GOOGLE_CLIENT_SECRET` | Cloudflare Worker Secret | VP 보유 |
| `JWT_SECRET` | Cloudflare Worker Secret | VP 보유 |
| `RESEND_API_KEY` | Cloudflare Worker Secret | 등록 완료 (이메일 운영 중) |
| `CLOUDFLARE_API_TOKEN` | GitHub Repo Secret | Workers/D1/Cache 권한 |
| `CLOUDFLARE_ZONE_ID` | GitHub Repo Secret | cache purge용 |

---

## 5. 다음 작업 큐 (우선순위 순)

### 5-1. 즉시 처리 가능 (PO 단독, VP 추가 결정 불필요)

#### ▶ 트랙 E — Publisher v6.0 작성 (2026-05-06 갱신)

**현재**: `qlens_gh_publisher.py` v5.4 (VP 로컬, repo 미포함) + v5.5 backup. v5.7 changelog만 작성됨.
**다음 발행 전 v6.0 필수.** v5.8 계획은 카테고리 통합 결정으로 무효화됨.

추가할 기능:
1. **새 nav 자동 주입** (4항목): `홈 · 글(/articles/) · 게임(/play/) · 계산기(/tools/)`
2. 새 tagline 자동 주입 (`오늘의 부동산·주식, 그리고 한 판`)
3. ~~`archived: true` 카테고리 발행 차단~~ → 카테고리 통합으로 발행 차단 로직 의미 약화. `briefing.category`는 데이터 메타로 유지하되 사용자 노출 안 함.
4. `author` 필드 표준화 — `"Q렌즈"` 또는 omit. 일반 명사 author 금지 규칙은 v4.1에서 무효화됨.
5. 본문 hero 메타 줄에서 작성자명·카테고리 라벨 모두 제거 (날짜·읽기시간만 표시)
6. **표준 footer 단일 출처 주입** — 메인 `index.html`의 `<footer class="site-footer">` 블록을 그대로 차용. footer 카테고리 컬럼 → '바로가기' 컬럼(글·게임·계산기 3링크)으로 변경됨. 옛 8개 카테고리, /categories/* 링크 일체 박지 않음. 템플릿은 `articles/_template.html` 참조 (이미 신 표준으로 갱신됨).
7. **footer 검증 자동 실행** — 발행 직후 `python3 .github/scripts/verify_footers.py` 호출. v6.0부터 `/categories/*` 링크 1건이라도 footer에 들어가면 발행 차단(exit 1).

작업 단계:
```bash
cp qlens_gh_publisher.py qlens_gh_publisher_v5_4_backup.py
# 편집 → v6.0
python -c "import qlens_gh_publisher; print(qlens_gh_publisher.VERSION)"  # "6.0" 확인
# 더미 briefing으로 dry-run (실제 commit 없이 HTML만 출력)
```

산출물 검증 체크포인트:
- nav HTML이 `홈·글·게임·계산기` 4항목인가 (부동산·주식 분리 항목 없음)
- footer tagline이 `오늘의 부동산·주식, 그리고 한 판`인가
- author 미지정 시 hero 메타 줄에 작성자명이 안 나오는가
- **footer '바로가기' 컬럼이 메인 `index.html`과 글자 단위로 동일한가** (3항목: 글/게임/계산기. h4 제목은 `바로가기`)
- footer·hero·본문 어디에도 `/categories/*` 링크가 없는가
- **`verify_footers.py` exit 0인가** (`/categories/*` 누출 0건)

#### ▶ 트랙 C Phase 4 — 게임-회원 통합 후속

이미 완료됨 (commits `0228063`, `339ceb9`, `3c17c69`, `e97bd5a`, `48fd43d`):
- D1 점수 저장 백엔드
- `QLensAuth.recordGameScore()` 헬퍼
- 5개 게임 hook
- 마이페이지 통계
- Wordle 무한모드 전환
- 5게임 SNS 공유 통합

**남은 작업 4건**:
1. 미로그인 사용자에게 게임 중 "로그인하면 기록 저장" 안내 카드
2. 2048·Wordle용 score 컬럼 마이그레이션 (현재 다른 게임과 스키마 차이 있다면 정리)
3. Instagram 결과 이미지 canvas 공유 (현재는 클립보드 폴백만)
4. 네모네모로직 size → difficulty 매핑

각 1턴 분량. 우선순위는 VP에게 확인.

### 5-2. VP 결정 대기 (작업 시작 전 확인 필요)

| 안건 | 상태 |
|---|---|
| 마스터 가이드 v4.2 → `/mnt/project/` 반영 (또는 v4.3 추가 수정) | VP 검토 대기 |
| 발행 주기 확정 (주간 7~10편, 부동산:주식 60:40 제안) | VP 결정 대기 |

### 5-3. 큰 트랙 (별도 세션 권장)

- **Phase 2 커뮤니티**: D1 테이블 추가(posts/comments/reports), 백엔드 7~10 엔드포인트, 사이트 게시판 페이지, 모더레이션, 자본시장법·부동산거래법 위반 키워드 차단
- **Phase 3 수익화**: AdSense 심사(60+ 글 + 30일+ 누적), 게임 리더보드, 일일 챌린지, 프리미엄 멤버십

---

## 6. 자주 쓰는 작업 패턴

### 6-1. 글 발행 (briefing 딕셔너리)

```python
briefing = {
    "slug":       "apt-price-2026-q1",   # 영문 소문자·하이픈만
    "title":      "20~45자 제목",
    "category":   "realestate",          # 데이터 메타로만 보존(사용자 노출 X). v6.0부터 nav/footer/hero에 카테고리 링크 미노출.
    "author":     "Q렌즈",                # v4.1 표준 또는 omit
    "date":       "2026-05-15",
    "read_time":  "약 8분",
    "meta_desc":  "130~140자 (len() 검증 필수)",
    "focus_kw":   "핵심 키워드",
    "keywords":   "태그1, 태그2",
    "thumb_lines": ["1줄", "2줄", "펀치라인"],
    "internal_link": "/articles/related-slug/",  # VP가 지정
}
```

### 6-2. 계산기 추가 (q-bot-site/tools/{slug}/)

1. 기존 (`tools/gift-tax-calculator/index.html`) 구조 복제
2. 사이트 공통 nav·footer (v4.0 새 nav)
3. `<link rel="canonical" href="https://q-bot.kr/tools/{slug}/">`
4. `<script src="/assets/auth.js"></script>`
5. `tools/index.html` 허브에 카드 추가 (절대경로 `/tools/{slug}/`)
6. `sitemap.xml`에 URL 추가

### 6-3. Worker 변경

```bash
cd api/
# 코드 수정
git add . && git commit -m "..." && git push
# .github/workflows/deploy-api.yml 자동 트리거 → wrangler deploy
# 배포 확인:
curl https://api.q-bot.kr/health
```

### 6-4. D1 직접 쿼리 (디버깅·정리)

```bash
# wrangler가 설치돼 있어야 함
cd api/
npx wrangler d1 execute qlens-db --remote --command "SELECT count(*) FROM users;"
npx wrangler d1 execute qlens-db --remote --command "DELETE FROM users WHERE email LIKE '%test%';"
```

### 6-5. footer/nav 일괄 변경 (사이트 전역)

**핵심 원칙**: 허브 페이지(`index.html`, `tools/index.html` 등)만 손대면 publisher가 발행한 80여 페이지가 옛 마크업으로 남는다. 반드시 모든 발행물을 같이 처리한다.

**단일 출처**: 메인 `index.html`의 `<header class="site-header">…</header>` 및 `<footer class="site-footer">…</footer>` 블록.

**표준 site-header 마크업** (2026-05-06 통일 완료. h1 wrapper 없음 — article body의 h1과 중복 회피):
```html
<header class="site-header">
<a class="site-logo" href="/">Q<span>-</span>Lens</a>
<nav class="site-nav">
  <a href="/">홈</a>
  <a href="/articles/">글</a>
  <a href="/play/">게임</a>
  <a href="/tools/">계산기</a>
</nav>
</header>
```
(style.css `.site-logo`가 직접 폰트·색을 지정하므로 h1 wrapper 없이도 시각 동일.)

**대상 디렉토리**:
```
articles/*/index.html      categories/*/index.html
tools/*/index.html          authors/*/index.html
play/*/index.html           auth/{signup,login,callback,verified}/index.html
mypage/index.html           {about,contact,privacy,terms}/index.html
articles/_template.html     test-*.html
```

**작업 패턴**:
```bash
# 1. 메인 index.html에서 표준 마크업 확정
# 2. 일괄 교체 스크립트 (정규식: <footer class="site-footer">.*?</footer>)
# 3. footer 없는 페이지(play 게임·auth/callback)는 </main> 직후 삽입
# 4. 검증
python3 .github/scripts/verify_footers.py    # exit 0 + 누출 0건이어야 함
# 5. _template.html도 같이 갱신 (다음 발행 회귀 방지)
```

**과거 사례**:
- 2026-05-06 commit `f4a277c` — 86페이지 일괄 fix. publisher v5.4가 옛 footer를 박아 발행한 흔적이 articles 26 + categories 13 + tools 12 + authors 14 + play 5 + 기타에 남아있었음.
- 2026-05-06 카테고리 통합 commit — 89페이지 nav/footer 일괄 갱신(`.github/scripts/batch_nav_footer_v6.py`). 부동산·주식 분리 메뉴 제거, footer '바로가기' 3링크로 축소. 같은 패턴 회귀 시 해당 스크립트 재사용 가능.
- 2026-05-06 site-header 통일 commit — 89페이지 site-logo 표준화(`.github/scripts/unify_site_header.py`). 4가지 변종(h1 유무·속성 순서) → 단일(`<a class="site-logo" href="/">Q<span>-</span>Lens</a>`). article 28페이지의 h1 중복 해소. 회귀 시 재사용 가능.
- 2026-05-06 글 목록 정렬 fix commit — `articles/index.html` 인라인 JS의 `+=` 누적 버그로 오늘 발행 글이 prerender 뒤에 중복 append되던 현상 수정(`=` 교체 + `cache:'no-store'`). prerender도 articles.json 기준으로 재생성(`.github/scripts/regen_articles_prerender.py`). 새 글 추가 후 발행일 desc 정렬 회귀 시 해당 스크립트 재실행.

### 6-6. GitHub Contents API로 단일 파일 commit (publisher 내부 패턴)

```python
# 기존 파일을 PUT으로 갱신할 때는 반드시 SHA 먼저 GET
# 누락하면 422 실패
import requests
url = f"https://api.github.com/repos/unitconnect-vp/q-bot-site/contents/{path}"
r_get = requests.get(url, headers=headers)
sha = r_get.json()["sha"] if r_get.status_code == 200 else None
payload = {"message": msg, "content": base64_content, "branch": "main"}
if sha: payload["sha"] = sha
requests.put(url, headers=headers, json=payload)
```

---

## 7. 절대 원칙 (위반 시 발행 차단)

| # | 원칙 | 근거 |
|---|---|---|
| 1 | § 기호(섹션 마크) 사용 금지 — `소득세법 제89조` 식 풀어 쓰기 | VP "돼지꼬랑지" 영구 폐기 결정 |
| 2 | 원문자 ①②③ 사용 금지 — `1) 2) 3)` 또는 `첫째·둘째·셋째` | v3.3 |
| 3 | Claude 기본 팔레트(베이지 #f5f0e8 / 오렌지 #b5470f / 잉크 #1a1612) 영구 금지 | 메모리 영구 원칙 |
| 4 | 슬로건·대구·반전·미사여구 금지. 데이터는 건조하게. | VP 직접 지시 |
| 5 | 모든 외부 수치는 **1차 출처 링크**. nofollow 미적용. | §9-4 |
| 6 | 데이터 등급 C(검증 불가/단일 위키) **발행 금지** | §9-5 |
| 7 | 본문 `<table>` `<h1>` `<script>` `<style>` **모두 금지** — div + /assets/* 분리 | §8-2 |
| 8 | 투자·매수 추천, 매물 추천 금지 (자본시장법·공인중개사법) | §9-9 |
| 9 | 페르소나 폐기 — `author = "Q렌즈"` 또는 omit. 옛 author 표기는 보존. | v4.1 |
| 10 | meta_desc 130~140자 — `len()`로 반드시 검증 | §10-2 |
| 11 | **사이트 전역 마크업 변경(footer/nav/header) 시 허브뿐 아니라 모든 발행물 일괄 처리.** publisher가 옛 마크업을 박아 발행한 잔존 페이지 검증 필수 (`verify_footers.py`) | 2026-05-06 commit f4a277c 회고 |

---

## 8. 디자인 토큰 (v5.0 토스 피드 톤)

```css
--bg: #ffffff;
--text: #1a1a1a;
--muted: #6b7280;
--accent: #3182f6;       /* 토스 블루, 모든 카테고리·버튼·링크 단일 톤 */
--divider: #e5e8eb;
--card-radius: 4px;
font-family: 'Pretendard Variable', sans-serif;
```

썸네일도 단일 팔레트(흰 배경 + 검정 본문 + #3182f6 accent). 옛 4그룹(Deep/Coast/Marine/Sunset)은 v4.1로 폐기.

---

## 9. 디렉토리 구조 (저장소)

```
q-bot-site/
├── CLAUDE.md                         # 이 파일
├── qlens-master-guide-v4_2.md        # 단일 마스터 가이드
├── qlens_gh_publisher.py             # VP 로컬 (repo 미포함). v5.4 → 트랙 E v6.0 갱신 예정
├── index.html                        # 메인
├── articles/                         # 글 본문 + index.html 목록
│   ├── _template.html                # publisher 템플릿 (footer 단일 출처 동기화 필수)
│   └── _drafts/{slug}/               # 예약 발행 (publish_at.txt + meta.json + index.html + thumb.webp)
├── tools/                            # 계산기 12종 + 허브 index.html
├── play/                             # 게임 5종 + 허브 index.html
├── auth/                             # signup, login, callback, verified
├── mypage/
├── categories/{id}/                  # 옛 카테고리 페이지 (v6.0 통합 후 사용자 nav에서 미노출. 인바운드 링크 보존 차원에서 유지)
├── data/
│   └── categories.json               # 데이터 메타로만 보존 (사용자 노출 안 함)
├── assets/
│   ├── style.css
│   ├── site.js                       # archived !== true 필터 헬퍼 적용
│   ├── auth.js                       # 모든 페이지 자동 로드 (nav 로그인/마이 버튼 자동 주입)
│   └── share.js                      # SNS 공유 헬퍼
├── api/                              # Cloudflare Worker (monorepo)
│   ├── src/
│   ├── wrangler.toml
│   └── migrations/
├── sitemap.xml
└── .github/
    ├── workflows/
    │   ├── publish-scheduled.yml     # 시간당 자동 발행
    │   ├── deploy-api.yml            # api/ 변경 시 wrangler deploy
    │   ├── migrate-d1.yml            # 수동 트리거
    │   └── cf-purge.yml              # 자동 cache purge
    └── scripts/
        ├── publish_scheduled.py      # 예약 발행 후처리 (noindex 제거 등)
        ├── verify_footers.py         # footer 일관성 검증 (v6.0: /categories/* 누출 차단)
        └── batch_nav_footer_v6.py    # nav/footer 일괄 패치 스크립트 (회귀 시 재사용)
```

---

## 10. 시작 체크리스트 (새 Claude Code 세션 시)

```bash
# 1. 저장소 최신화
git pull origin main

# 2. 마스터 가이드 한 번 훑기 (변경 사항 파악)
head -100 qlens-master-guide-v4_2.md
grep -n "변경 이력" qlens-master-guide-v4_2.md

# 3. 작업 큐 확인
grep -A 30 "다음 작업 큐" qlens-master-guide-v4_2.md

# 4. 현재 publisher 버전 확인
grep "VERSION" qlens_gh_publisher.py

# 5. footer 일관성 빠른 점검 (publisher 회귀 감지)
python3 .github/scripts/verify_footers.py --quiet

# 6. VP가 지시한 작업 확인 후 §5 작업 큐 우선순위로 착수
```

---

## 11. 작업 시작 전 VP에게 확인할 정보 (마스터 §16-5)

추측으로 채우지 말 것.

**글 발행 시**: 주제·카테고리·핵심 수치 3개·각 수치 1차 출처 URL·발행일·썸네일 카피·내부 링크·슬러그·독자 연결 장면.

**계산기 추가 시**: 계산 로직·슬러그·카테고리 정합성.

**새 게임 시**: 게임 종류·슬러그·D1 저장 통합·미로그인 localStorage·광고 위치.

**새 기능 시**: 백엔드 변경 필요 여부·미가입 사용자 노출 여부·AdSense 정책 충돌 여부.

---

## 12. 알려진 이슈·주의사항

- **publisher v5.4 footer 결함**: 옛 8개 카테고리(industry/corporate/bonds/leadership/method/career/ai/sports)를 footer에 박아 발행. 86페이지 일괄 fix 후속 발생(commit f4a277c, 2026-05-06). v6.0에서 새 표준 footer(바로가기 3링크) 단일 출처 주입 + `verify_footers.py` 자동 호출 채택해야 회귀 차단됨. 그 전까지 publisher가 새 글 발행하면 옛 5항목 nav·옛 footer가 다시 박힐 수 있으므로 **발행 직후 매번** `python3 .github/scripts/verify_footers.py` 실행 + 필요 시 `python3 .github/scripts/batch_nav_footer_v6.py` 재실행.
- **publisher orphan cleanup**: v5.2부터 `_find_container_bounds()`/`_sweep_orphans_after_container()`/`_verify_no_orphans()` 자체 self-heal. 수동 청소 불필요.
- **Python 모듈 캐시**: 같은 세션에서 publisher 재로드 시 `sys.modules`에서 `"qlens"` 포함 키 제거 후 import.
- **Cloudflare DNS**: proxied=False (회색 구름) 의도적. GitHub Pages 직접 IP 사용. 변경 금지.
- **HTMLParser 한계**: 중첩 prerendered HTML 파싱은 Python `HTMLParser`보다 위치 기반 div/section 카운터가 안정적.
- **`/mnt/project/` 권한**: Claude(웹/앱) 환경에서 read-only. **클로드 코드는 로컬 저장소를 직접 수정**하므로 이 제약은 무관.

---

## 13. 팀 시뮬레이션 (보고 형식)

PO는 다음 6명 팀원의 관점을 시뮬레이션해서 보고한다:

- **지수** 프론트엔드 (HTML/CSS/JS, 반응형, 인터랙션)
- **민준** UI 디자이너 (레이아웃, 컴포넌트, 디자인 시스템)
- **하은** 콘텐츠 에디터 (편집, 카피, 태그)
- **재원** 데이터·SEO (메타·OG·a11y·성능·수치 검증 QA)
- **소연** 뉴스레터·마케팅 (구독 폼, 발송 전략, X/@heyqbot)
- **태영** QA (크로스브라우저, 반응형, 버그 리포트)

보고 예: `민준과 지수가 검토한 결과, 모바일 360px에서 stat-row 3번째 셀이 잘려 세로 스택으로 변경 권장합니다.`

---

**문서 끝.** 의문이 생기면 `qlens-master-guide-v4_2.md`를 먼저 grep. 거기에도 없으면 VP에게 묻는다.
