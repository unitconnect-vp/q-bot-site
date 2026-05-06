#!/usr/bin/env python3
"""
Q렌즈 site-header 단일 표준 정렬 스크립트.

배경:
- 2026-05-06 검토 결과 89개 공개 HTML에 site-header 변종 4가지 존재:
  · variant 1 (36p): `<a class="site-logo" href="/"><h1 ...>Q-Lens</h1></a>`
  · variant 2 (39p): `<a href="/" class="site-logo"><h1 ...>Q-Lens</h1></a>`
  · variant 3 (2p) : `<a href="/" class="site-logo">Q-Lens</a>`
  · variant 4 (12p): `<a class="site-logo" href="/">Q-Lens</a>`
- 75페이지가 logo를 `<h1>`로 감싸 article body의 `<h1>`과 중복
  (SEO 페이지당 h1 1개 원칙 위배). tools/* 12페이지는 이미 h1 없는 형태.

표준:
  <header class="site-header">
  <a class="site-logo" href="/">Q<span>-</span>Lens</a>
  <nav class="site-nav">
    <a href="/">홈</a>
    <a href="/articles/">글</a>
    <a href="/play/">게임</a>
    <a href="/tools/">계산기</a>
  </nav>
  </header>

style.css의 `.site-logo h1 { font: inherit; display: inline; }`
규칙은 h1 제거 후에도 .site-logo 직접 스타일이 적용되어 시각적
렌더링 동일.

실행:
  python3 .github/scripts/unify_site_header.py
  python3 .github/scripts/unify_site_header.py --dry-run
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCLUDE_DIRS = {'.git', 'api', 'node_modules', 'palettes-fresh'}

# 표준 site-logo 마크업 (h1 wrapper 없음, class first 속성 순서)
STD_LOGO = '<a class="site-logo" href="/">Q<span>-</span>Lens</a>'

# 기존 site-logo anchor 매칭 (h1 유무 무관, 속성 순서 무관)
# - h1이 있으면 h1 내부 텍스트가 "Q<span>-</span>Lens" 또는 "Q-Lens" 형태
SITE_LOGO_RE = re.compile(
    r'<a\s+(?:class="site-logo"\s+href="/"|href="/"\s+class="site-logo")[^>]*>'
    r'(?:<h1[^>]*>)?'
    r'\s*Q<span>-</span>Lens\s*'
    r'(?:</h1>)?'
    r'</a>',
    re.DOTALL,
)


def iter_public_html(root: Path):
    for p in root.rglob('*.html'):
        if any(part in EXCLUDE_DIRS for part in p.relative_to(root).parts):
            continue
        yield p


def main():
    dry = '--dry-run' in sys.argv
    pages = list(iter_public_html(ROOT))
    patched = 0
    untouched = []

    for path in pages:
        try:
            text = path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"ERROR reading {path}: {e}", file=sys.stderr)
            continue

        new_text, n = SITE_LOGO_RE.subn(STD_LOGO, text, count=1)
        if n == 0 or new_text == text:
            untouched.append(path)
            continue

        rel = path.relative_to(ROOT)
        print(f"  PATCH {rel}")
        patched += 1
        if not dry:
            path.write_text(new_text, encoding='utf-8')

    print()
    print(f"Pages scanned : {len(pages)}")
    print(f"  patched     : {patched}")
    print(f"  untouched   : {len(untouched)}")

    if untouched and dry:
        print()
        print("Untouched (no site-logo anchor matched, or already standard):")
        for p in untouched:
            print(f"  {p.relative_to(ROOT)}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
