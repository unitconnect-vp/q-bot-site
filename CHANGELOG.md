## 2026-05-05 — publisher v5.7: sitemap 게임 누락 사고 차단 + 게임 3종 신규 배포

**배경**

publisher v5.6까지 sitemap.xml 생성 시 `/play/*` URL을 포함시키는 로직이 없어서, 매 아티클 발행마다 sitemap이 덮어쓰일 때 게임 페이지가 계속 빠졌음. 결과적으로 기존 sudoku·nonogram이 장기간 검색엔진에 등록되지 않은 상태였음. 신규 게임 3종 배포(2026-05-05) 점검 중 발견.

**변경**
- 게임 3종 신규 배포 (`/play/2048/`, `/play/wordle/`, `/play/slitherlink/`)
  - 2048 — 슬라이드/머지, 키보드+스와이프+마우스 드래그, localStorage 자동 저장
  - 한국어 워들 — 자모 분해 채점, 일일 챌린지, 단어 풀 156개(검증 통과 한자어 명사)
  - 슬리더링크 — 5×5 동적 polygon 생성, 모든 클루 노출, 단일 폐곡선 검증
- `/play/index.html` 허브에 카드 3장 추가 (총 5종 게임)
- `sitemap.xml`에 6개 URL 수동 등록 (게임 허브 + 5개 게임)
- publisher v5.7 패치
  - `SITEMAP_HUBS`에 `("play/", "weekly", "0.8")` 추가
  - `SITEMAP_GAMES` 신규 상수 — sudoku/nonogram/2048/wordle/slitherlink
  - `deploy()` sitemap 생성 루프에 4-3.5 게임 섹션 추가
  - `SITE_VERSION` v5.6 → v5.7

**검증**
- 5개 게임 페이지: GA / canonical `/play/` / nav 4메뉴 / footer 없음 / 베이지·오렌지 금지 팔레트 0건
- 슬리더링크 polygon 생성 100회 시뮬레이션 → 100% valid 슬리더링크 솔루션
- 워들 단어 풀 156개 모두 양음절 양받침 자모 6개 검증 통과
- publisher v5.7 모듈 import 정상 + SITEMAP_GAMES 5개 + deploy() 루프 포함 확인
- 다음 아티클 발행부터 sitemap.xml에 게임 URL 자동 포함됨

---

## 2026-05-05 — 시리즈 잔존 일괄 정리 (37개 페이지)

v3.7에서 시리즈 기능 삭제 후 산재한 잔존 흔적을 모두 제거.

**변경 사항**
- 푸터 dead link `<li><a href="/series/">시리즈</a></li>` 31개 페이지에서 일괄 제거
  - articles/ 목록·about·contact·privacy·terms / authors/* / categories/*
- 글 6편의 본문 시리즈 배너/참조/링크 카드 통째 삭제 (마커 `<!-- 시리즈 ... -->` + 다음 div 블록)
  - 12eok-nontax-trap-high-value-home, capital-gains-tax-sunset-d21-signal, temp-2house-3year-rule-trap (집 매도 3부작)
  - battery-lfp-ncm-market-restructure, ev-battery-contract-restructure-post-chungla, ev-fire-statistics-reality-check (전기차 화재 3부작)
  - 카드 내 링크는 모두 /articles/ 직접 링크였음 (dead link 0). 자동 관련 글 렌더링(site.js v3.5)이 보충
- about "발행 리듬" 섹션 본문의 시리즈 기획 문단 + dead link 제거

**검증**
- 변경 후 37개 파일 모두 `/series/` 또는 `시리즈` 텍스트 잔여 0건

---

## 2026-05-05 — about 페이지: 편집팀 섹션 삭제

**변경**
- `<h2>3. 편집팀</h2>` 섹션 4줄 통째 제거 (편집팀 소개 + 3원칙 + 필진 소개 링크)
- 후속 섹션 번호 재정렬: 4→3 (발행 리듬), 5→4 (계산기 도구), 6→5 (문의)

**최종 about 구조 (5개 섹션)**
1. Q렌즈란 / 2. 다루는 영역 — 13개 카테고리 / 3. 발행 리듬 / 4. 계산기 도구 / 5. 문의

---

## 2026-05-05 — 9개 계산기 body 박스 → .tool-wrap 분리

이전 커밋의 알려진 이슈(헤더가 body 640px 박스 안에 갇힘) 해결.

**변경 사항 (9개 계산기 동일)**
- body 룰에서 `padding: 2rem 1.25rem 4rem` / `max-width: 640px` / `margin: 0 auto` 3속성 제거 → body 풀폭으로 해방
- 표준 헤더 다음에 `<div class="tool-wrap">` 시작, `</body>` 직전에 `</div>` 닫음
- assets/style.css에 `.tool-wrap { max-width: 640px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }` 추가

**효과**
- 표준 헤더가 viewport 풀폭으로 표시 (다른 페이지와 동일)
- 본문은 기존과 동일한 640px 박스 유지
- sticky 헤더 정상 동작

**대상 9개 (균일 패턴)**
- compound / freelancer-tax / gift-tax / loan / portfolio-concentration / resignation-simulator / salary / severance / unemployment

**범위 외 (3개 outlier)**
- capital-gains-tax / ev-vs-ice / ev-insurance: body 룰이 다른 패턴(Pretendard 사용 또는 max-width 미사용)이라 별도 검토 필요

---

## 2026-05-05 — 페이지별 상단 메뉴 통일

**56개 페이지의 site-nav 마크업을 홈과 동일한 표준으로 일괄 교체**

- 옛 메뉴(홈/카테고리/필진/시리즈/heyqbot 계산기) 사용 중이던 28개 페이지 (categories/*, authors/* 다수, _template) → 신 메뉴로 교체
- 신 메뉴이지만 라벨 "아티클" 그대로였던 28개 페이지 (articles/*, about, contact, privacy 등) → "글"로 통일
- 표준 메뉴: 홈 / 동네 카드 / 계산기 / 글
- site-logo 마크업은 페이지 성격별 기존 그대로 유지 (메인 페이지군 = h1 포함, 상세 페이지 = plain)

**작업 범위 외 (별도 디자인 시스템 또는 보류)**
- /tools/ 계산기 12개: 자체 인라인 네비 (별도 마이크로사이트 형태)
- /town/: 자체 topbar (별도 마이크로사이트)
- 삭제 안내 리다이렉트 페이지 6개 (jeonse-fraud, housing-supply-cliff 등)
- /palettes-fresh/* 4개, test-* 2개: 내부/실험 페이지

---

## 2026-05-05 — 메뉴 디자인 강화 + 어휘 통일 (아티클 → 글)

**메뉴 디자인 (style.css)**
- `.site-nav`: gap 28px → 4px, 항목별 padding 8px 16px + border-radius 8px
- 항목 사이 1px × 14px 세로 구분선 추가 (`a + a::before` 패턴)
- hover 시 옅은 파랑 배경(`rgba(49,130,246,0.08)`) + accent 색상
- 폰트 가중치 600 → 700
- 모바일(900px 이하): 좁은 padding(6px 12px)

**어휘 통일 — 화면 노출 텍스트 "아티클" → "글"**
- 메뉴: `아티클` → `글`
- 헤딩: `지금 많이 읽는 글` → `인기글`, `최신 아티클` → `최신글`
- 서브헤딩: `독자들이 주목한 이번 주 아티클` → `독자들이 주목한 이번 주 글`
- 계산기 섹션 부제: `아티클의 숫자를…` → `글의 숫자를…`
- site.js: `이 주의 아티클` → `이 주의 글`, `아티클 N편` → `글 N편`, 관련 글 빈/오류 메시지
- site.js v5.1 → v5.2

**보류**
- `<meta>` 태그(description, og, twitter)의 "롱폼 아티클 플랫폼" 표현은 SEO 자산이라 별도 결정으로 보류

---

## 2026-05-05 — 오리지널 시리즈 기능 제거

**제거**
- 홈 `오리지널 시리즈` 섹션 (index.html)
- `/series/` 디렉토리 전체 (허브 + market-concentration-2026 상세)
- `/data/series.json`
- `assets/site.js`의 시리즈 라우터·렌더 함수 (`renderHomeSeries`, `renderSeriesList`, `renderSeriesDetail`) → v5.1
- `assets/style.css`의 `.series-grid`, `.series-card*` 클래스
- `sitemap.xml`의 `/series/` URL 엔트리
- 푸터의 시리즈 링크
- `articles.json`에서 두 아티클의 `series`/`series_order` 필드 (kospi-6000-concentration, nps-rebalancing-suspension)

**유지**
- 시리즈에 속해 있던 두 아티클 본문 페이지 (`/articles/kospi-6000-concentration/`, `/articles/nps-rebalancing-suspension/`)는 독립 아티클로 그대로 유지

---

# Q-Lens Changelog

Q렌즈 사이트의 버전별 변경 기록입니다. 이 문서의 최상단 버전은 사이트 푸터의 버전 표기와 동기화됩니다.

---

## v5.3 — 2026-05-03

### Changed

- **사이트 헤더 표준 통일 — 거주지 의사결정 도구 컨셉 격상**
  v4.0 컨셉 정의(2026-04-29)에서 Q-Lens를 "이해 도구"로 재정의. 동네 카드를 "거주지 의사결정 도구"로 핵심 주제 격상. 이를 반영해 사이트 전체 헤더 메뉴를 단일 표준으로 통일.
  - 새 표준: `홈 / 동네 카드 / 계산기 / 아티클` (4개)
  - 동네 카드를 2번째 위치로 — 핵심 주제 가시성 확보
  - 아티클 4번째로 — 보조 수단 위치
  - 적용 범위: 메인 페이지 + 정적 페이지 9개(articles/categories/series/about/tools/contact/privacy/terms/authors) + 모든 아티클 20개 + town/, tools/ 자체 페이지

### Fixed

- **폐기된 heyqbot.github.io/qlens-tools 링크 전수 정리**
  publisher v5.2까지 헤더 계산기 링크가 폐기 저장소(heyqbot/qlens-tools, 2026-04-18 사용 중단) 가리킴. 모든 페이지 본문·헤더에서 `https://heyqbot.github.io/qlens-tools` → `/tools/` 또는 `https://q-bot.kr/tools/` 로 일괄 교체. 잔존 0건 검증.

- **stale 정적 페이지 정리**
  `/town/seoul/gangnam/index.html` (이전 정적 진입 시도 잔재) 삭제 + sitemap.xml에서 해당 URL 제거. 현재 /town/은 SPA 단일 페이지로 운영.

### Added

- **publisher 스크립트 v5.3** (`qlens_gh_publisher_v5_3.py`)
  헤더 nav 새 표준 적용 + heyqbot 링크 → `/tools/` 교체 + `internal_link_pattern` 갱신(`q-bot.kr/tools/`로 인식).

### Operational

- 사이트 헤더 4종 혼재(메인 / 정적페이지 / 옛publisher / 신publisher) 상태가 단일 표준으로 정리됨. 향후 publisher v5.3로 발행되는 모든 신규 아티클은 자동으로 새 표준 헤더 사용.
- v4.0 컨셉의 §6 홈페이지 IA 재설계(v6.0)는 별도 작업으로 분리. 이번 v5.3은 헤더만 선반영.

### Pending (v5.3 외 별도 작업)

- 동네 카드 "거주지 의사결정 도구" 강화 — 5/4 시작 (3주 로드맵: 페르소나별 적합도, A vs B 비교, 의사결정 체크리스트 연결, 상대값 의미 부여)
- LOCALDATA 학원 데이터, KOSIS 5세별 연령 분포 추가
- 카테고리 13개 → 4~6개 토픽 클러스터 통합 (v4.0 §10-1)
- 가이드 v4.0 초안 작성

---

## v5.3 — 2026-05-04

### Removed

- **거주지 의사결정 도구 폐기 (`/town/persona/*`)**
  v4.0 컨셉(이해 도구) 미스매치 + 시군구 단위 점수 모델의 근본적 현실성 부족으로 도구 일체 제거.
  - 시군구 단위(강남구·마포구 등)는 사용자의 실제 의사결정 단위(동·단지·학군)와 너무 거시적
  - 평당가 중위값 등 집계 통계는 동내 편차를 평탄화시켜 결정 근거로 못 씀
  - 사용자 흐름(회사 위치 → 통근범위 → 예산 → 학군)에 "전국 시군구 점수표"가 들어갈 자리 없음
  - 삭제 대상: `/town/persona/index.html`, `/town/persona/compare/index.html`, `/town/persona/checklist/index.html`, `/data/town-records.json`, `.github/scripts/town_persona_*_template.html` 3개
  - nav 정리: 31개 페이지(아티클 23·인덱스 8)에서 "거주지 도구" 메뉴 항목 제거
  - **추가 폐기**: `articles/residence-decision-data-guide-2026/` (도구 가이드 글 — 도구 없으면 무의미. index.html·thumb.webp 삭제, articles.json·sitemap.xml·메인/허브 카드 정리)
  - 유지: `/town/` 동네 카드 (공공데이터 단순 표시, 점수 안 매김 → v4.0 컨셉 충돌 없음)
- **푸터 버전 표기 v5.3으로 갱신.**

---

## v5.2 — 2026-04-23

### Fixed

- **메인페이지·아티클 허브의 카드 중복 표시 (v3.x 누출 잔재 복구)**
  v5.1 파서는 올바르게 동작하지만, v3.x 시절 non-greedy 파서가 만든 오염이 이미 `/index.html`과 `/articles/index.html`에 누적되어 있었음. v5.1의 `_fill_container()`는 "컨테이너 내부 교체" 방식이라 바깥에 떠 있던 카드 파편 DOM을 치우지 못함.
  - 영향: `/` 메인페이지에서 "지금 많이 읽는 글" 6개 뒤에 동일 카드 5개 세로 나열, "최신 아티클" 4개 뒤에 동일 카드 3개 세로 나열. `/articles/`에서는 17개의 오래된 카드 파편이 피드 아래에 누적.
  - 조치: 배포된 두 파일에서 orphan 카드 전량 제거 후 재푸시 (hotfix 커밋).

### Added

- **`_sweep_orphans_after_container()` 헬퍼 (재발 방지)**
  프리렌더 컨테이너 닫힘 직후부터 다음 '구조적' 태그(section/footer/main/aside/header/id 달린 div 등) 직전까지의 영역에 아티클 카드 파편이 있으면 자동 제거. 매 발행 시 실행되어, 과거 누출로 오염된 페이지가 있어도 점진적으로 자가 치유됨.
- **`_verify_no_orphans()` 푸시 전 자가검증**
  sweep 후에도 orphan이 남아있으면 경고 로그 출력. 향후 새로운 컨테이너를 추가할 때 누출 감지 안전망으로 동작.
- **푸터 버전 표기 v5.2로 갱신.**

### Operational

- `_prerender_home()`과 `_prerender_articles_hub()`가 fill → sweep → verify → put 순서로 실행되도록 변경. fill만 하던 v5.1보다 한 단계 더 견고.

---

## v5.1 — 2026-04-21

### Fixed

- **허브 페이지 카드 중복 렌더링**
  `qlens_gh_publisher`의 `_fill_container()` 정규식이 non-greedy `.*?`로 컨테이너를 파싱해, 중첩된 `</div>` 중 첫 번째에서 매칭이 조기 종료되던 버그. 프리렌더 HTML이 컨테이너 바깥으로 튀어나가며 기존 카드 마크업과 겹쳐 보였음.
  - 영향 페이지: `/` (home-recent · home-ranking), `/articles/` (feed-all)
  - 증상: "최신 아티클" 카드가 세로 방향으로 무한 확장, "지금 많이 읽는 글" 1~6번이 두 번 연속 표시
  - 조치: depth-aware 파서로 교체 (positional group, 여닫는 `<div>`/`<section>` 카운터 추적)

### Added

- **푸터 버전 표기 체계 도입**
  모든 주요 페이지 푸터의 "이용약관" 뒤에 현재 사이트 버전(`v5.1`) 링크 추가. 클릭 시 이 CHANGELOG.md로 이동.
- **publisher 스크립트에 `SITE_VERSION` · `CHANGELOG_URL` 상수 도입**
  아티클 발행 시 `wrap_article()`이 푸터에 자동 주입. 버전 올릴 때 상수 하나만 바꾸면 이후 발행 글 전체에 반영됨.
- **`.footer-version` CSS 클래스**
  톤다운된 회색, hover 시 accent 색상 전환.

---

## v5.0 — 2026-04-15

사이트 전면 리디자인. WordPress → GitHub Pages 전환 후 첫 메이저 디자인.

### Changed

- **테마**: 토스피드 스타일 (흰색 배경 + 블루 `#3182f6` accent)
- **폰트**: Pretendard Variable 적용
- **구분선**: 4px 검정 + 72px 블루 accent bar
- **카드**: border-radius 4px
- **썸네일**: 4그룹 팔레트로 개편 (Deep / Coast / Marine / Sunset)
  - 레거시 Claude 기본 팔레트(베이지 `#f5f0e8` · 주황 `#b5470f`)는 전 사이트에서 영구 금지

### Added

- 계산기 12종 통합 배포 (`/tools/{slug}/`, 기존 `heyqbot/qlens-tools` 저장소 폐기)
- 필진 11명 체계 (기존 3명 Lens / Grain / Thread → Ellis · Mills · Harper · Reed · Dash / Wren · Nova / Kai / Quinn · Cole · Ray)
- 카테고리 13개 (기존 7개 → 4그룹으로 재구성: 산업·경제 / 시장·사회 / 테크 / 일·조직)
- `sitemap.xml`에 계산기·카테고리·필진 허브 URL 자동 포함

---

## v4.x 이전

WordPress / Cafe24 운영 시기. 상세 히스토리는 Writing Guide v2.9 이하 버전을 참조.
