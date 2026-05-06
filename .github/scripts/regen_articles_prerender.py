#!/usr/bin/env python3
"""
articles/index.html의 prerender(`<div id="feed-all">…</div>`)를
articles/articles.json 단일 출처로부터 재생성한다.

배경:
- 2026-05-06 발견: articles/index.html prerender가 articles.json보다
  오래되어 오늘 발행 글(seongnam-apt-trading-volume-buyer-guide-2026)이
  목록에서 누락. 인라인 JS도 `+=` 누적이라 prerender 뒤에 중복 append.
- JS 측은 동일 turn에 `=` 교체로 수정. 이 스크립트는 prerender(SEO·초기
  페인트)를 articles.json과 동기화한다.

실행:
  python3 .github/scripts/regen_articles_prerender.py
  python3 .github/scripts/regen_articles_prerender.py --dry-run
"""
import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLES_JSON = ROOT / 'articles' / 'articles.json'
LIST_PAGE = ROOT / 'articles' / 'index.html'

FEED_RE = re.compile(
    r'(<div id="feed-all" class="feed-recent">\s*'
    r'<!-- PRERENDERED feed-all — JS overrides -->)'
    r'(.*?)'
    r'(\s*</div>\s*\n*</main>)',
    re.DOTALL,
)


def render_card(a: dict) -> str:
    slug = escape(a.get('slug', ''))
    title = escape(a.get('title', ''))
    category = escape(a.get('category', ''))
    author = escape(a.get('author', ''))
    date = escape(a.get('date', ''))
    read_time = escape(a.get('read_time', ''))
    return (
        f'            <a href="/articles/{slug}/" class="card">\n'
        f'              <img class="card-thumb" src="/articles/{slug}/thumb.webp" '
        f'alt="{title}" loading="lazy">\n'
        f'              <div class="card-body">\n'
        f'                <p class="card-cat">{category}</p>\n'
        f'                <p class="card-title">{title}</p>\n'
        f'                <p class="card-meta">{author} · {date} · {read_time}</p>\n'
        f'              </div>\n'
        f'            </a>'
    )


def main():
    dry = '--dry-run' in sys.argv

    articles = json.loads(ARTICLES_JSON.read_text(encoding='utf-8'))
    sorted_articles = sorted(articles, key=lambda a: a.get('date', ''), reverse=True)

    cards = '\n'.join(render_card(a) for a in sorted_articles)
    new_block = '\n' + cards + '\n      '

    text = LIST_PAGE.read_text(encoding='utf-8')
    m = FEED_RE.search(text)
    if not m:
        print("ERROR: feed-all prerender block not found in articles/index.html",
              file=sys.stderr)
        return 1

    new_text = text[:m.start(2)] + new_block + text[m.end(2):]

    if new_text == text:
        print(f"No change. {len(sorted_articles)} articles already match prerender.")
        return 0

    print(f"Rewriting prerender — {len(sorted_articles)} cards (latest: "
          f"{sorted_articles[0]['slug']} {sorted_articles[0]['date']})")

    if dry:
        return 0

    LIST_PAGE.write_text(new_text, encoding='utf-8')
    print("OK — articles/index.html updated.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
