#!/usr/bin/env python3
"""
Q렌즈 자체 방문자 트래커(/assets/analytics.js)를 모든 공개 HTML 페이지의
</head> 직전에 주입한다.

용도:
- 트래커 도입 시 1회 일괄 주입
- publisher가 옛 마크업으로 발행해 누락된 페이지가 생기면 회귀 fix용 재실행

대상 제외:
- api/*, node_modules/*, .git/*
- palettes-fresh/*  (시안 페이지)
- test-*.html       (검증 페이지)

이미 analytics.js가 박힌 페이지는 건드리지 않음(idempotent).

실행:
  python3 .github/scripts/inject_analytics.py
  python3 .github/scripts/inject_analytics.py --dry-run
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXCLUDE_DIRS = {'.git', 'api', 'node_modules', 'palettes-fresh'}
EXCLUDE_FILE_PREFIXES = ('test-',)

SCRIPT_TAG = '<script src="/assets/analytics.js" defer></script>'
HEAD_CLOSE_RE = re.compile(r'</head>', re.IGNORECASE)
ALREADY_RE = re.compile(r'/assets/analytics\.js')


def iter_targets(root: Path):
    for p in root.rglob('*.html'):
        rel = p.relative_to(root)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if rel.name.startswith(EXCLUDE_FILE_PREFIXES):
            continue
        yield p


def main():
    dry = '--dry-run' in sys.argv
    injected = []
    skipped_already = []
    skipped_nohead = []

    for path in iter_targets(ROOT):
        try:
            text = path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"ERROR reading {path}: {e}", file=sys.stderr)
            continue

        if ALREADY_RE.search(text):
            skipped_already.append(path)
            continue

        m = HEAD_CLOSE_RE.search(text)
        if not m:
            skipped_nohead.append(path)
            continue

        new_text = text[:m.start()] + SCRIPT_TAG + '\n' + text[m.start():]
        if not dry:
            path.write_text(new_text, encoding='utf-8')
        injected.append(path)

    print(f"Analytics injection — {'DRY RUN' if dry else 'APPLIED'}")
    print(f"  injected         : {len(injected)}")
    print(f"  already had tag  : {len(skipped_already)}")
    print(f"  no </head> tag   : {len(skipped_nohead)}")

    if skipped_nohead:
        print("\nNO </head> tag found:")
        for p in skipped_nohead:
            print(f"  {p.relative_to(ROOT)}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
