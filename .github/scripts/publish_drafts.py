#!/usr/bin/env python3
"""
Q렌즈 예약 발행 스크립트
- articles/_drafts/{slug}/publish_at.txt 를 읽어 발행 시각 확인
- 현재 시각(UTC)이 publish_at 이후면 articles/{slug}/ 로 이동
- articles.json, sitemap.xml 자동 업데이트
"""

import os
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
DRAFTS_DIR = REPO_ROOT / "articles" / "_drafts"
ARTICLES_DIR = REPO_ROOT / "articles"
ARTICLES_JSON = ARTICLES_DIR / "articles.json"
SITEMAP_XML = REPO_ROOT / "sitemap.xml"
SITE_URL = "https://q-bot.kr"

now = datetime.now(timezone.utc)
print(f"[{now.isoformat()}] 예약 발행 체크 시작")

if not DRAFTS_DIR.exists():
    print("_drafts 폴더 없음 — 발행할 항목 없음")
    exit(0)

# articles.json 로드
if ARTICLES_JSON.exists():
    with open(ARTICLES_JSON, encoding="utf-8") as f:
        articles = json.load(f)
else:
    articles = []

published_slugs = []

for draft_path in sorted(DRAFTS_DIR.iterdir()):
    if not draft_path.is_dir():
        continue

    slug = draft_path.name
    publish_at_file = draft_path / "publish_at.txt"

    if not publish_at_file.exists():
        print(f"  SKIP {slug}: publish_at.txt 없음")
        continue

    publish_at_str = publish_at_file.read_text().strip()
    try:
        # 형식: 2026-04-18T09:00:00+09:00 또는 2026-04-18T00:00:00Z
        publish_at = datetime.fromisoformat(publish_at_str)
        if publish_at.tzinfo is None:
            # 타임존 없으면 KST(UTC+9) 가정
            from datetime import timedelta
            publish_at = publish_at.replace(tzinfo=timezone(timedelta(hours=9)))
    except ValueError:
        print(f"  SKIP {slug}: publish_at.txt 형식 오류 ({publish_at_str})")
        continue

    if now < publish_at:
        print(f"  WAIT {slug}: 발행 예정 {publish_at.isoformat()}")
        continue

    # 발행 시각 도달 — articles/{slug}/ 로 이동
    target_path = ARTICLES_DIR / slug
    if target_path.exists():
        print(f"  SKIP {slug}: 이미 발행됨")
        shutil.rmtree(draft_path)
        continue

    # publish_at.txt 제거 후 이동
    publish_at_file.unlink()
    shutil.move(str(draft_path), str(target_path))
    print(f"  PUBLISH {slug} → articles/{slug}/")
    published_slugs.append(slug)

    # meta.json 읽어서 articles.json 업데이트
    meta_file = target_path / "meta.json"
    if meta_file.exists():
        with open(meta_file, encoding="utf-8") as f:
            meta = json.load(f)
        # 중복 방지
        if not any(a["slug"] == slug for a in articles):
            articles.insert(0, {
                "slug": meta.get("slug", slug),
                "title": meta.get("title", slug),
                "category": meta.get("category", ""),
                "author": meta.get("author", ""),
                "date": meta.get("date", now.strftime("%Y-%m-%d")),
                "read_time": meta.get("read_time", "")
            })
            print(f"  articles.json 업데이트: {slug}")
    else:
        print(f"  WARNING {slug}: meta.json 없음 — articles.json 미업데이트")

# articles.json 저장
if published_slugs:
    articles.sort(key=lambda a: a.get("date", ""), reverse=True)
    with open(ARTICLES_JSON, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"articles.json 저장 완료")

    # sitemap.xml 재생성 — 전체 URL 포함 (필자·카테고리·시리즈·법적 페이지)
    today_str = now.strftime("%Y-%m-%d")
    
    # 데이터 로드
    DATA_DIR = REPO_ROOT / "data"
    try:
        with open(DATA_DIR / "authors.json", encoding="utf-8") as f:
            authors_data = json.load(f)
    except FileNotFoundError:
        authors_data = []
    try:
        with open(DATA_DIR / "categories.json", encoding="utf-8") as f:
            categories_data = json.load(f)
    except FileNotFoundError:
        categories_data = []
    try:
        with open(DATA_DIR / "series.json", encoding="utf-8") as f:
            series_data = json.load(f)
    except FileNotFoundError:
        series_data = []
    
    urls = []
    # 정적
    urls.append((f"{SITE_URL}/", today_str, "daily", "1.0"))
    urls.append((f"{SITE_URL}/authors/", today_str, "weekly", "0.8"))
    urls.append((f"{SITE_URL}/categories/", today_str, "weekly", "0.8"))
    urls.append((f"{SITE_URL}/series/", today_str, "weekly", "0.8"))
    # 아티클
    for a in articles:
        urls.append((f"{SITE_URL}/articles/{a['slug']}/", a.get("date", today_str), "monthly", "0.9"))
    # 필자
    for a in authors_data:
        urls.append((f"{SITE_URL}/authors/{a['id']}/", today_str, "weekly", "0.7"))
    # 카테고리
    for c in categories_data:
        slug_c = c.get("slug") or c.get("id")
        if slug_c:
            urls.append((f"{SITE_URL}/categories/{slug_c}/", today_str, "weekly", "0.7"))
    # 시리즈
    for s in series_data:
        urls.append((f"{SITE_URL}/series/{s['id']}/", today_str, "monthly", "0.7"))
    # 법적·정보
    urls.append((f"{SITE_URL}/about/", today_str, "yearly", "0.5"))
    urls.append((f"{SITE_URL}/contact/", today_str, "yearly", "0.5"))
    urls.append((f"{SITE_URL}/privacy/", today_str, "yearly", "0.3"))
    urls.append((f"{SITE_URL}/terms/", today_str, "yearly", "0.3"))
    
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, changefreq, priority in urls:
        lines.extend([
            '  <url>',
            f'    <loc>{loc}</loc>',
            f'    <lastmod>{lastmod}</lastmod>',
            f'    <changefreq>{changefreq}</changefreq>',
            f'    <priority>{priority}</priority>',
            '  </url>',
        ])
    lines.append('</urlset>')
    sitemap = "\n".join(lines)

    with open(SITEMAP_XML, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"sitemap.xml 재생성 완료 ({len(urls)} URLs)")

print(f"완료: {len(published_slugs)}건 발행됨 {published_slugs}")
