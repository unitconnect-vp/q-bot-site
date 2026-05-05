#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q렌즈 동네 카드 — 빌드 v3 (서울+경기 시도 그룹 셀렉터)"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

DATA_PATH = Path("town/data/all.json")
OUTPUT = Path("town/index.html")


PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Q렌즈 동네 카드 — 전국 시군구 데이터</title>
<meta name="description" content="주소 한 줄이면 그 동네의 인구·부동산·교육·환경·의료 데이터를 한 장에. 전국 17개 시도 시군구.">
<link rel="canonical" href="https://q-bot.kr/town/">
<meta property="og:title" content="Q렌즈 동네 카드">
<meta property="og:description" content="당신의 동네는 어떻게 보일까요? 전국 시군구 데이터.">
<meta property="og:url" content="https://q-bot.kr/town/">
<link href="/assets/style.css" rel="stylesheet">
<meta property="og:type" content="website">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { font-family: 'Pretendard Variable', Pretendard, -apple-system, sans-serif; background: #ffffff; color: #0f172a; font-feature-settings: 'tnum'; -webkit-font-smoothing: antialiased; line-height: 1.6; }
.wrap { max-width: 760px; margin: 0 auto; padding: 0 20px; }
.hero { margin-bottom: 32px; }
.hero-eyebrow { font-size: 13px; color: #64748b; margin-bottom: 8px; letter-spacing: 0.02em; }
.hero h1 { font-size: 48px; font-weight: 800; line-height: 1.1; letter-spacing: -0.03em; color: #0f172a; margin-bottom: 12px; }
.hero-tagline { font-size: 17px; color: #475569; margin-bottom: 24px; max-width: 540px; }
.hero-meta { font-size: 12px; color: #94a3b8; padding-top: 12px; border-top: 1px solid #e5e7eb; }
.hero-meta b { color: #3182f6; font-weight: 600; }
.intro-note { background: #f8fafc; padding: 16px 20px; border-radius: 4px; font-size: 13px; color: #475569; line-height: 1.6; margin: 24px 0 32px; }
.intro-note b { color: #0f172a; }
.filter-bar { position: sticky; top: 0; background: #ffffff; padding: 12px 0 8px; z-index: 10; margin-bottom: 16px; }
.filter-input-wrap { position: relative; margin-bottom: 10px; }
.filter-input { width: 100%; padding: 12px 40px 12px 16px; font-size: 15px; border: 1.5px solid #e5e7eb; border-radius: 4px; font-family: inherit; background: #fff; outline: none; transition: border-color 0.15s; }
.filter-input:focus { border-color: #0f172a; }
.filter-input-clear { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); width: 28px; height: 28px; border: none; background: #f3f4f6; color: #6b7280; border-radius: 50%; cursor: pointer; font-size: 16px; font-weight: 700; display: none; align-items: center; justify-content: center; padding: 0; line-height: 1; }
.filter-input-clear:hover { background: #e5e7eb; color: #0f172a; }
.filter-input-clear.show { display: flex; }
.region-row { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.region-chip { flex: 0 0 auto; padding: 10px 16px; background: #fff; border: 1.5px solid #e5e7eb; border-radius: 4px; font-size: 14px; font-weight: 700; color: #0f172a; cursor: pointer; transition: all 0.12s; user-select: none; font-family: inherit; }
.region-chip:hover { border-color: #0f172a; }
.region-chip.active { background: #3182f6; color: #fff; border-color: #3182f6; }
.region-chip .count { opacity: 0.65; font-weight: 500; margin-left: 5px; font-size: 12px; }
.region-chip.active .count { opacity: 0.85; }
.sido-chips { display: flex; gap: 6px; overflow-x: auto; padding: 2px 0 8px; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
.sido-chips::-webkit-scrollbar { display: none; }
.sido-chip { flex-shrink: 0; padding: 8px 16px; background: #fff; border: 1px solid #e5e7eb; border-radius: 999px; font-size: 14px; font-weight: 600; color: #475569; cursor: pointer; transition: all 0.12s; white-space: nowrap; user-select: none; font-family: inherit; }
.sido-chip:hover { border-color: #0f172a; color: #0f172a; }
.sido-chip.active { background: #0f172a; color: #fff; border-color: #0f172a; }
.sido-chip .count { opacity: 0.6; font-weight: 500; margin-left: 4px; font-size: 12px; }
.sido-chip.active .count { opacity: 0.7; }
.sido-chip.hidden { display: none; }
.sgg-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 32px; }
.sgg-card { display: block; padding: 16px 14px; background: #fff; border: 1px solid #e5e7eb; border-radius: 4px; text-align: left; cursor: pointer; transition: all 0.12s; position: relative; }
.sgg-card:hover { border-color: #0f172a; }
.sgg-card.active { background: #0f172a; border-color: #0f172a; }
.sgg-card.active .sgg-name, .sgg-card.active .sgg-sido { color: #fff; }
.sgg-card.active .sgg-sido { opacity: 0.7; }
.sgg-card.in-compare { border-color: #3182f6; border-width: 2px; }
.sgg-card.in-compare::after { content: '비교중'; position: absolute; top: 6px; right: 6px; font-size: 10px; font-weight: 700; color: #3182f6; background: #eff6ff; padding: 2px 6px; border-radius: 3px; }
.sgg-name { font-size: 17px; font-weight: 700; color: #0f172a; line-height: 1.25; letter-spacing: -0.01em; }
.sgg-sido { font-size: 13px; color: #94a3b8; font-weight: 500; margin-top: 4px; }
.result-meta { font-size: 13px; color: #64748b; margin-bottom: 14px; padding-left: 2px; font-weight: 500; }
.empty-state { text-align: center; padding: 40px 20px; color: #94a3b8; font-size: 14px; }
.empty-state b { color: #475569; }
@media (max-width: 640px) {
  .sgg-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .sgg-card { padding: 14px 12px; }
  .sgg-name { font-size: 16px; }
  .sgg-sido { font-size: 12px; }
  .filter-bar { padding: 10px 0 6px; }
  .sido-chip { padding: 7px 14px; font-size: 13px; }
  .region-chip { padding: 9px 14px; font-size: 13px; flex: 1 1 calc(50% - 4px); text-align: center; }
}
/* 비교 모드 UI */
.compare-bar { background: #f0f9ff; border: 1.5px solid #3182f6; border-radius: 6px; padding: 14px 16px; margin-bottom: 24px; display: none; }
.compare-bar.active { display: block; }
.compare-bar-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.compare-bar-title { font-size: 14px; font-weight: 700; color: #0f172a; }
.compare-bar-actions { display: flex; gap: 8px; }
.compare-btn { padding: 6px 12px; font-size: 12px; font-weight: 700; border-radius: 4px; cursor: pointer; border: none; font-family: inherit; }
.compare-btn-primary { background: #3182f6; color: #fff; }
.compare-btn-primary:disabled { background: #cbd5e1; cursor: not-allowed; }
.compare-btn-ghost { background: #fff; color: #475569; border: 1px solid #cbd5e1; }
.compare-slots { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.compare-slot { background: #fff; border: 1px dashed #93c5fd; border-radius: 4px; padding: 10px 12px; min-height: 56px; display: flex; flex-direction: column; justify-content: center; position: relative; }
.compare-slot.filled { border-style: solid; border-color: #3182f6; }
.compare-slot-empty { color: #94a3b8; font-size: 12px; text-align: center; }
.compare-slot-name { font-size: 14px; font-weight: 700; color: #0f172a; line-height: 1.2; }
.compare-slot-sido { font-size: 11px; color: #64748b; margin-top: 2px; }
.compare-slot-remove { position: absolute; top: 4px; right: 4px; width: 20px; height: 20px; border: none; background: #f3f4f6; color: #6b7280; border-radius: 50%; cursor: pointer; font-size: 12px; line-height: 1; padding: 0; }
.compare-slot-remove:hover { background: #fee2e2; color: #ef4444; }
.toggle-compare-btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px; background: #fff; border: 1.5px solid #3182f6; border-radius: 4px; color: #3182f6; font-size: 13px; font-weight: 700; cursor: pointer; font-family: inherit; margin-bottom: 14px; }
.toggle-compare-btn.active { background: #3182f6; color: #fff; }
.toggle-compare-btn:hover { background: #eff6ff; }
.toggle-compare-btn.active:hover { background: #1d4ed8; }
.card-add-compare { display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px; background: #fff; border: 1.5px solid #3182f6; border-radius: 4px; color: #3182f6; font-size: 13px; font-weight: 700; cursor: pointer; font-family: inherit; margin: 0 0 24px; }
.card-add-compare:hover { background: #eff6ff; }
.card-add-compare.added { background: #3182f6; color: #fff; }
@media (max-width: 640px) {
  .compare-slots { grid-template-columns: 1fr; }
}
/* 추세 차트 (월별 라인) */
.trend-block { margin: 20px 0 12px; }
.trend-title { font-size: 13px; font-weight: 700; color: #0f172a; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: baseline; }
.trend-title-delta { font-size: 12px; font-weight: 600; }
.trend-title-delta.up { color: #ef4444; }
.trend-title-delta.down { color: #3182f6; }
.trend-title-delta.flat { color: #94a3b8; }
.trend-svg { width: 100%; height: 80px; display: block; }
.trend-axis { font-size: 10px; color: #94a3b8; display: flex; justify-content: space-between; margin-top: 4px; padding: 0 2px; }
.trend-empty { font-size: 12px; color: #94a3b8; padding: 12px; background: #f8fafc; border-radius: 4px; text-align: center; }
/* 비교 패널 (사이드바이사이드) */
.compare-panel { background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 24px; margin-top: 32px; }
.compare-panel-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 4px solid #0f172a; }
.compare-panel-head h2 { font-size: 24px; font-weight: 800; letter-spacing: -0.02em; }
.compare-panel-close { background: none; border: none; color: #64748b; font-size: 14px; cursor: pointer; font-family: inherit; }
.compare-panel-close:hover { color: #0f172a; }
.compare-grid { display: grid; gap: 16px; margin-bottom: 24px; }
.compare-grid.cols-2 { grid-template-columns: repeat(2, 1fr); }
.compare-grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
.compare-col { padding: 16px; background: #f8fafc; border-radius: 4px; }
.compare-col-name { font-size: 16px; font-weight: 800; color: #0f172a; margin-bottom: 4px; }
.compare-col-sido { font-size: 11px; color: #64748b; margin-bottom: 16px; }
.compare-row { display: grid; padding: 12px 0; border-bottom: 1px solid #e5e7eb; align-items: baseline; gap: 8px; }
.compare-row.cols-2 { grid-template-columns: 110px repeat(2, 1fr); }
.compare-row.cols-3 { grid-template-columns: 110px repeat(3, 1fr); }
.compare-row:last-child { border-bottom: none; }
.compare-row-label { font-size: 12px; color: #64748b; font-weight: 500; }
.compare-row-val { font-size: 14px; font-weight: 700; color: #0f172a; font-variant-numeric: tabular-nums; }
.compare-row-val.best { color: #3182f6; }
.compare-row-val.worst { color: #ef4444; }
.compare-row-val.dim { color: #cbd5e1; font-weight: 500; }
@media (max-width: 640px) {
  .compare-grid.cols-2, .compare-grid.cols-3 { grid-template-columns: 1fr; }
  .compare-row.cols-2 { grid-template-columns: 100px 1fr 1fr; font-size: 12px; }
  .compare-row.cols-3 { grid-template-columns: 90px repeat(3, 1fr); font-size: 11px; }
  .compare-row-val { font-size: 13px; }
  .compare-panel { padding: 16px; }
}
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

<header class="site-header">
  <a class="site-logo" href="/"><h1 style="display:inline;font:inherit;margin:0;padding:0;">Q<span>-</span>Lens</h1></a>
  <nav class="site-nav">
    <a href="/">홈</a>
    <a href="/town/">동네 카드</a>
    <a href="/tools/">계산기</a>
    <a href="/articles/">글</a>
  </nav>
</header>

<div class="wrap">

  <section class="hero">
    <div class="hero-eyebrow">전국 __TOTAL_COUNT__개 시군구</div>
    <h1>당신의 동네는<br>어떻게 보일까요?</h1>
    <p class="hero-tagline">시군구를 선택하면 그 동네의 인구·부동산·교육·환경·의료 데이터를 카드 한 장에 보여드립니다.</p>
    <div class="hero-meta">데이터 갱신 <b>__UPDATED__</b> · 출처 국토교통부·환경공단·심평원·교육부·통계청</div>
  </section>


  <div class="intro-note">
    아래에서 시군구를 선택하세요. 데이터는 매주 자동 갱신됩니다.
    학원·사업장(LOCALDATA), 인구 연령 분포는 곧 추가됩니다.
  </div>

  <button class="toggle-compare-btn" id="toggle-compare" aria-pressed="false">⊕ 비교 모드</button>

  <div class="compare-bar" id="compare-bar">
    <div class="compare-bar-head">
      <div class="compare-bar-title">비교할 동네 선택 (최대 3개)</div>
      <div class="compare-bar-actions">
        <button class="compare-btn compare-btn-ghost" id="compare-clear">전체 비우기</button>
        <button class="compare-btn compare-btn-primary" id="compare-show" disabled>비교 보기</button>
      </div>
    </div>
    <div class="compare-slots" id="compare-slots">
      <div class="compare-slot" data-slot="0"><div class="compare-slot-empty">슬롯 1 비어있음</div></div>
      <div class="compare-slot" data-slot="1"><div class="compare-slot-empty">슬롯 2 비어있음</div></div>
      <div class="compare-slot" data-slot="2"><div class="compare-slot-empty">슬롯 3 비어있음</div></div>
    </div>
  </div>

  __SIDO_SECTIONS__

  <div class="card-area" id="card-area">
    <div class="card-empty">위에서 시군구를 선택하면 카드가 여기에 나타납니다</div>
  </div>

  <div class="compare-panel" id="compare-panel" style="display:none;">
    <div class="compare-panel-head">
      <h2>동네 비교</h2>
      <button class="compare-panel-close" id="compare-panel-close">✕ 닫기</button>
    </div>
    <div id="compare-panel-body"></div>
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
    RECORDS[r.slug] = r;
  });

  // 비교 모드 전역 상태
  var COMPARE_STATE = {
    enabled: false,
    slots: []  // 최대 3개 슬러그
  };
  window.__COMPARE = COMPARE_STATE;

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
    var yearly = env.pm25_yearly;
    var bars = [];
    // 1년 평균 (KOSIS) — 가장 위
    if (yearly && yearly.pm25_yearly !== null && yearly.pm25_yearly !== undefined) {
      bars.push(renderBar('PM2.5 1년 평균 (' + rec.sido_name + ')', yearly.pm25_yearly, 50, 'µg', true));
    }
    // 실시간 시도 평균
    if (avg.pm10 !== null) bars.push(renderBar('PM10 실시간 (' + rec.sido_name + ')', avg.pm10, 100, 'µg', false));
    if (gu && gu.pm10 !== null && gu.pm10 !== undefined) bars.push(renderBar('PM10 실시간 (' + rec.name + ')', gu.pm10, 100, 'µg', true));
    if (avg.pm25 !== null) bars.push(renderBar('PM2.5 실시간 (' + rec.sido_name + ')', avg.pm25, 50, 'µg', false));
    if (gu && gu.pm25 !== null && gu.pm25 !== undefined) bars.push(renderBar('PM2.5 실시간 (' + rec.name + ')', gu.pm25, 50, 'µg', true));
    return bars.length ? '<div class="bar-block">' + bars.join('') + '</div>' : '<p style="color:#94a3b8;font-size:13px;">측정소 데이터 없음</p>';
  }
  function renderMedical(rec) {
    var m = rec.sections.medical || {};
    var by = m.by_type || {};
    // 의료기관 위계 순서: 최상위 시설 → 작은 규모
    var ORDER = ['상급종합','종합병원','병원','요양병원','정신병원','치과병원','한방병원','의원','치과의원','한의원','조산원','보건의료원','보건소','보건지소','보건진료소'];
    var entries = [];
    ORDER.forEach(function(k) { if (by[k]) entries.push([k, by[k]]); });
    Object.keys(by).forEach(function(k) { if (ORDER.indexOf(k) === -1 && by[k]) entries.push([k, by[k]]); });
    if (!entries.length) return '<p style="color:#94a3b8;font-size:13px;">데이터 없음</p>';
    var max = Math.max.apply(null, entries.map(function(e) { return e[1]; }));
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

  function renderTrend(rec) {
    var t = rec.sections.real_estate_trade || {};
    var monthly = t.monthly_breakdown;
    if (!monthly || monthly.length < 2) {
      return '<div class="trend-block">'
        + '<div class="trend-title">월별 거래량·가격 추이</div>'
        + '<div class="trend-empty">시계열 데이터는 다음 데이터 갱신 후 표시됩니다 (12개월 누적 후 차트 활성화).</div>'
        + '</div>';
    }
    // 거래량 라인 + 평당가 라인 (정규화)
    var counts = monthly.map(function(m) { return m.count || 0; });
    var prices = monthly.map(function(m) { return m.median_price_per_pyeong_man || 0; });
    var maxC = Math.max.apply(null, counts) || 1;
    var maxP = Math.max.apply(null, prices) || 1;
    var minP = Math.min.apply(null, prices.filter(function(x) { return x > 0; })) || 0;
    var W = 600, H = 80, pad = 6;
    function lineCount() {
      return counts.map(function(v, i) {
        var x = pad + (W - 2*pad) * (i / (counts.length - 1));
        var y = H - pad - (H - 2*pad) * (v / maxC);
        return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1);
      }).join(' ');
    }
    function linePrice() {
      var range = maxP - minP || 1;
      return prices.map(function(v, i) {
        var x = pad + (W - 2*pad) * (i / (prices.length - 1));
        var y = v > 0 ? (H - pad - (H - 2*pad) * ((v - minP) / range)) : (H/2);
        return (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1);
      }).join(' ');
    }
    // 평당가 변화율 (첫 vs 마지막)
    var first = prices.find(function(p) { return p > 0; });
    var last = prices.slice().reverse().find(function(p) { return p > 0; });
    var deltaHTML = '';
    if (first && last) {
      var pct = Math.round((last - first) / first * 1000) / 10;
      var cls = pct > 1 ? 'up' : (pct < -1 ? 'down' : 'flat');
      var sign = pct > 0 ? '+' : '';
      deltaHTML = '<span class="trend-title-delta ' + cls + '">평당가 ' + sign + pct + '%</span>';
    }
    var firstYM = monthly[0].ym || '';
    var lastYM = monthly[monthly.length-1].ym || '';
    function ymLabel(s) { return s.length === 6 ? s.substr(2,2)+'.'+s.substr(4,2) : s; }
    return '<div class="trend-block">'
      + '<div class="trend-title"><span>월별 거래량 (선) · 평당가 변동 (점선)</span>' + deltaHTML + '</div>'
      + '<svg class="trend-svg" viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none">'
      + '<path d="' + lineCount() + '" fill="none" stroke="#0f172a" stroke-width="2" />'
      + '<path d="' + linePrice() + '" fill="none" stroke="#3182f6" stroke-width="2" stroke-dasharray="4 3" />'
      + '</svg>'
      + '<div class="trend-axis"><span>' + ymLabel(firstYM) + '</span><span>' + ymLabel(lastYM) + '</span></div>'
      + '</div>';
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

    var inCompare = COMPARE_STATE.slots.indexOf(rec.slug) !== -1;
    var addBtnLabel = inCompare ? '✓ 비교 슬롯에 추가됨' : '⊕ 비교에 추가';
    var addBtnCls = inCompare ? 'card-add-compare added' : 'card-add-compare';

    return ''
      + '<div class="card-region">' + escapeHTML(rec.name_full) + '</div>'
      + '<div class="card-name">' + escapeHTML(rec.name) + '</div>'
      + '<button class="' + addBtnCls + '" data-slug="' + escapeHTML(rec.slug) + '" id="card-add-compare-btn">' + addBtnLabel + '</button>'
      + '<div class="ql-stat-row">'
      + '<div class="ql-stat-cell">' + stat1 + '</div>'
      + '<div class="ql-stat-cell">' + stat2 + '</div>'
      + '<div class="ql-stat-cell">' + stat3 + '</div>'
      + '</div>'
      + '<section class="section">'
      + '<div class="section-num">01 — 부동산</div><h2>집값과 거래의 흐름</h2>'
      + '<p class="section-sub">최근 3개월 아파트 매매·전월세 실거래.</p>'
      + renderRealEstate(rec)
      + renderTrend(rec)
      + '<div class="insight"><div class="insight-tag">Q렌즈의 시각</div><p>' + insightRealEstate(rec) + '</p></div>'
      + '<div class="source">출처: 국토교통부 실거래가 공개시스템</div></section>'
      + '<section class="section">'
      + '<div class="section-num">02 — 의료</div><h2>병원·의원 분포</h2>'
      + '<p class="section-sub">시군구 내 의료기관 종별.</p>'
      + renderMedical(rec)
      + '<div class="insight"><div class="insight-tag">Q렌즈의 시각</div><p>' + insightMedical(rec) + '</p></div>'
      + '<div class="source">출처: 건강보험심사평가원</div></section>'
      + '<section class="section">'
      + '<div class="section-num">03 — 교육</div><h2>학교 분포</h2>'
      + '<p class="section-sub">시군구 내 정규 학교.</p>'
      + renderEducation(rec)
      + '<div class="insight"><div class="insight-tag">Q렌즈의 시각</div><p>' + insightEducation(rec) + '</p></div>'
      + '<div class="source">출처: 교육부 NEIS</div></section>'
      + '<section class="section">'
      + '<div class="section-num">04 — 인구</div><h2>누가 살고 있나</h2>'
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
    document.querySelectorAll('.sgg-card').forEach(function(el) {
      el.classList.toggle('active', el.dataset.slugkey === slugKey);
    });
    if (pushState && history.pushState) {
      history.pushState({slug: slugKey}, '', '?gu=' + slugKey);
    }
    document.title = rec.name + ' — Q렌즈 동네 카드';
    // 카드 내 "비교 추가" 버튼
    var addBtn = document.getElementById('card-add-compare-btn');
    if (addBtn) {
      addBtn.addEventListener('click', function() {
        toggleCompareSlot(addBtn.dataset.slug);
      });
    }
    area.scrollIntoView({behavior: 'smooth', block: 'start'});
  }

  

  document.querySelectorAll('.sgg-card').forEach(function(chip) {
    chip.addEventListener('click', function(e) {
      e.preventDefault();
      if (COMPARE_STATE.enabled) {
        toggleCompareSlot(chip.dataset.slugkey);
      } else {
        selectGu(chip.dataset.slugkey, true);
      }
    });
  });

  window.addEventListener('popstate', function() {
    var slug = (new URLSearchParams(location.search)).get('gu');
    if (slug) selectGu(slug, false);
  });

  var initialSlug = (new URLSearchParams(location.search)).get('gu');
  if (initialSlug) {
    // backward compat
    var legacyMap = {
      'gangnam': '11680', 'seocho': '11650', 'songpa': '11710', 'gangdong': '11740',
      'gangseo': '11500', 'mapo': '11440', 'yongsan': '11170', 'jongno': '11110',
      'seoul-gangnam': '11680', 'seoul-seocho': '11650', 'seoul-songpa': '11710',
      'seoul-gangdong': '11740', 'seoul-gangseo': '11500', 'seoul-mapo': '11440',
      'gyeonggi-seongnam-bundang': '41135', 'gyeonggi-suwon-yeongtong': '41117',
      'gyeonggi-bucheon': '41190', 'gyeonggi-goyang-deogyang': '41281'
    };
    var resolved = RECORDS[initialSlug] ? initialSlug : legacyMap[initialSlug];
    if (resolved && RECORDS[resolved]) {
      selectGu(resolved, false);
    }
  } else {
    // 디폴트: 서울 송파구 (URL 파라미터 없을 때)
    var DEFAULT_SLUG = 'seoul/songpa';
    if (RECORDS[DEFAULT_SLUG]) selectGu(DEFAULT_SLUG, false);
  }
})();
(function() {
  var input = document.getElementById('sgg-search');
  var clearBtn = document.getElementById('sgg-clear');
  var regionRow = document.getElementById('region-row');
  var chipsWrap = document.getElementById('sido-chips');
  var grid = document.getElementById('sgg-grid');
  var meta = document.getElementById('result-meta');
  var empty = document.getElementById('empty-state');
  var allCards = Array.prototype.slice.call(grid.querySelectorAll('.sgg-card'));
  var totalCount = allCards.length;
  var activeSido = '';
  var activeRegion = '';

  // 권역 → 시도 매핑
  var REGION_MAP = {
    capital: ['서울특별시', '인천광역시', '경기도'],
    chungcheong: ['대전광역시', '세종특별자치시', '충청북도', '충청남도'],
    honam: ['광주광역시', '전라남도', '전북특별자치도'],
    yeongnam: ['부산광역시', '대구광역시', '울산광역시', '경상북도', '경상남도'],
    gangwon_jeju: ['강원특별자치도', '제주특별자치도']
  };

  function applyFilter() {
    var q = (input.value || '').trim().toLowerCase();
    var visible = 0;
    var regionSidos = activeRegion ? REGION_MAP[activeRegion] : null;
    for (var i = 0; i < allCards.length; i++) {
      var card = allCards[i];
      var sido = card.dataset.sido;
      var name = card.dataset.name.toLowerCase();
      var sidoShort = card.querySelector('.sgg-sido').textContent.toLowerCase();
      var matchRegion = !regionSidos || regionSidos.indexOf(sido) !== -1;
      var matchSido = !activeSido || sido === activeSido;
      var matchQ = !q || name.indexOf(q) !== -1 || sido.toLowerCase().indexOf(q) !== -1 || sidoShort.indexOf(q) !== -1;
      if (matchRegion && matchSido && matchQ) {
        card.style.display = '';
        visible++;
      } else {
        card.style.display = 'none';
      }
    }
    if (visible === 0) {
      empty.style.display = 'block';
      meta.style.display = 'none';
    } else {
      empty.style.display = 'none';
      meta.style.display = 'block';
      meta.textContent = visible === totalCount ? '전국 ' + totalCount + '개 시군구' : visible + '개 시군구 표시 중';
    }
    clearBtn.classList.toggle('show', q.length > 0);
  }

  function updateSidoChips() {
    var sidoChips = chipsWrap.querySelectorAll('.sido-chip');
    for (var i = 0; i < sidoChips.length; i++) {
      var chip = sidoChips[i];
      var chipRegion = chip.dataset.region;
      if (!chip.dataset.sido) {
        chip.classList.remove('hidden');
        var countEl = chip.querySelector('.count');
        if (activeRegion) {
          var total = 0;
          var sidos = REGION_MAP[activeRegion];
          for (var j = 0; j < sidos.length; j++) {
            var match = chipsWrap.querySelector('[data-sido="' + sidos[j] + '"]');
            if (match) {
              var c = match.querySelector('.count');
              if (c) total += parseInt(c.textContent, 10) || 0;
            }
          }
          if (countEl) countEl.textContent = total;
        } else {
          if (countEl) countEl.textContent = totalCount;
        }
        continue;
      }
      if (!activeRegion || chipRegion === activeRegion) {
        chip.classList.remove('hidden');
      } else {
        chip.classList.add('hidden');
        if (chip.classList.contains('active')) {
          chip.classList.remove('active');
          activeSido = '';
          var allChip = chipsWrap.querySelector('.sido-chip[data-sido=""]');
          if (allChip) allChip.classList.add('active');
        }
      }
    }
  }

  input.addEventListener('input', applyFilter);
  clearBtn.addEventListener('click', function() {
    input.value = '';
    applyFilter();
    input.focus();
  });

  if (regionRow) {
    regionRow.addEventListener('click', function(e) {
      var chip = e.target.closest('.region-chip');
      if (!chip) return;
      var chips = regionRow.querySelectorAll('.region-chip');
      for (var i = 0; i < chips.length; i++) chips[i].classList.remove('active');
      chip.classList.add('active');
      activeRegion = chip.dataset.region || '';
      activeSido = '';
      var sidoChips = chipsWrap.querySelectorAll('.sido-chip');
      for (var j = 0; j < sidoChips.length; j++) sidoChips[j].classList.remove('active');
      var allSidoChip = chipsWrap.querySelector('.sido-chip[data-sido=""]');
      if (allSidoChip) allSidoChip.classList.add('active');
      updateSidoChips();
      applyFilter();
    });
  }

  chipsWrap.addEventListener('click', function(e) {
    var chip = e.target.closest('.sido-chip');
    if (!chip || chip.classList.contains('hidden')) return;
    var chips = chipsWrap.querySelectorAll('.sido-chip');
    for (var i = 0; i < chips.length; i++) chips[i].classList.remove('active');
    chip.classList.add('active');
    activeSido = chip.dataset.sido;
    applyFilter();
    var rect = chip.getBoundingClientRect();
    var wrapRect = chipsWrap.getBoundingClientRect();
    if (rect.right > wrapRect.right || rect.left < wrapRect.left) {
      chip.scrollIntoView({behavior: 'smooth', inline: 'center', block: 'nearest'});
    }
  });

  // ============ 비교 모드 ============
  var COMPARE = window.__COMPARE;
  var toggleBtn = document.getElementById('toggle-compare');
  var compareBar = document.getElementById('compare-bar');
  var slotEls = compareBar.querySelectorAll('.compare-slot');
  var clearBtnC = document.getElementById('compare-clear');
  var showBtn = document.getElementById('compare-show');
  var panel = document.getElementById('compare-panel');
  var panelBody = document.getElementById('compare-panel-body');
  var panelClose = document.getElementById('compare-panel-close');

  function getRecord(slug) { return RECORDS[slug]; }

  window.toggleCompareSlot = function(slug) {
    var idx = COMPARE.slots.indexOf(slug);
    if (idx !== -1) {
      COMPARE.slots.splice(idx, 1);
    } else if (COMPARE.slots.length < 3) {
      COMPARE.slots.push(slug);
      if (!COMPARE.enabled) {
        COMPARE.enabled = true;
        compareBar.classList.add('active');
        toggleBtn.classList.add('active');
        toggleBtn.setAttribute('aria-pressed', 'true');
      }
    } else {
      // 슬롯 가득
      return;
    }
    renderSlots();
    syncCardCompareMarks();
    // 카드 내 추가 버튼 라벨 갱신
    var addBtn = document.getElementById('card-add-compare-btn');
    if (addBtn && addBtn.dataset.slug === slug) {
      var inCompare = COMPARE.slots.indexOf(slug) !== -1;
      addBtn.textContent = inCompare ? '✓ 비교 슬롯에 추가됨' : '⊕ 비교에 추가';
      addBtn.classList.toggle('added', inCompare);
    }
  };

  function renderSlots() {
    for (var i = 0; i < 3; i++) {
      var el = slotEls[i];
      var slug = COMPARE.slots[i];
      if (slug && RECORDS[slug]) {
        var rec = RECORDS[slug];
        el.classList.add('filled');
        el.innerHTML = '<div class="compare-slot-name">' + escapeHTMLLocal(rec.name) + '</div>'
          + '<div class="compare-slot-sido">' + escapeHTMLLocal(rec.sido_name) + '</div>'
          + '<button class="compare-slot-remove" data-slot="' + i + '" aria-label="제거">✕</button>';
      } else {
        el.classList.remove('filled');
        el.innerHTML = '<div class="compare-slot-empty">슬롯 ' + (i+1) + ' 비어있음</div>';
      }
    }
    showBtn.disabled = COMPARE.slots.length < 2;
  }

  function syncCardCompareMarks() {
    for (var i = 0; i < allCards.length; i++) {
      var slug = allCards[i].dataset.slugkey;
      allCards[i].classList.toggle('in-compare', COMPARE.slots.indexOf(slug) !== -1);
    }
  }

  function escapeHTMLLocal(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, function(c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }

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

  toggleBtn.addEventListener('click', function() {
    COMPARE.enabled = !COMPARE.enabled;
    compareBar.classList.toggle('active', COMPARE.enabled);
    toggleBtn.classList.toggle('active', COMPARE.enabled);
    toggleBtn.setAttribute('aria-pressed', COMPARE.enabled ? 'true' : 'false');
    toggleBtn.textContent = COMPARE.enabled ? '✕ 비교 모드 끄기' : '⊕ 비교 모드';
  });

  clearBtnC.addEventListener('click', function() {
    COMPARE.slots = [];
    renderSlots();
    syncCardCompareMarks();
    panel.style.display = 'none';
  });

  compareBar.addEventListener('click', function(e) {
    var btn = e.target.closest('.compare-slot-remove');
    if (!btn) return;
    var idx = parseInt(btn.dataset.slot, 10);
    if (!isNaN(idx)) {
      COMPARE.slots.splice(idx, 1);
      renderSlots();
      syncCardCompareMarks();
      var addBtn = document.getElementById('card-add-compare-btn');
      if (addBtn) {
        var inC = COMPARE.slots.indexOf(addBtn.dataset.slug) !== -1;
        addBtn.textContent = inC ? '✓ 비교 슬롯에 추가됨' : '⊕ 비교에 추가';
        addBtn.classList.toggle('added', inC);
      }
    }
  });

  showBtn.addEventListener('click', function() {
    if (COMPARE.slots.length < 2) return;
    renderComparePanel();
    panel.style.display = 'block';
    panel.scrollIntoView({behavior: 'smooth', block: 'start'});
  });

  panelClose.addEventListener('click', function() {
    panel.style.display = 'none';
  });

  function renderComparePanel() {
    var recs = COMPARE.slots.map(getRecord).filter(function(x) { return x; });
    var n = recs.length;
    var colsCls = 'cols-' + n;

    // 비교 행 정의
    var rows = [
      {label: '평당가 (만원)', get: function(r) { return (r.sections.real_estate_trade || {}).median_price_per_pyeong_man; }, fmt: 'num', dir: 'lowBest'},
      {label: '매매 중앙값 (억)', get: function(r) { return (r.sections.real_estate_trade || {}).median_deal_amount_man; }, fmt: 'eok', dir: 'lowBest'},
      {label: '월평균 거래', get: function(r) { return (r.sections.real_estate_trade || {}).monthly_count_avg; }, fmt: 'numRound', dir: 'highBest'},
      {label: '전세 중앙값 (억)', get: function(r) { return (r.sections.real_estate_rent || {}).median_jeonse_man; }, fmt: 'eok', dir: 'lowBest'},
      {label: '인구', get: function(r) { return (r.sections.population || {}).sgg_total; }, fmt: 'num', dir: 'none'},
      {label: '의료기관', get: function(r) { return (r.sections.medical || {}).sgg_count; }, fmt: 'num', dir: 'highBest', unit: '곳'},
      {label: '학교', get: function(r) { return (r.sections.education || {}).sgg_count; }, fmt: 'num', dir: 'highBest', unit: '개'}
    ];

    var html = '';
    // 헤더 (이름 카드들)
    html += '<div class="compare-grid ' + colsCls + '">';
    for (var i = 0; i < n; i++) {
      var rec = recs[i];
      html += '<div class="compare-col">'
        + '<div class="compare-col-name">' + escapeHTMLLocal(rec.name) + '</div>'
        + '<div class="compare-col-sido">' + escapeHTMLLocal(rec.sido_name) + '</div>'
        + '</div>';
    }
    html += '</div>';

    // 비교 행
    html += '<div>';
    rows.forEach(function(row) {
      var values = recs.map(function(r) { return row.get(r); });
      var nums = values.filter(function(v) { return v !== null && v !== undefined && v !== 0; });
      var bestVal = null, worstVal = null;
      if (nums.length > 1 && row.dir !== 'none') {
        if (row.dir === 'lowBest') { bestVal = Math.min.apply(null, nums); worstVal = Math.max.apply(null, nums); }
        else { bestVal = Math.max.apply(null, nums); worstVal = Math.min.apply(null, nums); }
      }
      html += '<div class="compare-row ' + colsCls + '">'
        + '<div class="compare-row-label">' + row.label + '</div>';
      values.forEach(function(v) {
        var disp = '—';
        var cls = 'compare-row-val';
        if (v === null || v === undefined || v === 0) { cls += ' dim'; }
        else {
          if (row.fmt === 'num') disp = fmtNum(v) + (row.unit ? ' ' + row.unit : '');
          else if (row.fmt === 'numRound') disp = Math.round(v) + (row.unit || '건');
          else if (row.fmt === 'eok') disp = fmtEok(v);
          else disp = String(v);
          if (bestVal !== null && v === bestVal && nums.length > 1) cls += ' best';
          else if (worstVal !== null && v === worstVal && nums.length > 1) cls += ' worst';
        }
        html += '<div class="' + cls + '">' + disp + '</div>';
      });
      html += '</div>';
    });
    html += '</div>';

    // 추세 요약 (12개월 데이터 있으면)
    var trendSummary = '';
    recs.forEach(function(r, idx) {
      var t = r.sections.real_estate_trade || {};
      if (t.monthly_breakdown && t.monthly_breakdown.length >= 2) {
        var prices = t.monthly_breakdown.map(function(m) { return m.median_price_per_pyeong_man; }).filter(function(x) { return x > 0; });
        if (prices.length >= 2) {
          var first = prices[0], last = prices[prices.length-1];
          var pct = Math.round((last - first) / first * 1000) / 10;
          trendSummary += '<div style="font-size:13px;margin:6px 0;color:#475569;">' + escapeHTMLLocal(r.name) + ' 평당가 추세: <b style="color:' + (pct > 1 ? '#ef4444' : (pct < -1 ? '#3182f6' : '#94a3b8')) + '">' + (pct > 0 ? '+' : '') + pct + '%</b></div>';
        }
      }
    });
    if (trendSummary) {
      html += '<div style="margin-top:24px;padding:16px;background:#f0f9ff;border-radius:4px;">'
        + '<div style="font-size:12px;font-weight:700;color:#3182f6;letter-spacing:0.1em;margin-bottom:8px;">추세 요약</div>'
        + trendSummary + '</div>';
    } else {
      html += '<div style="margin-top:24px;padding:12px;background:#f8fafc;border-radius:4px;font-size:12px;color:#64748b;text-align:center;">추세 데이터(12개월 누적)는 다음 데이터 갱신 후 표시됩니다.</div>';
    }

    panelBody.innerHTML = html;
  }

  // 초기 비교 슬롯 렌더
  renderSlots();
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
    # 시도 짧은 이름
    SIDO_SHORT = {
        "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
        "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
        "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
        "충청북도": "충북", "충청남도": "충남", "전라남도": "전남",
        "경상북도": "경북", "경상남도": "경남", "제주특별자치도": "제주",
        "강원특별자치도": "강원", "전북특별자치도": "전북",
    }
    
    # 시도 → 권역 매핑
    SIDO_REGION = {
        "서울특별시": "capital", "인천광역시": "capital", "경기도": "capital",
        "대전광역시": "chungcheong", "세종특별자치시": "chungcheong", "충청북도": "chungcheong", "충청남도": "chungcheong",
        "광주광역시": "honam", "전라남도": "honam", "전북특별자치도": "honam",
        "부산광역시": "yeongnam", "대구광역시": "yeongnam", "울산광역시": "yeongnam", "경상북도": "yeongnam", "경상남도": "yeongnam",
        "강원특별자치도": "gangwon_jeju", "제주특별자치도": "gangwon_jeju",
    }
    
    # 권역별 카운트 누적
    region_counts = {"capital": 0, "chungcheong": 0, "honam": 0, "yeongnam": 0, "gangwon_jeju": 0}
    
    # 시도 칩 + 평면 시군구 카드 빌드
    chip_count_html = ""
    cards_html = []
    total_count = 0
    
    for sido in sido_list:
        sido_records = [r for r in records if r["sido_code"] == sido["code"]]
        if not sido_records: continue
        sido_name = sido["name"]
        sido_short = SIDO_SHORT.get(sido_name, sido_name)
        region = SIDO_REGION.get(sido_name, "")
        if region:
            region_counts[region] += len(sido_records)
        chip_count_html += f'<button class="sido-chip" data-sido="{sido_name}" data-region="{region}">{sido_short}<span class="count">{len(sido_records)}</span></button>\n  '
        for rec in sido_records:
            cards_html.append(
                f'  <a class="sgg-card" data-slugkey="{rec["slug"]}" data-sido="{sido_name}" data-name="{rec["name"]}">'
                f'<div class="sgg-name">{rec["name"]}</div>'
                f'<div class="sgg-sido">{sido_short}</div></a>'
            )
            total_count += 1
    
    sido_sections = f'''<div class="filter-bar">
  <div class="filter-input-wrap">
    <input type="search" id="sgg-search" class="filter-input" placeholder="동네 이름 검색 (예: 강남, 마포, 분당)" autocomplete="off">
    <button class="filter-input-clear" id="sgg-clear" aria-label="검색어 지우기">×</button>
  </div>
  <div class="region-row" id="region-row">
    <button class="region-chip active" data-region="">전체<span class="count">{total_count}</span></button>
    <button class="region-chip" data-region="capital">수도권<span class="count">{region_counts["capital"]}</span></button>
    <button class="region-chip" data-region="chungcheong">충청권<span class="count">{region_counts["chungcheong"]}</span></button>
    <button class="region-chip" data-region="honam">호남권<span class="count">{region_counts["honam"]}</span></button>
    <button class="region-chip" data-region="yeongnam">영남권<span class="count">{region_counts["yeongnam"]}</span></button>
    <button class="region-chip" data-region="gangwon_jeju">강원·제주<span class="count">{region_counts["gangwon_jeju"]}</span></button>
  </div>
  <div class="sido-chips" id="sido-chips">
    <button class="sido-chip active" data-sido="" data-region="">전체<span class="count">{total_count}</span></button>
    {chip_count_html.rstrip()}
  </div>
</div>

<div class="result-meta" id="result-meta">전국 {total_count}개 시군구</div>

<div class="sgg-grid" id="sgg-grid">
{chr(10).join(cards_html)}
</div>
<div class="empty-state" id="empty-state" style="display:none;"><b>일치하는 동네가 없습니다.</b><br>다른 검색어를 시도해 주세요.</div>'''

    try:
        dt = datetime.fromisoformat(data["fetched_at"].replace("Z", "+00:00"))
        updated = dt.strftime("%Y년 %m월 %d일")
    except Exception:
        updated = "—"

    data_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    html = (PAGE
            .replace("__SIDO_SECTIONS__", sido_sections)
            .replace("__UPDATED__", updated)
            .replace("__TOTAL_COUNT__", str(len(records)))
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
