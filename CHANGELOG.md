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
  - 잔존: `articles/residence-decision-data-guide-2026/` (글 자체가 도구 가이드 — 발행인 결정 대기)
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
