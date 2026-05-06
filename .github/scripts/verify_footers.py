#!/usr/bin/env python3
"""
Q렌즈 footer 일관성 검증 스크립트.

용도:
- 모든 공개 페이지의 footer 블록을 검사해 archived 카테고리 누출과
  footer-tagline 누락을 보고한다.
- publisher 발행 직후 / CI / 수동 점검에서 사용.
- 누출 발견 시 exit(1).

실행:
  python3 .github/scripts/verify_footers.py
  python3 .github/scripts/verify_footers.py --quiet   # 누출 없으면 침묵

배경:
  publisher v5.4가 옛 8개 카테고리(archived 포함)를 footer에 박아 발행해
  86페이지 일괄 fix 후속이 발생함(commit f4a277c, 2026-05-06).
  v5.8에서 표준 footer 단일 출처 주입 채택 후에도 회귀 방지용으로 유지.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# data/categories.json에서 archived:true인 카테고리 ID
ARCHIVED_CATEGORIES = {
    'industry', 'corporate', 'bonds',
    'leadership', 'method', 'career',
    'ai', 'sports',
}

# footer 검증 제외 (비공개 디자인 시안·CI 산출물·서드파티 등)
EXCLUDE_DIRS = {'.git', 'api', 'node_modules', 'palettes-fresh'}

FOOTER_BLOCK_RE = re.compile(
    r'<footer\b[^>]*class="[^"]*site-footer[^"]*"[^>]*>(.*?)</footer>',
    re.DOTALL,
)
ARCHIVED_LINK_RE = re.compile(
    r'/categories/(' + '|'.join(ARCHIVED_CATEGORIES) + r')/'
)
TAGLINE_RE = re.compile(r'class="footer-tagline"')


def iter_public_html(root: Path):
    for p in root.rglob('*.html'):
        rel_parts = p.relative_to(root).parts
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        yield p


def main():
    quiet = '--quiet' in sys.argv

    leaks = []          # [(path, count, sample_categories)]
    missing_tagline = []  # [path]
    missing_footer = []   # [path] — footer 블록 자체 없음
    pages_checked = 0

    for path in iter_public_html(ROOT):
        pages_checked += 1
        try:
            text = path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"ERROR reading {path}: {e}", file=sys.stderr)
            continue

        m = FOOTER_BLOCK_RE.search(text)
        if not m:
            # mypage·auth 같은 일부 페이지는 footer 의도적으로 없을 수 있음 →
            # 단, q-bot.kr 공개 라우트라면 일관성 위해 누락 보고
            missing_footer.append(path)
            continue

        footer_html = m.group(1)
        archived_hits = ARCHIVED_LINK_RE.findall(footer_html)
        if archived_hits:
            leaks.append((path, len(archived_hits), sorted(set(archived_hits))))

        if not TAGLINE_RE.search(footer_html):
            missing_tagline.append(path)

    has_problems = bool(leaks or missing_tagline or missing_footer)

    if quiet and not has_problems:
        return 0

    print(f"Footer audit — {pages_checked} pages checked")
    print(f"  archived leaks       : {len(leaks)}")
    print(f"  missing tagline      : {len(missing_tagline)}")
    print(f"  missing footer block : {len(missing_footer)}")
    print()

    if leaks:
        print("ARCHIVED CATEGORY LEAKS in footer:")
        for path, count, cats in leaks:
            rel = path.relative_to(ROOT)
            print(f"  {rel}  ({count} links: {', '.join(cats)})")
        print()

    if missing_tagline:
        print("MISSING footer-tagline:")
        for path in missing_tagline:
            print(f"  {path.relative_to(ROOT)}")
        print()

    if missing_footer:
        print("MISSING <footer class='site-footer'> block:")
        for path in missing_footer:
            print(f"  {path.relative_to(ROOT)}")
        print()

    if leaks:
        print("FAIL — archived 카테고리 footer 누출. publisher v5.4의 옛 footer가")
        print("       박혀 있을 가능성. 표준 footer로 재발행 또는 일괄 패치 필요.")
        return 1

    if missing_tagline or missing_footer:
        print("WARN — 누출 없음. 단 footer 일관성 보강 필요.")
        return 0

    print("OK — 모든 페이지 footer 일관성 정상.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
