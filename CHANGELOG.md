# Q-Lens CHANGELOG

Q렌즈 사이트의 버전별 변경 기록입니다. 발행 가이드(Writing Guide) 버전과는 별개이며, 사이트 UI/인프라/기능 단위의 릴리스를 추적합니다.

버전 체계:
- **Major (X.0)** — 전면 리디자인 또는 구조적 변경
- **Minor (X.Y)** — 기능 추가, UI 섹션 개편, 운영 체계 변경
- **Patch (X.Y.Z)** — 버그픽스, 문구 수정, 소폭 스타일 조정

---

## v5.1 — 2026-04-21

### Fixed
- **홈 "지금 많이 읽는 글" 중복 렌더링** — `_fill_container()`의 정규식이 non-greedy `.*?`로 중첩 `</div>`에서 조기 종료되어 기존 카드 HTML이 컨테이너 밖으로 튀어나가던 문제. depth-aware 파서로 교체.
- **아티클 허브 "최신 아티클" 카드 세로 무한 확장** — 위와 동일 원인. `/articles/index.html`의 `feed-all` 컨테이너에서 발생.

### Added
- **푸터 버전 표기** — 모든 주요 페이지의 `footer-legal`에 현재 사이트 버전을 링크로 노출 (`개인정보처리방침 · 이용약관 · v5.1`). 클릭 시 GitHub의 CHANGELOG.md로 이동.
- **CHANGELOG.md** — 저장소 루트에 버전별 기록 문서 신설. 이후 릴리스 시 이 문서에 항목 추가.
- **publisher 스크립트 버전 동기화** — `qlens_gh_publisher.py`에 `SITE_VERSION` / `CHANGELOG_URL` 상수 도입. 아티클 페이지 푸터에 자동 주입.
- **`.footer-version` CSS 스타일** — 톤다운된 회색, hover시 accent 블루.

### Notes
- 이번 버전부터 사이트 UI/인프라 변경은 모두 이 문서에 기록합니다.
- 발행 가이드(Writing Guide) 버전(v3.x)은 `qlens-writing-guide-v3_x.md` 내부의 "버전 히스토리" 섹션에서 별도 관리됩니다.

---

## v5.0 — 2026-04 (Major Release)

### 사이트 리디자인 — 토스피드 스타일 전환

#### Design System
- 배경: 크림 `#f5f0e8` → 흰색 `#ffffff`
- Accent: 주황 `#b5470f` → 블루 `#3182f6`
- 잉크: `#1a1612` → `#0a0a0a`
- 폰트: Noto Serif KR → **Pretendard Variable** (CDN)
- 구분선: 4px 검정 + 블루 72px accent bar
- 카드 border-radius: 일관된 4px

#### Thumbnail Palette Groups
필자를 4개 그룹으로 묶고 각 그룹에 썸네일 팔레트 1:1 매핑:
- **Deep** (산업·경제): `#0f172a` + `#60a5fa` — Ellis, Mills, Harper, Reed, Dash
- **Coast** (시장·사회): `#134e4a` + `#2dd4bf` — Wren, Nova
- **Marine** (테크): `#1e1b4b` + `#a78bfa` — Kai
- **Sunset** (일·조직): `#451a03` + `#fb923c` — Quinn, Cole, Ray

#### Infrastructure
- 플랫폼: WordPress (Cafe24) → **GitHub Pages** (`unitconnect-vp/q-bot-site`)
- DNS: Cloudflare
- 발행 파이프라인: `qlens_gh_publisher.py` (Pillow 썸네일 → HTML 래핑 → articles.json → sitemap.xml → GitHub 커밋)
- 계산기 통합: 과거 `heyqbot/qlens-tools` 별도 저장소 → 메인 저장소 `/tools/{slug}/`로 통합 (12종)

#### Typography & Content Rules
- `§` 기호(섹션 마크) 전면 금지 → `제89조` 등 풀어쓰기로 변경
- stat-row 클래스 기반 전환 (`.ql-stat-row`, `.ql-stat-cell`) — 모바일 640px 이하 자동 세로 스택
- h1 전면 금지 규칙 철회 → 페이지당 정확히 1개 (hero의 `.ql-title`)

#### Publishing Cadence
- 주 4회 → **매일 2편, 주 14편**으로 확대
- 필자·카테고리·팔레트 분산 원칙 도입

---

## 이전 버전 (v1.x ~ v4.x)

v5.0 이전의 변경 내역은 별도 문서(발행 가이드 `qlens-writing-guide-v3_x.md`의 버전 히스토리 섹션)와 Git 커밋 로그에 분산되어 있습니다. 사이트 버전으로서의 체계적 기록은 v5.0부터 시작됩니다.
