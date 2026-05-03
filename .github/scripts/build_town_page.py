#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q렌즈 동네 카드 — 빌드 스크립트 v1
town/data/seoul/gangnam.json → town/seoul/gangnam/index.html
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from string import Template

DATA_DIR = Path("town/data")
OUTPUT_BASE = Path("town")


# ─────────────────────────────────────────────────
# 포맷 헬퍼
# ─────────────────────────────────────────────────

def fmt_num(n):
    """1234567 → '1,234,567'."""
    if n is None:
        return "—"
    return f"{int(n):,}"


def fmt_man_to_eok(man):
    """만원 단위 → 억 표기. 12345만원 → 1.23억."""
    if man is None or man == 0:
        return "—"
    eok = man / 10000
    if eok >= 10:
        return f"{eok:.0f}억"
    return f"{eok:.1f}억"


def jeonse_ratio(rent, trade):
    """전세가율 — 전세 중앙값(만원) / 매매 중앙값(만원). 면적 보정은 2단계."""
    j = rent.get("median_jeonse_man")
    t = trade.get("median_deal_amount_man")
    if not j or not t:
        return None
    return round(j / t * 100, 1)


def pct_bar(value, max_value):
    """0~100% width 비율."""
    if not value or not max_value:
        return 0
    return min(100, round(value / max_value * 100))


# ─────────────────────────────────────────────────
# 인사이트 생성 — 실데이터 기반
# ─────────────────────────────────────────────────

def insight_real_estate(trade, rent):
    median_pyeong = trade.get("median_price_per_pyeong_man")
    monthly = trade.get("monthly_count_avg")
    jeonse_med = rent.get("median_jeonse_man")
    jratio = jeonse_ratio(rent, trade)

    parts = []
    if median_pyeong:
        parts.append(f"강남구 아파트 평당가 중앙값은 <b>{fmt_num(median_pyeong)}만원</b>")
    if monthly:
        parts.append(f"월평균 매매 거래는 <b>{int(monthly)}건</b>")
    if jratio:
        parts.append(f"전세 중앙값 대비 매매 중앙값 비율은 <b>약 {jratio}%</b> (면적 보정 전 단순 비교치)")
    sentence = ", ".join(parts) + "입니다."

    # 강남구는 일반적으로 거래량이 적은 시장
    follow = "거래량이 줄어든 게 시장이 얼어붙은 게 아니라, 가진 사람이 안 내놓는 시장이라는 해석도 가능합니다."
    return sentence + " " + follow


def insight_environment(env):
    seoul = env.get("seoul_avg", {}) or {}
    gn = env.get("gangnam_station") or {}
    s_pm25 = seoul.get("pm25")
    g_pm25 = gn.get("pm25")
    measured = env.get("measured_at", "")

    if g_pm25 is not None and s_pm25 is not None:
        if g_pm25 < s_pm25:
            cmp_text = f"서울 평균(<b>{s_pm25}</b>)보다 강남구(<b>{g_pm25}</b>)가 낮습니다"
        elif g_pm25 > s_pm25:
            cmp_text = f"서울 평균(<b>{s_pm25}</b>)보다 강남구(<b>{g_pm25}</b>)가 높습니다"
        else:
            cmp_text = f"서울 평균과 강남구 모두 <b>{g_pm25}</b>로 동일"
        return f"{measured} 기준 PM2.5 수치는 {cmp_text}. 단일 시점 측정값이라 추세는 누적 데이터로 별도 확인이 필요합니다."
    if s_pm25 is not None:
        return f"{measured} 기준 서울 평균 PM2.5는 <b>{s_pm25} µg</b>. 강남구 측정소 단일 데이터는 다음 페치 회차에 보강됩니다."
    return "측정 데이터를 받아오는 중입니다."


def insight_medical(med):
    g = med.get("gangnam_count", 0)
    seoul = med.get("total_seoul", 0)
    by_type = med.get("by_type", {}) or {}
    eui = by_type.get("의원", 0)
    sang = by_type.get("상급종합", 0)
    jong = by_type.get("종합병원", 0)

    notes = []
    if g and seoul:
        notes.append(f"강남구는 서울 전체 의료기관의 <b>{round(g/seoul*100, 1)}%</b>")
    if eui:
        notes.append(f"이 중 의원이 <b>{fmt_num(eui)}개</b>")
    if sang or jong:
        notes.append(f"상급종합 {sang}곳, 종합병원 {jong}곳")
    return ", ".join(notes) + "이 위치합니다. 의료 인프라는 양적으로 압도적이지만, 동네 단위로 들여다보면 분포 편차가 큽니다."


def insight_education(edu):
    g = edu.get("gangnam_count", 0)
    by_type = edu.get("by_type", {}) or {}
    elem = by_type.get("초등학교", 0)
    mid = by_type.get("중학교", 0)
    high = by_type.get("고등학교", 0)

    return (
        f"강남구 정규 학교는 <b>{g}개</b> "
        f"(초 <b>{elem}</b> · 중 <b>{mid}</b> · 고 <b>{high}</b>). "
        "학교 수만으로는 평범하지만, 학원·교습소를 포함한 사교육 인프라까지 합치면 그림이 달라집니다. "
        "사업장 데이터(2단계 추가 예정)와 함께 보면 진짜 밀도가 드러납니다."
    )


def insight_population(pop):
    g = pop.get("gangnam_total")
    s = pop.get("seoul_total")
    share = pop.get("share_of_seoul_pct")
    period = pop.get("period", "")

    if not g:
        return "인구 데이터 수집 중입니다."

    period_str = ""
    if period and len(period) == 6:
        period_str = f"{period[:4]}년 {period[4:].lstrip('0')}월 "

    avg_gu = round(s / 25) if s else None
    ratio_text = ""
    if avg_gu and g:
        ratio = round(g / avg_gu, 2)
        if ratio > 1:
            ratio_text = f" 서울 25개 자치구 평균(<b>{fmt_num(avg_gu)}명</b>) 대비 <b>{ratio}배</b>."
        elif ratio < 1:
            ratio_text = f" 서울 25개 자치구 평균(<b>{fmt_num(avg_gu)}명</b>) 대비 <b>{ratio}배</b>."

    return (
        f"{period_str}기준 강남구 인구는 <b>{fmt_num(g)}명</b>. "
        f"서울 전체의 <b>{share}%</b>를 차지합니다.{ratio_text} "
        "연령 분포·1인가구 비율·소득 구조는 다음 페치 회차에 추가됩니다."
    )


# ─────────────────────────────────────────────────
# HTML 빌드
# ─────────────────────────────────────────────────

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  font-family: 'Pretendard Variable', Pretendard, -apple-system, sans-serif;
  background: #ffffff; color: #0f172a;
  font-feature-settings: 'tnum';
  -webkit-font-smoothing: antialiased; line-height: 1.6;
}
.wrap { max-width: 760px; margin: 0 auto; padding: 0 20px; }
.topbar { border-bottom: 1px solid #e5e7eb; padding: 14px 0; margin-bottom: 56px; }
.topbar-inner { display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
.brand { font-weight: 700; color: #0f172a; text-decoration: none; }
.brand-sub { color: #64748b; margin-left: 8px; font-weight: 500; }
.search-pill { background: #f1f5f9; border: none; padding: 8px 16px; border-radius: 4px; font-family: inherit; font-size: 13px; color: #475569; cursor: pointer; }
.hero { margin-bottom: 56px; }
.hero-eyebrow { font-size: 13px; color: #64748b; margin-bottom: 8px; letter-spacing: 0.02em; }
.hero h1 { font-size: 56px; font-weight: 800; line-height: 1.1; letter-spacing: -0.03em; color: #0f172a; margin-bottom: 12px; }
.hero-tagline { font-size: 17px; color: #475569; margin-bottom: 32px; max-width: 540px; }
.hero-meta { font-size: 12px; color: #94a3b8; border-top: 4px solid #0f172a; border-bottom: 1px solid #e5e7eb; padding: 12px 0; }
.hero-meta b { color: #3182f6; font-weight: 600; }

.ql-stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; border: 1px solid #e5e7eb; border-radius: 4px; margin: 32px 0 56px; background: #ffffff; }
.ql-stat-cell { padding: 24px 20px; border-right: 1px solid #e5e7eb; }
.ql-stat-cell:last-child { border-right: none; }
.ql-stat-num { font-size: 32px; font-weight: 800; color: #0f172a; letter-spacing: -0.02em; line-height: 1.1; margin-bottom: 6px; }
.ql-stat-num .unit { font-size: 16px; color: #64748b; font-weight: 600; margin-left: 2px; }
.ql-stat-label { font-size: 12px; color: #64748b; font-weight: 500; }

@media (max-width: 640px) {
  .ql-stat-row { grid-template-columns: 1fr; }
  .ql-stat-cell { border-right: none; border-bottom: 1px solid #e5e7eb; }
  .ql-stat-cell:last-child { border-bottom: none; }
  .hero h1 { font-size: 40px; }
}

.section { margin-bottom: 64px; padding-top: 32px; border-top: 4px solid #0f172a; }
.section.pending { border-top-color: #cbd5e1; }
.section-num { font-size: 12px; color: #60a5fa; font-weight: 700; letter-spacing: 0.1em; }
.section.pending .section-num { color: #94a3b8; }
.section h2 { font-size: 28px; font-weight: 800; letter-spacing: -0.02em; color: #0f172a; margin: 8px 0; }
.section-sub { font-size: 14px; color: #64748b; margin-bottom: 24px; }

.bar-block { margin: 24px 0; }
.bar-row { display: grid !important; grid-template-columns: 90px 1fr 80px !important; align-items: center !important; gap: 12px !important; padding: 8px 0 !important; font-size: 13px !important; }
.bar-label { color: #475569 !important; font-weight: 500 !important; }
.bar-track { background: #f1f5f9 !important; height: 8px !important; border-radius: 4px !important; overflow: hidden !important; }
.bar-fill { background: #0f172a !important; height: 100% !important; border-radius: 4px !important; }
.bar-fill.accent { background: #60a5fa !important; }
.bar-value { text-align: right !important; color: #0f172a !important; font-weight: 600 !important; font-variant-numeric: tabular-nums !important; }

.compare-table { display: grid !important; grid-template-columns: 1fr 1fr 1fr !important; border: 1px solid #e5e7eb !important; border-radius: 4px !important; margin: 24px 0 !important; font-size: 13px !important; overflow: hidden !important; }
.compare-cell { padding: 14px 16px !important; border-right: 1px solid #e5e7eb !important; border-bottom: 1px solid #e5e7eb !important; }
.compare-cell:nth-child(3n) { border-right: none !important; }
.compare-cell.head { background: #f8fafc !important; font-weight: 700 !important; color: #0f172a !important; font-size: 12px !important; }
.compare-cell.label { color: #64748b !important; }
.compare-cell.val { color: #0f172a !important; font-weight: 600 !important; font-variant-numeric: tabular-nums !important; }
.compare-cell.val.highlight { color: #3182f6 !important; }

.insight { background: #f8fafc; border-left: 4px solid #60a5fa; padding: 20px 24px; margin: 24px 0; border-radius: 0 4px 4px 0; }
.section.pending .insight { border-left-color: #cbd5e1; }
.insight-tag { font-size: 11px; font-weight: 700; color: #3182f6; letter-spacing: 0.1em; margin-bottom: 8px; }
.section.pending .insight-tag { color: #94a3b8; }
.insight p { font-size: 15px; color: #0f172a; line-height: 1.65; }
.insight p b { color: #0f172a; font-weight: 700; }
.source { font-size: 11px; color: #94a3b8; margin-top: 16px; padding-top: 12px; border-top: 1px solid #f1f5f9; }

.cta { background: #0f172a; color: #ffffff; padding: 48px 32px; border-radius: 4px; text-align: center; margin: 80px 0; }
.cta h3 { font-size: 24px; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 12px; }
.cta p { font-size: 14px; color: #cbd5e1; margin-bottom: 24px; }

footer { border-top: 1px solid #e5e7eb; padding: 32px 0 48px; font-size: 12px; color: #94a3b8; text-align: center; }
footer a { color: #94a3b8; text-decoration: none; margin: 0 8px; }
"""


def render_bar(label, value, max_value, unit="", accent=False):
    pct = pct_bar(value, max_value)
    cls = "bar-fill accent" if accent else "bar-fill"
    val_text = f"{fmt_num(value)} {unit}".strip() if value is not None else "—"
    return (
        f'<div class="bar-row">'
        f'<div class="bar-label">{label}</div>'
        f'<div class="bar-track"><div class="{cls}" style="width: {pct}%"></div></div>'
        f'<div class="bar-value">{val_text}</div>'
        f'</div>'
    )


def render_real_estate(trade, rent):
    median_pyeong = trade.get("median_price_per_pyeong_man")
    median_deal = trade.get("median_deal_amount_man")
    monthly = trade.get("monthly_count_avg")
    jeonse_med = rent.get("median_jeonse_man")
    jeonse_count = rent.get("jeonse_count")
    monthly_count = rent.get("monthly_count")
    jratio = jeonse_ratio(rent, trade)

    rows = [
        ("아파트 평당가 (중앙값)", f"{fmt_num(median_pyeong)} 만원", True),
        ("매매 평균 거래액 (중앙값)", fmt_man_to_eok(median_deal), False),
        ("월평균 매매 건수", f"{int(monthly) if monthly else '—'} 건", False),
        ("전세 중앙값", fmt_man_to_eok(jeonse_med), False),
        ("전세 거래 / 월세 거래", f"{fmt_num(jeonse_count)} / {fmt_num(monthly_count)} 건", False),
        ("매매-전세 비율(단순)", f"{jratio} %" if jratio else "—", False),
    ]

    table = '<div class="compare-table" style="grid-template-columns: 1fr 1fr !important;">'
    table += '<div class="compare-cell head">지표</div><div class="compare-cell head">값</div>'
    for label, val, hi in rows:
        cls = "compare-cell val highlight" if hi else "compare-cell val"
        table += f'<div class="compare-cell label">{label}</div><div class="{cls}">{val}</div>'
    table += '</div>'
    return table


def render_environment(env):
    seoul = env.get("seoul_avg", {}) or {}
    gn = env.get("gangnam_station") or {}
    bars = []
    bars.append(render_bar("PM10 (서울평균)", seoul.get("pm10"), 100, "µg"))
    if gn.get("pm10") is not None:
        bars.append(render_bar("PM10 (강남구)", gn.get("pm10"), 100, "µg", accent=True))
    bars.append(render_bar("PM2.5 (서울평균)", seoul.get("pm25"), 50, "µg"))
    if gn.get("pm25") is not None:
        bars.append(render_bar("PM2.5 (강남구)", gn.get("pm25"), 50, "µg", accent=True))
    return '<div class="bar-block">' + "".join(bars) + '</div>'


def render_medical(med):
    by_type = med.get("by_type", {}) or {}
    if not by_type:
        return ""
    max_v = max(by_type.values())
    bars = [render_bar(k, v, max_v, "곳") for k, v in sorted(by_type.items(), key=lambda x: -x[1])]
    return '<div class="bar-block">' + "".join(bars) + '</div>'


def render_education(edu):
    by_type = edu.get("by_type", {}) or {}
    if not by_type:
        return ""
    # 정규 학교 4종 위주로
    main = ["초등학교", "중학교", "고등학교", "특수학교"]
    rows = [(k, by_type.get(k, 0)) for k in main if by_type.get(k)]
    other = sum(v for k, v in by_type.items() if k not in main)
    if other:
        rows.append(("기타", other))
    max_v = max(v for _, v in rows) if rows else 1
    bars = [render_bar(k, v, max_v, "개") for k, v in rows]
    return '<div class="bar-block">' + "".join(bars) + '</div>'


def render_population(pop):
    """강남구 인구 vs 서울 25개 자치구 평균 비교 막대."""
    g = pop.get("gangnam_total")
    s = pop.get("seoul_total")
    if not g:
        return ""
    avg_gu = round(s / 25) if s else None
    max_v = max(g, avg_gu) if avg_gu else g
    bars = [render_bar("강남구", g, max_v, "명", accent=True)]
    if avg_gu:
        bars.append(render_bar("서울 자치구 평균", avg_gu, max_v, "명"))
    if s:
        bars.append(render_bar("서울 전체", s, max(s, max_v), "명"))
    return '<div class="bar-block">' + "".join(bars) + '</div>'


# ─────────────────────────────────────────────────
# 페이지 템플릿
# ─────────────────────────────────────────────────

PAGE = Template("""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>$name — Q렌즈 동네 카드</title>
<meta name="description" content="$name의 인구·부동산·교육·환경·의료 데이터를 한 장에. 보이는 것 너머를 묻습니다.">
<link rel="canonical" href="https://q-bot.kr/town/$slug/">
<meta property="og:title" content="$name — Q렌즈 동네 카드">
<meta property="og:description" content="$name의 데이터 초상화. 평당가, 학교, 의료, 환경 한 눈에.">
<meta property="og:url" content="https://q-bot.kr/town/$slug/">
<meta property="og:type" content="website">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<style>$css</style>
</head>
<body>

<div class="topbar">
  <div class="wrap">
    <div class="topbar-inner">
      <div>
        <a href="/town/" class="brand">Q렌즈 동네 카드</a>
        <span class="brand-sub">보이는 것 너머를 묻습니다</span>
      </div>
      <button class="search-pill" onclick="alert('동네 검색은 곧 추가됩니다.')">🔍 다른 동네</button>
    </div>
  </div>
</div>

<div class="wrap">

  <section class="hero">
    <div class="hero-eyebrow">서울특별시</div>
    <h1>$name</h1>
    <p class="hero-tagline">$tagline</p>
    <div class="hero-meta">데이터 기준일 <b>$fetched_date</b> · 출처 국토교통부·환경공단·심평원·교육부·통계청</div>
  </section>

  <div class="ql-stat-row">
    <div class="ql-stat-cell">
      <div class="ql-stat-num">$stat1_num<span class="unit">$stat1_unit</span></div>
      <div class="ql-stat-label">$stat1_label</div>
    </div>
    <div class="ql-stat-cell">
      <div class="ql-stat-num">$stat2_num<span class="unit">$stat2_unit</span></div>
      <div class="ql-stat-label">$stat2_label</div>
    </div>
    <div class="ql-stat-cell">
      <div class="ql-stat-num">$stat3_num<span class="unit">$stat3_unit</span></div>
      <div class="ql-stat-label">$stat3_label</div>
    </div>
  </div>

  <section class="section">
    <div class="section-num">01 — 부동산</div>
    <h2>집값과 거래의 흐름</h2>
    <p class="section-sub">최근 2~3개월 강남구 아파트 매매·전월세 실거래 데이터.</p>
    $sec_real_estate
    <div class="insight">
      <div class="insight-tag">Q렌즈의 시각</div>
      <p>$insight_real_estate</p>
    </div>
    <div class="source">출처: 국토교통부 실거래가 공개시스템</div>
  </section>

  <section class="section">
    <div class="section-num">02 — 환경</div>
    <h2>공기와 측정값</h2>
    <p class="section-sub">에어코리아 시도/측정소 실시간 데이터.</p>
    $sec_environment
    <div class="insight">
      <div class="insight-tag">Q렌즈의 시각</div>
      <p>$insight_environment</p>
    </div>
    <div class="source">출처: 한국환경공단 에어코리아</div>
  </section>

  <section class="section">
    <div class="section-num">03 — 의료</div>
    <h2>병원·의원 분포</h2>
    <p class="section-sub">강남구 소재 의료기관 종별 분포.</p>
    $sec_medical
    <div class="insight">
      <div class="insight-tag">Q렌즈의 시각</div>
      <p>$insight_medical</p>
    </div>
    <div class="source">출처: 건강보험심사평가원</div>
  </section>

  <section class="section">
    <div class="section-num">04 — 교육</div>
    <h2>학교 분포</h2>
    <p class="section-sub">강남구 소재 정규 학교 (학원·교습소는 2단계 추가 예정).</p>
    $sec_education
    <div class="insight">
      <div class="insight-tag">Q렌즈의 시각</div>
      <p>$insight_education</p>
    </div>
    <div class="source">출처: 교육부 NEIS 교육정보 개방 포털</div>
  </section>

  <section class="section">
    <div class="section-num">05 — 인구</div>
    <h2>누가 살고 있나</h2>
    <p class="section-sub">행정안전부 주민등록인구 — 가장 단순하지만 동네의 골격을 가장 잘 보여주는 데이터.</p>
    $sec_population
    <div class="insight">
      <div class="insight-tag">Q렌즈의 시각</div>
      <p>$insight_population</p>
    </div>
    <div class="source">출처: 통계청 KOSIS · 행정안전부 주민등록인구 (DT_1B040A3)</div>
  </section>

  <div class="cta">
    <h3>당신의 동네는 어떻게 보일까요?</h3>
    <p>현재 강남구만 공개. 서울 25개 자치구는 단계적으로 추가됩니다.</p>
  </div>

</div>

<footer>
  <div class="wrap">
    Q렌즈 · q-bot.kr ·
    <a href="/about/">소개</a>
    <a href="/town/">동네 카드 홈</a>
    <a href="/contact/">문의</a>
  </div>
</footer>

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-04MMSE99PJ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-04MMSE99PJ');
</script>

</body>
</html>
""")


def build_page(data):
    sections = data["sections"]
    trade = sections.get("real_estate_trade", {}) or {}
    rent = sections.get("real_estate_rent", {}) or {}
    env = sections.get("environment", {}) or {}
    med = sections.get("medical", {}) or {}
    edu = sections.get("education", {}) or {}
    pop = sections.get("population", {}) or {}

    # 페치 시각 → KST 표기
    try:
        fetched_dt = datetime.fromisoformat(data["fetched_at"].replace("Z", "+00:00"))
        fetched_date = fetched_dt.strftime("%Y년 %m월")
    except Exception:
        fetched_date = "—"

    median_pyeong = trade.get("median_price_per_pyeong_man")
    median_jeonse = rent.get("median_jeonse_man")
    pop_total = pop.get("gangnam_total")

    return PAGE.safe_substitute({
        "name": data["name"],
        "slug": data["slug"],
        "tagline": "압구정·역삼·삼성·도곡 — 한국에서 가장 자주 거론되지만, 가장 덜 정확하게 알려진 동네.",
        "fetched_date": fetched_date,
        "css": CSS,

        "stat1_num": fmt_num(median_pyeong) if median_pyeong else "—",
        "stat1_unit": "만원" if median_pyeong else "",
        "stat1_label": "아파트 평당가 (중앙값)",

        "stat2_num": fmt_man_to_eok(median_jeonse).rstrip("억") if median_jeonse else "—",
        "stat2_unit": "억" if median_jeonse else "",
        "stat2_label": "전세 중앙값",

        "stat3_num": fmt_num(pop_total) if pop_total else "—",
        "stat3_unit": "명" if pop_total else "",
        "stat3_label": "인구 (주민등록 기준)",

        "sec_real_estate": render_real_estate(trade, rent),
        "sec_environment": render_environment(env),
        "sec_medical": render_medical(med),
        "sec_education": render_education(edu),
        "sec_population": render_population(pop),

        "insight_real_estate": insight_real_estate(trade, rent),
        "insight_environment": insight_environment(env),
        "insight_medical": insight_medical(med),
        "insight_education": insight_education(edu),
        "insight_population": insight_population(pop),
    })


# ─────────────────────────────────────────────────
# 허브 페이지 (/town/index.html)
# ─────────────────────────────────────────────────

HUB_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>동네 카드 — Q렌즈</title>
<meta name="description" content="주소 한 줄이면 그 동네의 인구·부동산·교육·환경·의료 데이터를 한 장에. 보이는 것 너머를 묻습니다.">
<link rel="canonical" href="https://q-bot.kr/town/">
<meta property="og:title" content="Q렌즈 동네 카드">
<meta property="og:description" content="당신의 동네는 어떻게 보일까요?">
<meta property="og:url" content="https://q-bot.kr/town/">
<meta property="og:type" content="website">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<style>$css

.hub-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin: 32px 0 64px; }
@media (max-width: 640px) { .hub-grid { grid-template-columns: 1fr; } }
.town-card { display: block; border: 1px solid #e5e7eb; border-radius: 4px; padding: 24px; text-decoration: none; color: inherit; transition: border-color 0.15s, transform 0.15s; position: relative; }
.town-card:hover { border-color: #0f172a; }
.town-card-region { font-size: 12px; color: #64748b; margin-bottom: 6px; letter-spacing: 0.02em; }
.town-card-name { font-size: 28px; font-weight: 800; color: #0f172a; letter-spacing: -0.02em; margin-bottom: 16px; }
.town-card-stat { font-size: 13px; color: #475569; padding: 4px 0; }
.town-card-stat b { color: #0f172a; font-weight: 700; font-variant-numeric: tabular-nums; }
.town-card-arrow { position: absolute; top: 24px; right: 24px; font-size: 20px; color: #94a3b8; }
.town-card:hover .town-card-arrow { color: #0f172a; }
.town-card.placeholder { border-style: dashed; background: #f8fafc; color: #94a3b8; }
.town-card.placeholder .town-card-name { color: #94a3b8; }

.hub-note { font-size: 13px; color: #64748b; padding: 16px 20px; background: #f8fafc; border-left: 4px solid #60a5fa; border-radius: 0 4px 4px 0; margin: 32px 0; }
</style>
</head>
<body>

<div class="topbar">
  <div class="wrap">
    <div class="topbar-inner">
      <div>
        <a href="/town/" class="brand">Q렌즈 동네 카드</a>
        <span class="brand-sub">보이는 것 너머를 묻습니다</span>
      </div>
      <a href="/" class="search-pill" style="text-decoration:none;">← Q렌즈 본 사이트</a>
    </div>
  </div>
</div>

<div class="wrap">

  <section class="hero">
    <div class="hero-eyebrow">동네를 데이터로 읽습니다</div>
    <h1>당신의 동네는<br>어떻게 보일까요?</h1>
    <p class="hero-tagline">주소 한 줄이면 그 동네의 인구·부동산·교육·환경·의료 데이터를 한 장에 정리해드립니다. 정부 공공데이터를 그대로, 그러나 의미 있게.</p>
    <div class="hero-meta">전국 자치구 단계적 공개 · 마지막 업데이트 <b>$updated</b></div>
  </section>

  <div class="hub-note">
    현재 <b>강남구 1개</b> 공개 중. 서울 25개 자치구는 데이터 검수 후 단계적으로 추가됩니다.<br>
    학원·사업장(LOCALDATA), 인구·소득(KOSIS) 데이터는 곧 보강됩니다.
  </div>

  <div class="hub-grid">
    $cards
  </div>

</div>

<footer>
  <div class="wrap">
    Q렌즈 · q-bot.kr ·
    <a href="/about/">소개</a>
    <a href="/town/">동네 카드 홈</a>
    <a href="/contact/">문의</a>
  </div>
</footer>

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-04MMSE99PJ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-04MMSE99PJ');
</script>

</body>
</html>
""")


def render_hub_card(data):
    """동네 데이터 1개 → 허브 카드 HTML."""
    sections = data.get("sections", {})
    trade = sections.get("real_estate_trade", {}) or {}
    med = sections.get("medical", {}) or {}
    edu = sections.get("education", {}) or {}

    ppy = trade.get("median_price_per_pyeong_man")
    med_count = med.get("gangnam_count") or med.get("sgg_count")
    edu_count = edu.get("gangnam_count") or edu.get("sgg_count")

    region = data.get("name_full", "").replace(data.get("name", ""), "").strip()

    stats = []
    if ppy:
        stats.append(f'<div class="town-card-stat">평당가 <b>{fmt_num(ppy)}만원</b></div>')
    if med_count:
        stats.append(f'<div class="town-card-stat">의료기관 <b>{fmt_num(med_count)}곳</b></div>')
    if edu_count:
        stats.append(f'<div class="town-card-stat">학교 <b>{fmt_num(edu_count)}개</b></div>')

    return (
        f'<a href="/town/{data["slug"]}/" class="town-card">'
        f'<div class="town-card-arrow">→</div>'
        f'<div class="town-card-region">{region}</div>'
        f'<div class="town-card-name">{data["name"]}</div>'
        + "".join(stats)
        + '</a>'
    )


def render_placeholder_cards(count=3):
    """미공개 자치구 placeholder."""
    items = ["서초구", "송파구", "마포구"][:count]
    return "".join(
        f'<div class="town-card placeholder">'
        f'<div class="town-card-region">서울특별시</div>'
        f'<div class="town-card-name">{name}</div>'
        f'<div class="town-card-stat">곧 공개</div>'
        f'</div>'
        for name in items
    )


def build_hub(all_data):
    """모든 동네 데이터 → 허브 페이지."""
    cards = "\n".join(render_hub_card(d) for d in all_data) + "\n" + render_placeholder_cards(3)

    # 가장 최근 페치 시각
    try:
        latest = max(d["fetched_at"] for d in all_data)
        dt = datetime.fromisoformat(latest.replace("Z", "+00:00"))
        updated = dt.strftime("%Y년 %m월 %d일")
    except Exception:
        updated = "—"

    return HUB_TEMPLATE.safe_substitute({
        "css": CSS,
        "cards": cards,
        "updated": updated,
    })


# ─────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────

def main():
    if not DATA_DIR.exists():
        print(f"❌ 데이터 디렉토리 없음: {DATA_DIR}", file=sys.stderr)
        sys.exit(1)

    data_files = sorted(DATA_DIR.rglob("*.json"))
    if not data_files:
        print(f"❌ 데이터 파일 없음: {DATA_DIR}/**/*.json", file=sys.stderr)
        sys.exit(1)

    all_data = []
    pages_built = []

    # 1. 개별 동네 페이지 빌드
    for f in data_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ✗ {f}: {e}", file=sys.stderr)
            continue

        html = build_page(data)
        out_dir = OUTPUT_BASE / data["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / "index.html"
        out.write_text(html, encoding="utf-8")
        all_data.append(data)
        pages_built.append((str(out), len(html)))
        print(f"  ✓ {out} ({len(html):,} bytes)")

    # 2. 허브 페이지 빌드
    hub_html = build_hub(all_data)
    hub_out = OUTPUT_BASE / "index.html"
    hub_out.write_text(hub_html, encoding="utf-8")
    print(f"  ✓ {hub_out} ({len(hub_html):,} bytes) [허브]")

    print(f"\n✓ 빌드 완료: {len(pages_built)}개 동네 + 허브 1개")

    summary_path = __import__("os").environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(f"# 빌드 결과\n\n")
            f.write(f"- 동네 페이지: **{len(pages_built)}개**\n")
            f.write(f"- 허브 페이지: 1개\n")
            f.write(f"- 허브 URL: https://q-bot.kr/town/\n\n")
            f.write("## 빌드 목록\n\n")
            for path, size in pages_built:
                f.write(f"- `{path}` ({size:,} bytes)\n")


if __name__ == "__main__":
    main()
