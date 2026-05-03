#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q렌즈 동네 카드 — 빌드 v3 (서울+경기 시도 그룹 셀렉터)"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

DATA_PATH = Path("town/data/seoul.json")
OUTPUT = Path("town/index.html")


PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Q렌즈 동네 카드 — 서울·경기 시군구 데이터</title>
<meta name="description" content="주소 한 줄이면 그 동네의 인구·부동산·교육·환경·의료 데이터를 한 장에. 서울 25개 자치구 + 경기 42개 시군구.">
<link rel="canonical" href="https://q-bot.kr/town/">
<meta property="og:title" content="Q렌즈 동네 카드">
<meta property="og:description" content="당신의 동네는 어떻게 보일까요? 서울·경기 67개 시군구.">
<meta property="og:url" content="https://q-bot.kr/town/">
<meta property="og:type" content="website">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { font-family: 'Pretendard Variable', Pretendard, -apple-system, sans-serif; background: #ffffff; color: #0f172a; font-feature-settings: 'tnum'; -webkit-font-smoothing: antialiased; line-height: 1.6; }
.wrap { max-width: 760px; margin: 0 auto; padding: 0 20px; }
.topbar { border-bottom: 1px solid #e5e7eb; padding: 14px 0; margin-bottom: 56px; }
.topbar-inner { display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
.brand { font-weight: 700; color: #0f172a; text-decoration: none; }
.brand-sub { color: #64748b; margin-left: 8px; font-weight: 500; }
.back-link { color: #475569; font-size: 13px; text-decoration: none; }
.hero { margin-bottom: 32px; }
.hero-eyebrow { font-size: 13px; color: #64748b; margin-bottom: 8px; letter-spacing: 0.02em; }
.hero h1 { font-size: 48px; font-weight: 800; line-height: 1.1; letter-spacing: -0.03em; color: #0f172a; margin-bottom: 12px; }
.hero-tagline { font-size: 17px; color: #475569; margin-bottom: 24px; max-width: 540px; }
.hero-meta { font-size: 12px; color: #94a3b8; padding-top: 12px; border-top: 1px solid #e5e7eb; }
.hero-meta b { color: #3182f6; font-weight: 600; }
.intro-note { background: #f8fafc; padding: 16px 20px; border-radius: 4px; font-size: 13px; color: #475569; line-height: 1.6; margin: 24px 0 32px; }
.intro-note b { color: #0f172a; }
.sido-section { margin: 32px 0 24px; }
.sido-header { font-size: 12px; color: #64748b; font-weight: 700; letter-spacing: 0.1em; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #0f172a; display: flex; justify-content: space-between; align-items: baseline; }
.sido-count { font-size: 11px; color: #94a3b8; font-weight: 500; letter-spacing: 0; }
.gu-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; margin-bottom: 24px; }
@media (max-width: 640px) {
  .gu-grid { grid-template-columns: repeat(3, 1fr); }
  .hero h1 { font-size: 36px; }
}
.gu-chip { display: block; padding: 12px 8px; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 4px; text-align: center; font-size: 13px; font-weight: 600; color: #475569; cursor: pointer; transition: all 0.12s; }
.gu-chip:hover { border-color: #0f172a; color: #0f172a; }
.gu-chip.active { background: #0f172a; color: #ffffff; border-color: #0f172a; }
.card-area { min-height: 400px; margin-top: 32px; }
.card-empty { text-align: center; padding: 64px 24px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 4px; color: #64748b; font-size: 14px; }
.card-name { font-size: 40px; font-weight: 800; letter-spacing: -0.03em; margin: 8px 0 12px; }
.card-region { font-size: 13px; color: #64748b; }
.ql-stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0; border: 1px solid #e5e7eb; border-radius: 4px; margin: 24px 0 56px; }
.ql-stat-cell { padding: 24px 20px; border-right: 1px solid #e5e7eb; }
.ql-stat-cell:last-child { border-right: none; }
.ql-stat-num { font-size: 32px; font-weight: 800; color: #0f172a; letter-spacing: -0.02em; line-height: 1.1; margin-bottom: 6px; }
.ql-stat-num .unit { font-size: 16px; color: #64748b; font-weight: 600; margin-left: 2px; }
.ql-stat-label { font-size: 12px; color: #64748b; font-weight: 500; }
@media (max-width: 640px) {
  .ql-stat-row { grid-template-columns: 1fr; }
  .ql-stat-cell { border-right: none; border-bottom: 1px solid #e5e7eb; }
  .ql-stat-cell:last-child { border-bottom: none; }
}
.section { margin-bottom: 56px; padding-top: 28px; border-top: 4px solid #0f172a; }
.section-num { font-size: 12px; color: #60a5fa; font-weight: 700; letter-spacing: 0.1em; }
.section h2 { font-size: 24px; font-weight: 800; letter-spacing: -0.02em; margin: 8px 0; }
.section-sub { font-size: 13px; color: #64748b; margin-bottom: 20px; }
.bar-block { margin: 20px 0; }
.bar-row { display: grid; grid-template-columns: 100px 1fr 80px; align-items: center; gap: 12px; padding: 7px 0; font-size: 13px; }
.bar-label { color: #475569; font-weight: 500; }
.bar-track { background: #f1f5f9; height: 8px; border-radius: 4px; overflow: hidden; }
.bar-fill { background: #0f172a; height: 100%; border-radius: 4px; }
.bar-fill.accent { background: #60a5fa; }
.bar-value { text-align: right; color: #0f172a; font-weight: 600; font-variant-numeric: tabular-nums; }
.kv-table { display: grid; grid-template-columns: 1fr 1fr; border: 1px solid #e5e7eb; border-radius: 4px; margin: 20px 0; font-size: 13px; overflow: hidden; }
.kv-cell { padding: 12px 16px; border-right: 1px solid #e5e7eb; border-bottom: 1px solid #e5e7eb; }
.kv-cell:nth-child(2n) { border-right: none; }
.kv-cell.label { color: #64748b; }
.kv-cell.val { color: #0f172a; font-weight: 600; font-variant-numeric: tabular-nums; }
.kv-cell.val.highlight { color: #3182f6; }
.insight { background: #f8fafc; border-left: 4px solid #60a5fa; padding: 16px 20px; margin: 20px 0; border-radius: 0 4px 4px 0; }
.insight-tag { font-size: 11px; font-weight: 700; color: #3182f6; letter-spacing: 0.1em; margin-bottom: 6px; }
.insight p { font-size: 14px; color: #0f172a; line-height: 1.65; }
.insight p b { font-weight: 700; }
.source { font-size: 11px; color: #94a3b8; margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9; }
footer { border-top: 1px solid #e5e7eb; padding: 32px 0 48px; font-size: 12px; color: #94a3b8; text-align: center; margin-top: 80px; }
footer a { color: #94a3b8; text-decoration: none; margin: 0 8px; }
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
      <a href="/" class="back-link">← Q렌즈 본 사이트</a>
    </div>
  </div>
</div>

<div class="wrap">

  <section class="hero">
    <div class="hero-eyebrow">서울·경기 67개 시군구</div>
    <h1>당신의 동네는<br>어떻게 보일까요?</h1>
    <p class="hero-tagline">시군구를 선택하면 그 동네의 인구·부동산·교육·환경·의료 데이터를 카드 한 장에 보여드립니다. 정부 공공데이터를 그대로, 그러나 의미 있게.</p>
    <div class="hero-meta">데이터 갱신 <b>__UPDATED__</b> · 출처 국토교통부·환경공단·심평원·교육부·통계청</div>
  </section>

  <div class="intro-note">
    아래에서 시군구를 선택하세요. 데이터는 매주 자동 갱신됩니다.
    학원·사업장(LOCALDATA), 인구 연령 분포는 곧 추가됩니다.
  </div>

  __SIDO_SECTIONS__

  <div class="card-area" id="card-area">
    <div class="card-empty">위에서 시군구를 선택하면 카드가 여기에 나타납니다</div>
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

<script async src="https://www.googletagmanager.com/gtag/js?id=G-04MMSE99PJ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-04MMSE99PJ');
</script>

<script id="town-data" type="application/json">
__DATA_JSON__
</script>

<script>
(function() {
  var raw = document.getElementById('town-data').textContent;
  var DATA = JSON.parse(raw);
  var RECORDS = {};
  DATA.records.forEach(function(r) {
    var key = r.slug.replace(/\\//g, '-');
    RECORDS[key] = r;
  });

  function fmtNum(n) {
    if (n === null || n === undefined) return '—';
    return Number(n).toLocaleString('ko-KR');
  }
  function fmtEok(man) {
    if (!man) return '—';
    var eok = man / 10000;
    if (eok >= 10) return Math.round(eok) + '억';
    return eok.toFixed(1) + '억';
  }
  function pct(value, max) {
    if (!value || !max) return 0;
    return Math.min(100, Math.round(value / max * 100));
  }
  function escapeHTML(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, function(c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }

  function insightRealEstate(rec) {
    var t = rec.sections.real_estate_trade || {};
    var r = rec.sections.real_estate_rent || {};
    var ppy = t.median_price_per_pyeong_man;
    var monthly = t.monthly_count_avg;
    var jeonse = r.median_jeonse_man;
    var trade = t.median_deal_amount_man;
    var ratio = (jeonse && trade) ? Math.round(jeonse / trade * 1000) / 10 : null;
    var parts = [];
    if (ppy) parts.push(rec.name + ' 아파트 평당가 중앙값은 <b>' + fmtNum(ppy) + '만원</b>');
    if (monthly) parts.push('월평균 매매 거래는 <b>' + Math.round(monthly) + '건</b>');
    if (ratio) parts.push('전세 중앙값 대비 매매 중앙값 비율은 <b>약 ' + ratio + '%</b>');
    if (parts.length === 0) return '거래 데이터가 부족해 분석을 보류합니다.';
    return parts.join(', ') + '입니다.';
  }
  function insightEnvironment(rec) {
    var env = rec.sections.environment || {};
    var avg = env.sido_avg || env.seoul_avg || {};
    var gu = env.gu_station || env.gangnam_station;
    var sidoLabel = rec.sido_name + ' 평균';
    if (gu && gu.pm25 !== null && avg.pm25 !== null) {
      var cmp = gu.pm25 < avg.pm25 ? '낮습니다' : (gu.pm25 > avg.pm25 ? '높습니다' : '같습니다');
      return env.measured_at + ' 기준 PM2.5는 ' + sidoLabel + '(<b>' + avg.pm25 + '</b>)보다 ' + rec.name + '(<b>' + gu.pm25 + '</b>)이 ' + cmp + '. 단일 시점 측정값입니다.';
    }
    if (avg.pm25 !== null) {
      return env.measured_at + ' 기준 ' + sidoLabel + ' PM2.5는 <b>' + avg.pm25 + ' µg</b>. ' + rec.name + ' 측정소는 다음 페치에 보강됩니다.';
    }
    return '환경 데이터를 받아오는 중입니다.';
  }
  function insightMedical(rec) {
    var m = rec.sections.medical || {};
    var t = m.sgg_count || 0;
    var byType = m.by_type || {};
    var eui = byType['의원'] || 0;
    var sang = byType['상급종합'] || 0;
    var jong = byType['종합병원'] || 0;
    if (!t) return rec.name + '의 의료기관 데이터를 수집 중입니다.';
    return rec.name + '에는 의료기관 <b>' + fmtNum(t) + '곳</b>이 있습니다. 의원 <b>' + fmtNum(eui) + '곳</b>, 상급종합 ' + sang + '곳, 종합병원 ' + jong + '곳.';
  }
  function insightEducation(rec) {
    var e = rec.sections.education || {};
    var t = e.sgg_count || 0;
    var by = e.by_type || {};
    if (!t) return rec.name + '의 학교 데이터를 수집 중입니다.';
    return rec.name + ' 정규 학교는 <b>' + t + '개</b> (초 <b>' + (by['초등학교'] || 0) + '</b> · 중 <b>' + (by['중학교'] || 0) + '</b> · 고 <b>' + (by['고등학교'] || 0) + '</b>). 학원·교습소 데이터는 곧 추가됩니다.';
  }
  function insightPopulation(rec) {
    var p = rec.sections.population || {};
    var g = p.sgg_total || p.gangnam_total;
    var sido = p.sido_total || p.seoul_total;
    var share = p.share_of_sido_pct || p.share_of_seoul_pct;
    var period = p.period;
    var sidoCount = (DATA.sido_list || []).find(function(s) { return s.code === rec.sido_code; });
    var nGu = sidoCount ? sidoCount.count : 0;
    if (!g) return rec.name + '의 인구 데이터를 수집 중입니다.';
    var periodStr = '';
    if (period && period.length === 6) periodStr = period.substr(0,4) + '년 ' + parseInt(period.substr(4),10) + '월 ';
    var avgGu = (sido && nGu) ? Math.round(sido / nGu) : null;
    var ratioText = '';
    if (avgGu && g) {
      var ratio = Math.round(g / avgGu * 100) / 100;
      ratioText = ' ' + rec.sido_name + ' ' + nGu + '개 시군구 평균(<b>' + fmtNum(avgGu) + '명</b>) 대비 <b>' + ratio + '배</b>.';
    }
    return periodStr + '기준 ' + rec.name + ' 인구는 <b>' + fmtNum(g) + '명</b>. ' + rec.sido_name + ' 전체의 <b>' + share + '%</b>를 차지합니다.' + ratioText;
  }

  function renderBar(label, value, max, unit, accent) {
    var p = pct(value, max);
    var cls = accent ? 'bar-fill accent' : 'bar-fill';
    var v = (value !== null && value !== undefined) ? fmtNum(value) + (unit ? ' ' + unit : '') : '—';
    return '<div class="bar-row"><div class="bar-label">' + escapeHTML(label) + '</div><div class="bar-track"><div class="' + cls + '" style="width:' + p + '%"></div></div><div class="bar-value">' + v + '</div></div>';
  }
  function renderRealEstate(rec) {
    var t = rec.sections.real_estate_trade || {};
    var r = rec.sections.real_estate_rent || {};
    var rows = [
      ['아파트 평당가 (중앙값)', t.median_price_per_pyeong_man ? fmtNum(t.median_price_per_pyeong_man) + ' 만원' : '—', true],
      ['매매 평균 거래액 (중앙값)', t.median_deal_amount_man ? fmtEok(t.median_deal_amount_man) : '—', false],
      ['월평균 매매 건수', t.monthly_count_avg ? Math.round(t.monthly_count_avg) + ' 건' : '—', false],
      ['전세 중앙값', r.median_jeonse_man ? fmtEok(r.median_jeonse_man) : '—', false],
      ['전세 / 월세 거래', (r.jeonse_count !== undefined ? r.jeonse_count : '—') + ' / ' + (r.monthly_count !== undefined ? r.monthly_count : '—') + ' 건', false],
    ];
    var ratio = (r.median_jeonse_man && t.median_deal_amount_man) ? Math.round(r.median_jeonse_man / t.median_deal_amount_man * 1000)/10 : null;
    rows.push(['매매-전세 비율(단순)', ratio !== null ? ratio + ' %' : '—', false]);
    var html = '<div class="kv-table">';
    rows.forEach(function(row) {
      var cls = row[2] ? 'kv-cell val highlight' : 'kv-cell val';
      html += '<div class="kv-cell label">' + escapeHTML(row[0]) + '</div><div class="' + cls + '">' + row[1] + '</div>';
    });
    html += '</div>';
    return html;
  }
  function renderEnvironment(rec) {
    var env = rec.sections.environment || {};
    var avg = env.sido_avg || env.seoul_avg || {};
    var gu = env.gu_station || env.gangnam_station;
    var bars = [];
    if (avg.pm10 !== null) bars.push(renderBar('PM10 (' + rec.sido_name + ')', avg.pm10, 100, 'µg', false));
    if (gu && gu.pm10 !== null && gu.pm10 !== undefined) bars.push(renderBar('PM10 (' + rec.name + ')', gu.pm10, 100, 'µg', true));
    if (avg.pm25 !== null) bars.push(renderBar('PM2.5 (' + rec.sido_name + ')', avg.pm25, 50, 'µg', false));
    if (gu && gu.pm25 !== null && gu.pm25 !== undefined) bars.push(renderBar('PM2.5 (' + rec.name + ')', gu.pm25, 50, 'µg', true));
    return bars.length ? '<div class="bar-block">' + bars.join('') + '</div>' : '<p style="color:#94a3b8;font-size:13px;">측정소 데이터 없음</p>';
  }
  function renderMedical(rec) {
    var m = rec.sections.medical || {};
    var by = m.by_type || {};
    var entries = Object.keys(by).map(function(k) { return [k, by[k]]; }).sort(function(a, b) { return b[1] - a[1]; });
    if (!entries.length) return '<p style="color:#94a3b8;font-size:13px;">데이터 없음</p>';
    var max = entries[0][1];
    return '<div class="bar-block">' + entries.map(function(e) { return renderBar(e[0], e[1], max, '곳', false); }).join('') + '</div>';
  }
  function renderEducation(rec) {
    var e = rec.sections.education || {};
    var by = e.by_type || {};
    var main = ['초등학교', '중학교', '고등학교', '특수학교'];
    var rows = main.filter(function(k) { return by[k]; }).map(function(k) { return [k, by[k]]; });
    var other = 0;
    Object.keys(by).forEach(function(k) { if (main.indexOf(k) === -1) other += by[k]; });
    if (other) rows.push(['기타', other]);
    if (!rows.length) return '<p style="color:#94a3b8;font-size:13px;">데이터 없음</p>';
    var max = Math.max.apply(null, rows.map(function(r) { return r[1]; }));
    return '<div class="bar-block">' + rows.map(function(r) { return renderBar(r[0], r[1], max, '개', false); }).join('') + '</div>';
  }
  function renderPopulation(rec) {
    var p = rec.sections.population || {};
    var g = p.sgg_total || p.gangnam_total;
    var sido = p.sido_total || p.seoul_total;
    var sidoCount = (DATA.sido_list || []).find(function(s) { return s.code === rec.sido_code; });
    var nGu = sidoCount ? sidoCount.count : 0;
    if (!g) return '<p style="color:#94a3b8;font-size:13px;">데이터 없음</p>';
    var avgGu = (sido && nGu) ? Math.round(sido / nGu) : null;
    var max = avgGu ? Math.max(g, avgGu) : g;
    var bars = [renderBar(rec.name, g, max, '명', true)];
    if (avgGu) bars.push(renderBar(rec.sido_name + ' 시군구 평균', avgGu, max, '명', false));
    if (sido) bars.push(renderBar(rec.sido_name + ' 전체', sido, Math.max(sido, max), '명', false));
    return '<div class="bar-block">' + bars.join('') + '</div>';
  }

  function buildCard(rec) {
    var t = rec.sections.real_estate_trade || {};
    var r = rec.sections.real_estate_rent || {};
    var p = rec.sections.population || {};
    var medianPyeong = t.median_price_per_pyeong_man;
    var medianJeonse = r.median_jeonse_man;
    var popTotal = p.sgg_total || p.gangnam_total;

    var stat1 = medianPyeong ? '<div class="ql-stat-num">' + fmtNum(medianPyeong) + '<span class="unit">만원</span></div><div class="ql-stat-label">아파트 평당가 (중앙값)</div>' : '<div class="ql-stat-num">—</div><div class="ql-stat-label">아파트 평당가</div>';
    var stat2 = medianJeonse ? '<div class="ql-stat-num">' + fmtEok(medianJeonse).replace('억','') + '<span class="unit">억</span></div><div class="ql-stat-label">전세 중앙값</div>' : '<div class="ql-stat-num">—</div><div class="ql-stat-label">전세 중앙값</div>';
    var stat3 = popTotal ? '<div class="ql-stat-num">' + fmtNum(popTotal) + '<span class="unit">명</span></div><div class="ql-stat-label">인구 (주민등록 기준)</div>' : '<div class="ql-stat-num">—</div><div class="ql-stat-label">인구</div>';

    return ''
      + '<div class="card-region">' + escapeHTML(rec.name_full) + '</div>'
      + '<div class="card-name">' + escapeHTML(rec.name) + '</div>'
      + '<div class="ql-stat-row">'
      + '<div class="ql-stat-cell">' + stat1 + '</div>'
      + '<div class="ql-stat-cell">' + stat2 + '</div>'
      + '<div class="ql-stat-cell">' + stat3 + '</div>'
      + '</div>'
      + '<section class="section">'
      + '<div class="section-num">01 — 부동산</div><h2>집값과 거래의 흐름</h2>'
      + '<p class="section-sub">최근 3개월 아파트 매매·전월세 실거래.</p>'
      + renderRealEstate(rec)
      + '<div class="insight"><div class="insight-tag">Q렌즈의 시각</div><p>' + insightRealEstate(rec) + '</p></div>'
      + '<div class="source">출처: 국토교통부 실거래가 공개시스템</div></section>'
      + '<section class="section">'
      + '<div class="section-num">02 — 환경</div><h2>공기와 측정값</h2>'
      + '<p class="section-sub">에어코리아 시도/측정소 실시간.</p>'
      + renderEnvironment(rec)
      + '<div class="insight"><div class="insight-tag">Q렌즈의 시각</div><p>' + insightEnvironment(rec) + '</p></div>'
      + '<div class="source">출처: 한국환경공단 에어코리아</div></section>'
      + '<section class="section">'
      + '<div class="section-num">03 — 의료</div><h2>병원·의원 분포</h2>'
      + '<p class="section-sub">시군구 내 의료기관 종별.</p>'
      + renderMedical(rec)
      + '<div class="insight"><div class="insight-tag">Q렌즈의 시각</div><p>' + insightMedical(rec) + '</p></div>'
      + '<div class="source">출처: 건강보험심사평가원</div></section>'
      + '<section class="section">'
      + '<div class="section-num">04 — 교육</div><h2>학교 분포</h2>'
      + '<p class="section-sub">시군구 내 정규 학교.</p>'
      + renderEducation(rec)
      + '<div class="insight"><div class="insight-tag">Q렌즈의 시각</div><p>' + insightEducation(rec) + '</p></div>'
      + '<div class="source">출처: 교육부 NEIS</div></section>'
      + '<section class="section">'
      + '<div class="section-num">05 — 인구</div><h2>누가 살고 있나</h2>'
      + '<p class="section-sub">행정안전부 주민등록인구 — 동네의 골격.</p>'
      + renderPopulation(rec)
      + '<div class="insight"><div class="insight-tag">Q렌즈의 시각</div><p>' + insightPopulation(rec) + '</p></div>'
      + '<div class="source">출처: 통계청 KOSIS · 주민등록인구 (DT_1B040A3)</div></section>';
  }

  function selectGu(slugKey, pushState) {
    var rec = RECORDS[slugKey];
    var area = document.getElementById('card-area');
    if (!rec) {
      area.innerHTML = '<div class="card-empty">시군구 데이터를 찾을 수 없습니다</div>';
      return;
    }
    area.innerHTML = buildCard(rec);
    document.querySelectorAll('.gu-chip').forEach(function(el) {
      el.classList.toggle('active', el.dataset.slugkey === slugKey);
    });
    if (pushState && history.pushState) {
      history.pushState({slug: slugKey}, '', '?gu=' + slugKey);
    }
    document.title = rec.name + ' — Q렌즈 동네 카드';
    area.scrollIntoView({behavior: 'smooth', block: 'start'});
  }

  document.querySelectorAll('.gu-chip').forEach(function(chip) {
    chip.addEventListener('click', function() {
      selectGu(chip.dataset.slugkey, true);
    });
  });

  window.addEventListener('popstate', function() {
    var slug = (new URLSearchParams(location.search)).get('gu');
    if (slug) selectGu(slug, false);
  });

  var initialSlug = (new URLSearchParams(location.search)).get('gu');
  if (initialSlug) {
    // backward compat: ?gu=gangnam → seoul-gangnam
    if (RECORDS[initialSlug]) {
      selectGu(initialSlug, false);
    } else if (RECORDS['seoul-' + initialSlug]) {
      selectGu('seoul-' + initialSlug, false);
    } else if (RECORDS['gyeonggi-' + initialSlug]) {
      selectGu('gyeonggi-' + initialSlug, false);
    }
  }
})();
</script>

</body>
</html>
"""


def main():
    if not DATA_PATH.exists():
        print(f"❌ 데이터 파일 없음: {DATA_PATH}", file=sys.stderr)
        sys.exit(1)

    raw = DATA_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    records = data.get("records", [])
    sido_list = data.get("sido_list", [])
    print(f"  로드: {len(records)}개 시군구 ({len(sido_list)}개 시도)")

    # 시도별 섹션 HTML 생성
    sections_html = []
    for sido in sido_list:
        sido_records = [r for r in records if r.get("sido_code") == sido["code"]]
        chips = []
        for rec in sido_records:
            slug_key = rec["slug"].replace("/", "-")
            chips.append(f'<a class="gu-chip" data-slugkey="{slug_key}">{rec["name"]}</a>')
        chips_html = "\n      ".join(chips)
        sections_html.append(
            f'  <div class="sido-section">\n'
            f'    <div class="sido-header">{sido["name"]}<span class="sido-count">{len(sido_records)}개 시군구</span></div>\n'
            f'    <div class="gu-grid">\n      {chips_html}\n    </div>\n'
            f'  </div>'
        )
    sido_sections = "\n".join(sections_html)

    try:
        dt = datetime.fromisoformat(data["fetched_at"].replace("Z", "+00:00"))
        updated = dt.strftime("%Y년 %m월 %d일")
    except Exception:
        updated = "—"

    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    html = (PAGE
            .replace("__SIDO_SECTIONS__", sido_sections)
            .replace("__UPDATED__", updated)
            .replace("__DATA_JSON__", data_json))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"  ✓ {OUTPUT} ({len(html):,} bytes)")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"# 빌드 결과\n\n- 페이지: `{OUTPUT}`\n- 크기: {len(html):,} bytes\n- 시군구: {len(records)}\n")


if __name__ == "__main__":
    main()
