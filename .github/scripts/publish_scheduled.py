#!/usr/bin/env python3
"""
Q렌즈 예약 발행 스크립트 v1.0 (2026-04-20)
============================================

설계 원칙:
- articles/scheduled.json 단일 진실 원천
- 아티클 파일은 처음부터 articles/{slug}/에 위치 (물리 이동 없음)
- 예약 대기 중: <meta name="robots" content="noindex"> 부착
- 발행 시각 도달: noindex 제거 + articles.json 등록 + sitemap + 허브 프리렌더

이 스크립트는 GitHub Actions에서 매시간 실행된다.
`.github/workflows/publish-scheduled.yml`에서 호출.

로컬 파일시스템으로 작동 (Actions의 checkout된 저장소 상태 기준).
"""

import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
SCHEDULED_JSON = ARTICLES_DIR / "scheduled.json"
ARTICLES_JSON = ARTICLES_DIR / "articles.json"
SITEMAP_XML = REPO_ROOT / "sitemap.xml"
DATA_DIR = REPO_ROOT / "data"
SITE_URL = "https://q-bot.kr"
KST = timezone(timedelta(hours=9))

# ================================================================
# SITEMAP CONSTANTS (qlens_gh_publisher_v3_4.py와 동기화)
# ================================================================

SITEMAP_HUBS = [
    ("",            "daily",   "1.0"),
    ("articles/",   "daily",   "0.9"),
    ("tools/",      "weekly",  "0.9"),
    ("categories/", "weekly",  "0.7"),
    ("authors/",    "weekly",  "0.7"),
    ("series/",     "weekly",  "0.7"),
    ("about/",      "monthly", "0.5"),
    ("contact/",    "monthly", "0.5"),
]

SITEMAP_TOOLS = [
    "capital-gains-tax-calculator", "compound-calculator",
    "ev-insurance-calculator", "ev-vs-ice-calculator",
    "freelancer-tax-calculator", "gift-tax-calculator",
    "loan-calculator", "portfolio-concentration",
    "resignation-simulator", "salary-calculator",
    "severance-calculator", "unemployment-calculator",
]

SITEMAP_CATEGORIES = [
    "industry", "corporate", "stocks", "bonds", "economy", "realestate",
    "society", "data", "leadership", "method", "career",
]

SITEMAP_AUTHORS = [
    "ellis", "mills", "harper", "reed", "dash",
    "wren", "nova", "kai", "quinn", "cole", "ray",
]

# ================================================================
# AUTHOR → GROUP (프리렌더 카드용)
# ================================================================

AUTHOR_TO_GROUP = {
    "Ellis": "deep", "Mills": "deep", "Harper": "deep", "Reed": "deep", "Dash": "deep",
    "Lens": "deep",
    "Wren": "coast", "Nova": "coast", "Grain": "coast",
    "Kai": "marine",
    "Quinn": "sunset", "Cole": "sunset", "Ray": "sunset", "Thread": "sunset",
}

# ================================================================
# 공용 헬퍼
# ================================================================

def _esc(s):
    if s is None:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

def _fmt_date(iso):
    return iso.replace("-", ".") if iso else ""

def _parse_dt(s):
    """ISO8601 문자열 → datetime. 타임존 없으면 KST로 간주."""
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    return dt

# ================================================================
# noindex 제거 (예약 → 공개 전환)
# ================================================================

NOINDEX_PATTERNS = [
    # 한 줄짜리 robots noindex 메타 (속성 순서 무관)
    re.compile(r'\s*<meta\s+name="robots"\s+content="noindex[^"]*"[^>]*>\s*', re.IGNORECASE),
    re.compile(r'\s*<meta\s+content="noindex[^"]*"\s+name="robots"[^>]*>\s*', re.IGNORECASE),
]

def remove_noindex(html):
    """HTML에서 robots noindex 메타 태그 제거."""
    for pat in NOINDEX_PATTERNS:
        html = pat.sub("\n  ", html)
    return html

# ================================================================
# 프리렌더 카드 생성
# ================================================================

def _card_home_recent(a):
    group = AUTHOR_TO_GROUP.get(a.get("author", ""), "deep")
    slug = _esc(a["slug"])
    title = _esc(a["title"])
    excerpt = f'\n          <div class="card__excerpt">{_esc(a["excerpt"])}</div>' if a.get("excerpt") else ""
    return f'''        <a href="/articles/{slug}/" class="card">
          <div class="card__thumb g-{group}">
            <img src="/articles/{slug}/thumb.webp" alt="{title}" loading="lazy">
          </div>
          <div class="card__cat">{_esc(a["category"])}</div>
          <div class="card__title">{title}</div>{excerpt}
          <div class="card__meta">{_esc(a["author"])} · {_fmt_date(a["date"])}</div>
        </a>'''

def _card_home_ranking(a, rank_idx):
    slug = _esc(a["slug"])
    title = _esc(a["title"])
    return f'''        <a href="/articles/{slug}/" class="rank-item">
          <span class="rank-num">{rank_idx + 1}</span>
          <div class="rank-body">
            <div class="rank-cat">{_esc(a["category"])}</div>
            <div class="rank-title">{title}</div>
            <div class="rank-meta">{_esc(a["author"])} · {_fmt_date(a["date"])}</div>
          </div>
        </a>'''

def _card_feed_all(a):
    slug = _esc(a["slug"])
    title = _esc(a["title"])
    return f'''            <a href="/articles/{slug}/" class="card">
              <img class="card-thumb" src="/articles/{slug}/thumb.webp" alt="{title}" loading="lazy">
              <div class="card-body">
                <p class="card-cat">{_esc(a["category"])}</p>
                <p class="card-title">{title}</p>
                <p class="card-meta">{_esc(a["author"])} · {a["date"]} · {_esc(a.get("read_time", ""))}</p>
              </div>
            </a>'''

def _fill_container(html, container_id, inner_html, marker):
    pattern = re.compile(
        rf'(<(?:div|section)\s+[^>]*\bid="{re.escape(container_id)}"[^>]*>)(.*?)(</(?:div|section)>)',
        re.DOTALL,
    )
    m = pattern.search(html)
    if not m:
        return html, False
    open_tag, _, close_tag = m.groups()
    new_block = f'{open_tag}\n<!-- {marker} -->\n{inner_html}\n      {close_tag}'
    return html[:m.start()] + new_block + html[m.end():], True

def prerender_home(articles):
    path = REPO_ROOT / "index.html"
    if not path.exists():
        print(f"  ⚠️  index.html 없음 — skip")
        return
    html = path.read_text(encoding="utf-8")
    recent = articles[:4]
    top = articles[:6]
    recent_html = "\n".join(_card_home_recent(a) for a in recent)
    ranking_html = "\n".join(_card_home_ranking(a, i) for i, a in enumerate(top))
    html, ok1 = _fill_container(html, "home-recent", recent_html, "PRERENDERED recent — JS overrides")
    html, ok2 = _fill_container(html, "home-ranking", ranking_html, "PRERENDERED ranking — JS overrides")
    if ok1 or ok2:
        path.write_text(html, encoding="utf-8")
        print(f"  ✅ index.html 프리렌더 갱신 (recent={ok1}, ranking={ok2})")
    else:
        print(f"  ⚠️  index.html 컨테이너 못 찾음")

def prerender_articles_hub(articles):
    path = ARTICLES_DIR / "index.html"
    if not path.exists():
        print(f"  ⚠️  articles/index.html 없음 — skip")
        return
    html = path.read_text(encoding="utf-8")
    all_html = "\n".join(_card_feed_all(a) for a in articles)
    html, ok = _fill_container(html, "feed-all", all_html, "PRERENDERED feed-all — JS overrides")
    if ok:
        path.write_text(html, encoding="utf-8")
        print(f"  ✅ articles/index.html 프리렌더 갱신")
    else:
        print(f"  ⚠️  articles/index.html feed-all 못 찾음")

# ================================================================
# sitemap 재생성
# ================================================================

def rebuild_sitemap(articles):
    today = datetime.now(KST).strftime("%Y-%m-%d")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, freq, prio in SITEMAP_HUBS:
        lines += [
            '  <url>',
            f'    <loc>{SITE_URL}/{path}</loc>',
            f'    <lastmod>{today}</lastmod>',
            f'    <changefreq>{freq}</changefreq>',
            f'    <priority>{prio}</priority>',
            '  </url>',
        ]
    for art in articles:
        lines += [
            '  <url>',
            f'    <loc>{SITE_URL}/articles/{art["slug"]}/</loc>',
            f'    <lastmod>{art["date"]}</lastmod>',
            '    <changefreq>monthly</changefreq>',
            '    <priority>0.8</priority>',
            '  </url>',
        ]
    for tool_slug in SITEMAP_TOOLS:
        lines += [
            '  <url>',
            f'    <loc>{SITE_URL}/tools/{tool_slug}/</loc>',
            f'    <lastmod>{today}</lastmod>',
            '    <changefreq>monthly</changefreq>',
            '    <priority>0.8</priority>',
            '  </url>',
        ]
    for cat_slug in SITEMAP_CATEGORIES:
        lines += [
            '  <url>',
            f'    <loc>{SITE_URL}/categories/{cat_slug}/</loc>',
            f'    <lastmod>{today}</lastmod>',
            '    <changefreq>weekly</changefreq>',
            '    <priority>0.6</priority>',
            '  </url>',
        ]
    for auth_slug in SITEMAP_AUTHORS:
        lines += [
            '  <url>',
            f'    <loc>{SITE_URL}/authors/{auth_slug}/</loc>',
            f'    <lastmod>{today}</lastmod>',
            '    <changefreq>weekly</changefreq>',
            '    <priority>0.5</priority>',
            '  </url>',
        ]
    lines.append('</urlset>')
    SITEMAP_XML.write_text("\n".join(lines), encoding="utf-8")
    print(f"  ✅ sitemap.xml 재생성 ({len(articles)} 아티클 포함)")

# ================================================================
# 메인
# ================================================================

def main():
    now = datetime.now(KST)
    print(f"[{now.isoformat()}] 예약 발행 체크 시작")

    if not SCHEDULED_JSON.exists():
        print("scheduled.json 없음 — 예약된 항목 없음")
        return 0

    scheduled = json.loads(SCHEDULED_JSON.read_text(encoding="utf-8"))
    if not scheduled:
        print("scheduled.json 비어있음 — 예약된 항목 없음")
        return 0

    # 발행 대상 필터
    ready = []
    remaining = []
    for entry in scheduled:
        try:
            pub_at = _parse_dt(entry["publish_at"])
        except (ValueError, KeyError) as e:
            print(f"  ⚠️  {entry.get('slug', '???')}: publish_at 파싱 실패 — scheduled.json에서 제외")
            continue
        if pub_at <= now:
            ready.append(entry)
        else:
            remaining.append(entry)
            diff_hours = (pub_at - now).total_seconds() / 3600
            print(f"  ⏳ WAIT {entry['slug']}: {diff_hours:.1f}h 후 발행")

    if not ready:
        print("발행 시각 도달한 항목 없음")
        return 0

    print(f"\n발행 대상 {len(ready)}건")

    # articles.json 로드
    articles = []
    if ARTICLES_JSON.exists():
        articles = json.loads(ARTICLES_JSON.read_text(encoding="utf-8"))

    published = []
    for entry in ready:
        slug = entry["slug"]
        article_path = ARTICLES_DIR / slug / "index.html"

        if not article_path.exists():
            print(f"  ❌ {slug}: articles/{slug}/index.html 없음 — skip")
            # scheduled.json에서 제거 (복구 불가능)
            continue

        # 1. noindex 제거
        html = article_path.read_text(encoding="utf-8")
        before_len = len(html)
        html = remove_noindex(html)
        if len(html) != before_len:
            article_path.write_text(html, encoding="utf-8")
            print(f"  ✅ {slug}: noindex 메타 제거")
        else:
            print(f"  ⚠️  {slug}: noindex 메타 없음 (이미 공개 상태?) — 계속 진행")

        # 2. articles.json에 등록 (중복 제거)
        meta = entry.get("meta", {})
        articles = [a for a in articles if a.get("slug") != slug]
        articles.insert(0, {
            "slug": slug,
            "title": meta.get("title", slug),
            "category": meta.get("category", ""),
            "author": meta.get("author", ""),
            "date": meta.get("date", now.strftime("%Y-%m-%d")),
            "read_time": meta.get("read_time", ""),
        })
        published.append(slug)
        print(f"  ✅ {slug}: articles.json 등록")

    if not published:
        # 발행 성공 0건이면 scheduled.json만 정리
        SCHEDULED_JSON.write_text(
            json.dumps(remaining, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("\n발행 성공 0건 — scheduled.json만 정리")
        return 0

    # 3. 최신순 정렬
    articles.sort(key=lambda a: a.get("date", ""), reverse=True)
    ARTICLES_JSON.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  ✅ articles.json 저장 (총 {len(articles)}편)")

    # 4. sitemap + 프리렌더
    print("\n[sitemap + 프리렌더]")
    rebuild_sitemap(articles)
    prerender_home(articles)
    prerender_articles_hub(articles)

    # 5. scheduled.json에서 발행 완료 제거
    SCHEDULED_JSON.write_text(
        json.dumps(remaining, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n완료: {len(published)}건 발행 — {published}")
    print(f"scheduled.json 잔여: {len(remaining)}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
