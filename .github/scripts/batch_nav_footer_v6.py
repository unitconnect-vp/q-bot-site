#!/usr/bin/env python3
"""
Q렌즈 nav/footer 일괄 갱신 스크립트.

배경:
- VP 결정(2026-05-06): 글 카테고리 폐기, 상단 메뉴 부동산+주식 → 글 통합.
- VP 결정(2026-05-06, 게시판): nav 5번째 항목 '게시판' 추가, footer 바로가기에 '게시판' 추가.
- 새 nav: 홈 · 글 · 게임 · 계산기 · 게시판
- 새 footer 바로가기: 글 · 게임 · 계산기 · 게시판

이력:
- v6.0 (2026-05-06): 카테고리 통합 → 4항목 nav · 바로가기 3링크
- v6.1 (2026-05-06): 게시판 추가 → 5항목 nav · 바로가기 4링크 (현재)

대상:
- 저장소 내 모든 공개 *.html (api·node_modules·palettes-fresh·.git 제외)

실행:
  python3 .github/scripts/batch_nav_footer_v6.py            # 변경 적용
  python3 .github/scripts/batch_nav_footer_v6.py --dry-run  # 변경 대상만 출력
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCLUDE_DIRS = {'.git', 'api', 'node_modules', 'palettes-fresh'}

# 새 표준 nav (header 내부) — 5항목
NEW_NAV = '''<nav class="site-nav">
      <a href="/">홈</a>
      <a href="/articles/">글</a>
      <a href="/play/">게임</a>
      <a href="/tools/">계산기</a>
      <a href="/board/">게시판</a>
    </nav>'''

# 새 표준 footer "바로가기" 컬럼 — 4링크
NEW_FOOTER_COL = '''<div class="footer-col">
<h4 class="footer-col__title">바로가기</h4>
<ul class="footer-col__list">
<li><a href="/articles/">글</a></li>
<li><a href="/play/">게임</a></li>
<li><a href="/tools/">계산기</a></li>
<li><a href="/board/">게시판</a></li>
</ul>
</div>'''

# 정규식: <nav class="site-nav"> ... </nav>  (비탐욕)
NAV_RE = re.compile(
    r'<nav\s+class="site-nav"[^>]*>.*?</nav>',
    re.DOTALL,
)

# footer "바로가기" col block — h4 바로가기 + 그 아래 ul
FOOTER_COL_RE = re.compile(
    r'<div class="footer-col">\s*'
    r'<h4 class="footer-col__title">바로가기</h4>\s*'
    r'<ul class="footer-col__list">.*?</ul>\s*'
    r'</div>',
    re.DOTALL,
)


def iter_public_html(root: Path):
    for p in root.rglob('*.html'):
        rel_parts = p.relative_to(root).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        yield p


def patch_text(text: str):
    """returns (new_text, nav_changed, footer_changed)"""
    nav_changed = False
    footer_changed = False

    new_text, n = NAV_RE.subn(NEW_NAV, text, count=1)
    if n > 0 and new_text != text:
        nav_changed = True
        text = new_text

    new_text, n = FOOTER_COL_RE.subn(NEW_FOOTER_COL, text, count=1)
    if n > 0 and new_text != text:
        footer_changed = True
        text = new_text

    return text, nav_changed, footer_changed


def main():
    dry_run = '--dry-run' in sys.argv

    pages = list(iter_public_html(ROOT))
    nav_count = 0
    footer_count = 0
    untouched = []

    for path in pages:
        try:
            original = path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"ERROR reading {path}: {e}", file=sys.stderr)
            continue

        new_text, nav_chg, foot_chg = patch_text(original)

        if not (nav_chg or foot_chg):
            untouched.append(path)
            continue

        if nav_chg:
            nav_count += 1
        if foot_chg:
            footer_count += 1

        rel = path.relative_to(ROOT)
        flags = []
        if nav_chg:
            flags.append('nav')
        if foot_chg:
            flags.append('footer')
        print(f"  PATCH {rel}  [{','.join(flags)}]")

        if not dry_run:
            path.write_text(new_text, encoding='utf-8')

    print()
    print(f"Pages scanned   : {len(pages)}")
    print(f"  nav patched   : {nav_count}")
    print(f"  footer patched: {footer_count}")
    print(f"  untouched     : {len(untouched)}")

    if untouched and dry_run:
        print()
        print("Untouched (no site-nav or footer-col 바로가기 block):")
        for p in untouched:
            print(f"  {p.relative_to(ROOT)}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
