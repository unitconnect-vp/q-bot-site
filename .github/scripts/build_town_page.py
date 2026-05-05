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
.hero { padding-top: 48px; margin-bottom: 32px; }
.hero-eyebrow { font-size: 13px; color: #64748b; margin-bottom: 8px; letter-spacing: 0.02em; }
.hero h1 { font-size: 48px; font-weight: 800; line-height: 1.1; letter-spacing: -0.03em; color: #0f172a; margin-bottom: 12px; }
.hero-tagline { font-size: 17px; color: #475569; margin-bottom: 24px; max-width: 540px; }
.hero-meta { font-size: 12px; color: #94a3b8; padding-top: 12px; border-top: 1px solid #e5e7eb; }
.hero-meta b { color: #3182f6; font-weight: 600; }
.filter-bar { position: sticky; top: 0; background: #ffffff; padding: 12px 0 8px; z-index: 10; margin-bottom: 16px; }
.filter-input-wrap { position: relative; margin-bottom: 10px; }
.filter-input { width: 100%; padding: 12px 40px 12px 16px; font-size: 15px; border: 1.5px solid #e5e7eb; border-radius: 4px; font-family: inherit; background: #fff; outline: none; transition: border-color 0.15s; }
.filter-input:focus { border-color: #0f172a; }
.filter-input-clear { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); width: 28px; height: 28px; border: none; background: #f3f4f6; color: #6b7280; border-radius: 50%; cursor: pointer; font-size: 16px; font-weight: 700; display: none; align-items: center; justify-content: center; padding: 0; line-height: 1; }
.filter-input-clear:hover { background: #e5e7eb; color: #0f172a; }
.filter-input-clear.show { display: flex; }
/* === 검색 autocomplete 드롭다운 (v3.7.5, 2026-05-05) === */
.search-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  max-height: 420px;
  overflow-y: auto;
  z-index: 20;
}
.search-dropdown[hidden] { display: none; }
.search-section-label {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 12px 16px 6px;
}
.search-item {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  border: 0;
  background: #fff;
  width: 100%;
  text-align: left;
  font-family: inherit;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.1s;
}
.search-item:last-child { border-bottom: 0; }
.search-item:hover, .search-item.active { background: #f8fafc; }
.search-item-name { font-size: 15px; font-weight: 600; color: #0f172a; }
.search-item-sido { font-size: 12px; color: #94a3b8; flex-shrink: 0; }
.search-empty { padding: 28px 16px; text-align: center; color: #94a3b8; font-size: 13px; }
.search-empty b { color: #475569; }
.sgg-name { font-size: 17px; font-weight: 700; color: #0f172a; line-height: 1.25; letter-spacing: -0.01em; }
.sgg-sido { font-size: 13px; color: #94a3b8; font-weight: 500; margin-top: 4px; }
@media (max-width: 640px) {
  .sgg-name { font-size: 16px; }
  .sgg-sido { font-size: 12px; }
  .filter-bar { padding: 10px 0 6px; }
  .hero { padding-top: 32px; }
  .hero h1 { font-size: 36px; }
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
.source { font-size: 11px; color: #94a3b8; margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9; }
.compare-add { display: inline-block; padding: 8px 14px; background: #fff; border: 1.5px solid #3182f6; color: #3182f6; border-radius: 4px; font-size: 13px; font-weight: 700; cursor: pointer; margin-left: 8px; transition: all 0.12s; font-family: inherit; }
.compare-add:hover { background: #3182f6; color: #fff; }
.compare-add.added { background: #3182f6; color: #fff; border-color: #3182f6; }
.compare-add.added::before { content: '✓ '; }
.compare-tray { position: sticky; top: 0; background: #fff; border-bottom: 4px solid #3182f6; padding: 14px 0; margin-bottom: 24px; z-index: 20; display: none; }
.compare-tray.show { display: block; }
.compare-tray-inner { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.compare-tray-label { font-size: 13px; font-weight: 700; color: #0f172a; }
.compare-tray-chips { display: flex; gap: 6px; flex: 1; flex-wrap: wrap; }
.compare-chip { display: inline-flex; align-items: center; gap: 6px; padding: 6px 6px 6px 12px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 999px; font-size: 13px; font-weight: 600; color: #1e40af; }
.compare-chip-x { width: 22px; height: 22px; border: none; background: #1e40af; color: #fff; border-radius: 50%; cursor: pointer; font-size: 14px; line-height: 1; padding: 0; display: flex; align-items: center; justify-content: center; font-weight: 700; }
.compare-chip-x:hover { background: #0f172a; }
.compare-tray-actions { display: flex; gap: 8px; }
.compare-btn { padding: 8px 16px; border-radius: 4px; font-size: 13px; font-weight: 700; cursor: pointer; border: none; transition: all 0.12s; font-family: inherit; }
.compare-btn.primary { background: #0f172a; color: #fff; }
.compare-btn.primary:hover { background: #1e293b; }
.compare-btn.primary:disabled { background: #cbd5e1; cursor: not-allowed; }
.compare-btn.ghost { background: #fff; color: #64748b; border: 1px solid #e5e7eb; }
.compare-btn.ghost:hover { color: #0f172a; border-color: #0f172a; }
.compare-view { display: none; }
.compare-view.show { display: block; }
.compare-view-head { padding: 24px 0 16px; border-bottom: 4px solid #0f172a; margin-bottom: 24px; }
.compare-view-head h2 { font-size: 32px; font-weight: 800; letter-spacing: -0.02em; color: #0f172a; margin-bottom: 6px; }
.compare-view-head p { font-size: 14px; color: #64748b; }
.compare-table-wrap { overflow-x: auto; margin-bottom: 32px; -webkit-overflow-scrolling: touch; }
.compare-table { width: 100%; border-collapse: collapse; min-width: 560px; }
.compare-table th, .compare-table td { padding: 16px 14px; text-align: left; border-bottom: 1px solid #e5e7eb; font-size: 14px; }
.compare-table th { background: #f8fafc; font-size: 13px; font-weight: 600; color: #64748b; }
.compare-table th.sgg-head { background: #0f172a; color: #fff; font-size: 15px; font-weight: 800; text-align: center; padding: 14px 12px; letter-spacing: -0.01em; }
.compare-table th.sgg-head .sub { display: block; font-size: 11px; color: #cbd5e1; font-weight: 500; margin-top: 2px; }
.compare-table td.metric-label { font-size: 13px; color: #64748b; font-weight: 600; background: #f8fafc; width: 28%; }
.compare-table td.value { font-variant-numeric: tabular-nums; font-weight: 700; color: #0f172a; text-align: right; font-size: 15px; }
.compare-table td.value.best { color: #3182f6; }
.compare-table td.value.worst { color: #94a3b8; }
.compare-empty { text-align: center; padding: 60px 20px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 4px; color: #64748b; font-size: 14px; }
.trend-block { margin: 24px 0 8px; }
.trend-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; gap: 12px; flex-wrap: wrap; }
.trend-title { font-size: 14px; font-weight: 700; color: #0f172a; }
.trend-change { font-size: 15px; font-weight: 800; font-variant-numeric: tabular-nums; }
.trend-change.up { color: #dc2626; }
.trend-change.down { color: #2563eb; }
.trend-change.flat { color: #64748b; }
.trend-svg { width: 100%; height: 110px; display: block; }
.trend-axis { display: flex; justify-content: space-between; font-size: 11px; color: #94a3b8; padding: 4px 0 0; }
.trend-meta { font-size: 12px; color: #64748b; padding-top: 6px; }
.trend-empty { color: #94a3b8; font-size: 13px; padding: 16px 0; line-height: 1.5; background: #f8fafc; border-radius: 4px; padding: 16px; text-align: center; margin: 16px 0; }
.compare-trend-cell { font-variant-numeric: tabular-nums; font-weight: 700; }
.compare-trend-cell.up { color: #dc2626; }
.compare-trend-cell.down { color: #2563eb; }
.compare-trend-cell.flat { color: #64748b; }
@media (max-width: 640px) {
  .compare-tray-actions { width: 100%; justify-content: stretch; }
  .compare-tray-actions .compare-btn { flex: 1; }
  .compare-view-head h2 { font-size: 24px; }
  .compare-table th.sgg-head { font-size: 13px; padding: 10px 8px; }
  .compare-table td.value { font-size: 13px; padding: 12px 8px; }
  .compare-table td.metric-label { font-size: 12px; padding: 12px 8px; }
}
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
      <a href="/play/">게임</a>
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

  <div class="compare-tray" id="compare-tray">
    <div class="compare-tray-inner">
      <span class="compare-tray-label">비교</span>
      <div class="compare-tray-chips" id="compare-tray-chips"></div>
      <div class="compare-tray-actions">
        <button class="compare-btn ghost" id="compare-clear">전체 해제</button>
        <button class="compare-btn primary" id="compare-show" disabled>비교 보기 →</button>
      </div>
    </div>
  </div>

  <div class="filter-bar">
  <div class="filter-input-wrap">
    <input type="search" id="sgg-search" class="filter-input" placeholder="동네 이름 검색 (예: 강남, 마포, 분당)" autocomplete="off">
    <button class="filter-input-clear" id="sgg-clear" aria-label="검색어 지우기">×</button>
  </div>
  <div class="search-dropdown" id="search-dropdown" hidden></div>
</div>


  <div class="card-area" id="card-area">
    <div class="card-empty">동네를 검색해 선택하면 카드가 여기에 나타납니다</div>
  </div>

  <div class="compare-view" id="compare-view">
    <div class="compare-view-head">
      <h2 id="compare-title">동네 비교</h2>
      <p>핵심 지표를 나란히 비교합니다. 파란색 = 가장 높은 값.</p>
    </div>
    <div class="compare-table-wrap" id="compare-table-wrap"></div>
    <button class="compare-btn ghost" id="compare-back" style="margin-bottom:48px;">← 동네 선택으로 돌아가기</button>
  </div>

</div>

<footer class="site-footer">
  <div class="footer-inner">
    <div class="footer-brand">
      <div class="footer-logo">Q<span>-</span>Lens</div>
      <p class="footer-tagline">보이는 것 너머를 묻습니다</p>
      <div class="footer-social">
        <a class="footer-social__link" href="https://x.com/heyqbot" target="_blank" rel="noopener" aria-label="X (Twitter)">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        </a>
      </div>
    </div>
    <div class="footer-col">
      <h4 class="footer-col__title">카테고리</h4>
      <ul class="footer-col__list">
        <li><a href="/categories/industry/">산업·전략</a></li>
        <li><a href="/categories/corporate/">기업·경영</a></li>
        <li><a href="/categories/stocks/">주식·투자</a></li>
        <li><a href="/categories/bonds/">채권·금리</a></li>
        <li><a href="/categories/economy/">경제·정책</a></li>
        <li><a href="/categories/realestate/">부동산</a></li>
        <li><a href="/categories/society/">사회·이슈</a></li>
        <li><a href="/categories/data/">데이터·리서치</a></li>
        <li><a href="/categories/" class="footer-col__more">전체 보기 →</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <h4 class="footer-col__title">정보</h4>
      <ul class="footer-col__list">
        <li><a href="/about/">소개</a></li>
        <li><a href="/contact/">문의</a></li>
        <li><a href="/town/">동네 카드</a></li>
        <li><a href="/tools/">계산기</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">
    <p class="footer-copy">© 2026 Q-Lens. All rights reserved.</p>
    <p class="footer-legal">
      <a href="/privacy/">개인정보처리방침</a>
      <span>·</span>
      <a href="/terms/">이용약관</a>
      <span>·</span>
      <a href="https://github.com/unitconnect-vp/q-bot-site/blob/main/CHANGELOG.md" target="_blank" rel="noopener" class="footer-version">v5.1</a>
    </p>
  </div>
</footer>

<script async src="https://www.googletagmanager.com/gtag/js?id=G-04MMSE99PJ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-04MMSE99PJ');
</script>

<script id="town-data" type="application/json">__DATA_JSON__</script>

<script>
(function() {
  var raw = document.getElementById('town-data').textContent;
  var DATA = JSON.parse(raw);
  var RECORDS = {};
  DATA.records.forEach(function(r) {
    RECORDS[r.slug] = r;
  });
  window.__TOWN_RECORDS__ = RECORDS;

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

  function renderTrendChart(monthlyBreakdown, field, label, unit, isCount) {
    var mb = monthlyBreakdown || [];
    if (!mb.length) {
      return '<div class="trend-empty"><b>12개월 추세 데이터 수집 중</b><br>다음 데이터 갱신(매주 월) 이후 추세 차트가 표시됩니다.</div>';
    }
    var data = mb.filter(function(d) { return d[field] !== null && d[field] !== undefined; });
    if (data.length < 3) {
      return '<div class="trend-empty">최근 ' + mb.length + '개월 거래 데이터 — 추세 표시는 3개월 이상부터.</div>';
    }
    var w = 600, h = 110, pad = 12;
    var values = data.map(function(d) { return d[field]; });
    var minV = Math.min.apply(null, values);
    var maxV = Math.max.apply(null, values);
    var range = maxV - minV || 1;
    // count는 0부터 시작이 자연스러움
    if (isCount) { minV = 0; range = maxV || 1; }
    var step = data.length > 1 ? (w - 2*pad) / (data.length - 1) : 0;
    var points = data.map(function(d, i) {
      var x = pad + i * step;
      var y = h - pad - ((d[field] - minV) / range) * (h - 2*pad);
      return [x, y, d];
    });
    var svgInner;
    if (isCount) {
      // 막대 차트
      var barW = Math.max(8, step * 0.6);
      svgInner = points.map(function(p) {
        var bx = p[0] - barW/2;
        var by = p[1];
        var bh = (h - pad) - p[1];
        return '<rect x="' + bx + '" y="' + by + '" width="' + barW + '" height="' + Math.max(0, bh) + '" fill="#3182f6" rx="1"/>';
      }).join('');
    } else {
      // 라인 차트 (영역 + 라인 + 점)
      var path = 'M ' + points.map(function(p) { return p[0] + ',' + p[1]; }).join(' L ');
      var area = path + ' L ' + points[points.length-1][0] + ',' + (h-pad) + ' L ' + points[0][0] + ',' + (h-pad) + ' Z';
      svgInner = '<path d="' + area + '" fill="#3182f6" fill-opacity="0.08"/>' +
                 '<path d="' + path + '" stroke="#3182f6" stroke-width="2" fill="none"/>' +
                 points.map(function(p) { return '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="3" fill="#3182f6"/>'; }).join('');
    }

    function fmtYm(ym) { return ym.substring(2,4) + '.' + ym.substring(4) + '월'; }
    var first = data[0][field];
    var last = data[data.length-1][field];
    var changeHtml = '';
    if (first > 0 && !isCount) {
      var pct = ((last - first) / first) * 100;
      var dir = Math.abs(pct) < 0.5 ? 'flat' : (pct > 0 ? 'up' : 'down');
      var sign = pct >= 0 ? '+' : '';
      changeHtml = '<span class="trend-change ' + dir + '">' + sign + pct.toFixed(1) + '%</span>';
    } else if (isCount) {
      var totalCount = values.reduce(function(a,b){return a+b;}, 0);
      changeHtml = '<span class="trend-meta">총 ' + totalCount + ' 건</span>';
    }

    var metaLine;
    if (isCount) {
      metaLine = '월 평균 ' + Math.round(values.reduce(function(a,b){return a+b;}, 0) / values.length) + ' ' + unit;
    } else {
      metaLine = '시작 ' + fmtNum(first) + unit + ' → 최근 ' + fmtNum(last) + unit;
    }

    return '<div class="trend-block">' +
      '<div class="trend-head"><span class="trend-title">' + label + ' (' + data.length + '개월)</span>' + changeHtml + '</div>' +
      '<svg class="trend-svg" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none">' + svgInner + '</svg>' +
      '<div class="trend-axis"><span>' + fmtYm(data[0].ym) + '</span><span>' + fmtYm(data[data.length-1].ym) + '</span></div>' +
      '<div class="trend-meta">' + metaLine + '</div>' +
      '</div>';
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
    // 의료기관 위계 순서: 최상위 시설 → 작은 규모
    var ORDER = ['상급종합','종합병원','병원','치과병원','한방병원','요양병원','정신병원','의원','치과의원','한의원','조산원','보건의료원','보건소','보건지소','보건진료소'];
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
    var main = ['초등학교', '중학교', '고등학교', '특수학교', '대학교', '전문대학'];
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

  function renderPopulationTrend(rec) {
    var p = rec.sections.population || {};
    var yearly = p.yearly || [];
    if (!yearly.length) {
      return '<div class="trend-empty"><b>5년 인구 추이 데이터 수집 중</b><br>다음 데이터 갱신 이후 추이 차트가 표시됩니다.</div>';
    }
    if (yearly.length < 2) {
      return '<div class="trend-empty">' + yearly.length + '개 연도 데이터 — 추이 표시는 2년 이상부터.</div>';
    }
    var w = 600, h = 110, pad = 12;
    var values = yearly.map(function(d) { return d.total; });
    var minV = Math.min.apply(null, values);
    var maxV = Math.max.apply(null, values);
    var range = maxV - minV || 1;
    var step = yearly.length > 1 ? (w - 2*pad) / (yearly.length - 1) : 0;
    var points = yearly.map(function(d, i) {
      var x = pad + i * step;
      var y = h - pad - ((d.total - minV) / range) * (h - 2*pad);
      return [x, y, d];
    });
    var path = 'M ' + points.map(function(p) { return p[0] + ',' + p[1]; }).join(' L ');
    var area = path + ' L ' + points[points.length-1][0] + ',' + (h-pad) + ' L ' + points[0][0] + ',' + (h-pad) + ' Z';
    var svgInner = '<path d="' + area + '" fill="#3182f6" fill-opacity="0.08"/>' +
                   '<path d="' + path + '" stroke="#3182f6" stroke-width="2" fill="none"/>' +
                   points.map(function(pt) { return '<circle cx="' + pt[0] + '" cy="' + pt[1] + '" r="3" fill="#3182f6"/>'; }).join('');

    var first = yearly[0].total;
    var last = yearly[yearly.length-1].total;
    var pct = first > 0 ? ((last - first) / first) * 100 : 0;
    var dir = Math.abs(pct) < 0.5 ? 'flat' : (pct > 0 ? 'up' : 'down');
    // 인구는 증가가 좋은 신호이므로 색 매핑 일반 라인과 동일하게: up=빨강(상승, 부동산 상승과 동일 톤), down=파랑
    // 단 의미는 다름 — 인구 감소는 보통 우려 신호라서 회색 처리하는 게 더 정확함.
    // 결정: 인구는 단순 % 변화만 표기 (색상은 fixed 회색이 안전)
    var sign = pct >= 0 ? '+' : '';
    var changeHtml = '<span class="trend-change flat">' + sign + pct.toFixed(1) + '%</span>';

    return '<div class="trend-block">' +
      '<div class="trend-head"><span class="trend-title">인구 ' + yearly.length + '년 추이</span>' + changeHtml + '</div>' +
      '<svg class="trend-svg" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none">' + svgInner + '</svg>' +
      '<div class="trend-axis"><span>' + yearly[0].year + '</span><span>' + yearly[yearly.length-1].year + '</span></div>' +
      '<div class="trend-meta">' + yearly[0].year + '년 ' + fmtNum(first) + '명 → ' + yearly[yearly.length-1].year + '년 ' + fmtNum(last) + '명</div>' +
      '</div>';
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

    var compareBtn = '<button class="compare-add" data-slugkey="' + escapeHTML(rec.slug) + '" data-name="' + escapeHTML(rec.name) + '" data-sido="' + escapeHTML(rec.sido_name) + '">+ 비교에 추가</button>';

    return ''
      + '<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">'
      + '<div><div class="card-region">' + escapeHTML(rec.name_full) + '</div>'
      + '<div class="card-name">' + escapeHTML(rec.name) + '</div></div>'
      + compareBtn
      + '</div>'
      + '<div class="ql-stat-row">'
      + '<div class="ql-stat-cell">' + stat1 + '</div>'
      + '<div class="ql-stat-cell">' + stat2 + '</div>'
      + '<div class="ql-stat-cell">' + stat3 + '</div>'
      + '</div>'
      + '<section class="section">'
      + '<div class="section-num">01 — 부동산</div><h2>집값과 거래의 흐름</h2>'
      + '<p class="section-sub">최근 12개월 아파트 매매·전월세 실거래.</p>'
      + renderRealEstate(rec)
      + renderTrendChart((rec.sections.real_estate_trade || {}).monthly_breakdown, 'median_price_per_pyeong_man', '평당가 추이', '만원', false)
      + renderTrendChart((rec.sections.real_estate_trade || {}).monthly_breakdown, 'count', '월별 거래 건수', '건', true)
      + '<div class="source">출처: 국토교통부 실거래가 공개시스템</div></section>'
      + '<section class="section">'
      + '<div class="section-num">02 — 의료</div><h2>병원·의원 분포</h2>'
      + '<p class="section-sub">시군구 내 의료기관 종별.</p>'
      + renderMedical(rec)
      + '<div class="source">출처: 건강보험심사평가원</div></section>'
      + '<section class="section">'
      + '<div class="section-num">03 — 교육</div><h2>학교 분포</h2>'
      + '<p class="section-sub">유·초·중·고·특수학교 기준. 대학·전문대 미포함.</p>'
      + renderEducation(rec)
      + '<div class="source">출처: 교육부 NEIS</div></section>'
      + '<section class="section">'
      + '<div class="section-num">04 — 인구</div><h2>누가 살고 있나</h2>'
      + '<p class="section-sub">행정안전부 주민등록인구 — 동네의 골격.</p>'
      + renderPopulation(rec)
      + renderPopulationTrend(rec)
      + '<div class="source">출처: 통계청 KOSIS · 행정안전부 주민등록 (DT_1B040A3)</div></section>';
  }

  function selectGu(slugKey, pushState) {
    var rec = RECORDS[slugKey];
    var area = document.getElementById('card-area');
    if (!rec) {
      area.innerHTML = '<div class="card-empty">시군구 데이터를 찾을 수 없습니다</div>';
      return;
    }
    area.innerHTML = buildCard(rec);
    // 비교 모드에 이미 추가된 경우 버튼 상태 갱신
    if (typeof window.__updateCompareAdd__ === 'function') window.__updateCompareAdd__();
    if (pushState && history.pushState) {
      history.pushState({slug: slugKey}, '', '?gu=' + slugKey);
    }
    document.title = rec.name + ' — Q렌즈 동네 카드';
    area.scrollIntoView({behavior: 'smooth', block: 'start'});
  }

  

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
  // === 시군구 검색 autocomplete (v3.7.5, 2026-05-05) ===
  // 폐기된 sgg-grid + region-row + sido-chips + result-meta 대체.
  // input focus → 인기 동네 8개 / 입력 → 실시간 매칭 / 클릭 → selectGu 호출.
  var input = document.getElementById('sgg-search');
  var clearBtn = document.getElementById('sgg-clear');
  var dropdown = document.getElementById('search-dropdown');
  if (!input || !dropdown) return;

  var SEARCH_INDEX = __SEARCH_INDEX__;
  var POPULAR = ["seoul/gangnam", "seoul/seocho", "seoul/songpa", "seoul/mapo", "seoul/yongsan", "seoul/seongdong", "gyeonggi/bundang", "busan/haeundae"];
  var MAX_RESULTS = 12;
  var activeIdx = -1;
  var currentItems = []; // 현재 드롭다운에 노출된 항목들의 slugkey

  function escHtml(s) {
    return String(s).replace(/[&<>"']/g, function(c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }

  function renderItems(items, label) {
    if (!items.length) {
      dropdown.innerHTML = '<div class="search-empty"><b>일치하는 동네가 없습니다.</b><br>다른 검색어를 시도해 주세요.</div>';
      currentItems = [];
      activeIdx = -1;
      dropdown.hidden = false;
      return;
    }
    var labelHtml = label ? '<div class="search-section-label">' + escHtml(label) + '</div>' : '';
    var html = labelHtml + items.map(function(it) {
      return '<button type="button" class="search-item" data-slugkey="' + escHtml(it.k) + '">' +
             '<span class="search-item-name">' + escHtml(it.n) + '</span>' +
             '<span class="search-item-sido">' + escHtml(it.ss) + '</span>' +
             '</button>';
    }).join('');
    dropdown.innerHTML = html;
    currentItems = items;
    activeIdx = -1;
    dropdown.hidden = false;
  }

  function showPopular() {
    var popular = POPULAR.map(function(k) {
      for (var i = 0; i < SEARCH_INDEX.length; i++) {
        if (SEARCH_INDEX[i].k === k) return SEARCH_INDEX[i];
      }
      return null;
    }).filter(Boolean);
    renderItems(popular, '인기 동네');
  }

  function search(q) {
    q = q.trim().toLowerCase();
    if (!q) { showPopular(); return; }
    // 매칭: name(소문자) / sido(소문자) / sidoShort(소문자) 부분일치
    // 우선순위: name 시작 일치 > name 부분 일치 > sido/sidoShort 일치
    var startsWith = [], contains = [], sidoMatch = [];
    for (var i = 0; i < SEARCH_INDEX.length; i++) {
      var it = SEARCH_INDEX[i];
      var n = it.n.toLowerCase();
      var s = it.s.toLowerCase();
      var ss = it.ss.toLowerCase();
      if (n === q || n.indexOf(q) === 0) {
        startsWith.push(it);
      } else if (n.indexOf(q) !== -1) {
        contains.push(it);
      } else if (s.indexOf(q) !== -1 || ss.indexOf(q) !== -1) {
        sidoMatch.push(it);
      }
    }
    var results = startsWith.concat(contains, sidoMatch).slice(0, MAX_RESULTS);
    renderItems(results, null);
  }

  function closeDropdown() {
    dropdown.hidden = true;
    activeIdx = -1;
  }

  function moveActive(delta) {
    var els = dropdown.querySelectorAll('.search-item');
    if (!els.length) return;
    if (activeIdx >= 0) els[activeIdx].classList.remove('active');
    activeIdx = (activeIdx + delta + els.length) % els.length;
    els[activeIdx].classList.add('active');
    els[activeIdx].scrollIntoView({block: 'nearest'});
  }

  function selectByIdx(idx) {
    if (idx < 0 || idx >= currentItems.length) return;
    var it = currentItems[idx];
    selectItem(it);
  }

  function selectItem(it) {
    input.value = it.n;
    closeDropdown();
    // selectGu는 첫 번째 IIFE에서 정의돼 있고 외부에서 직접 호출 불가하므로,
    // hashchange/popstate 트리거 대신 ?gu= 쿼리 변경 후 popstate 시뮬레이션
    var newUrl = location.pathname + '?gu=' + encodeURIComponent(it.k);
    history.pushState({slug: it.k}, '', newUrl);
    window.dispatchEvent(new PopStateEvent('popstate', {state: {slug: it.k}}));
    // 카드 영역으로 스크롤
    var area = document.getElementById('card-area');
    if (area) area.scrollIntoView({behavior: 'smooth', block: 'start'});
  }

  // 이벤트 바인딩
  input.addEventListener('focus', function() {
    var q = input.value.trim();
    if (q) search(q); else showPopular();
  });
  input.addEventListener('input', function() {
    search(input.value);
  });
  input.addEventListener('keydown', function(e) {
    if (dropdown.hidden) {
      if (e.key === 'ArrowDown') { showPopular(); e.preventDefault(); }
      return;
    }
    if (e.key === 'ArrowDown') { moveActive(1); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { moveActive(-1); e.preventDefault(); }
    else if (e.key === 'Enter') {
      if (activeIdx >= 0) { selectByIdx(activeIdx); e.preventDefault(); }
      else if (currentItems.length === 1) { selectByIdx(0); e.preventDefault(); }
    } else if (e.key === 'Escape') {
      closeDropdown();
      input.blur();
    }
  });

  dropdown.addEventListener('mousedown', function(e) {
    // mousedown으로 처리 — blur 전에 발화되어 input.blur()로 인한 dropdown 닫힘 회피
    var item = e.target.closest('.search-item');
    if (!item) return;
    e.preventDefault();
    var slug = item.dataset.slugkey;
    for (var i = 0; i < currentItems.length; i++) {
      if (currentItems[i].k === slug) { selectItem(currentItems[i]); return; }
    }
  });

  document.addEventListener('mousedown', function(e) {
    if (dropdown.hidden) return;
    if (e.target.closest('.filter-input-wrap, .search-dropdown')) return;
    closeDropdown();
  });

  if (clearBtn) {
    clearBtn.addEventListener('click', function() {
      input.value = '';
      input.focus();
      showPopular();
    });
  }
})();

// ==================== 비교 모드 ====================
(function() {
  var TRAY = document.getElementById('compare-tray');
  var TRAY_CHIPS = document.getElementById('compare-tray-chips');
  var BTN_SHOW = document.getElementById('compare-show');
  var BTN_CLEAR = document.getElementById('compare-clear');
  var BTN_BACK = document.getElementById('compare-back');
  var VIEW = document.getElementById('compare-view');
  var TABLE_WRAP = document.getElementById('compare-table-wrap');
  var TITLE = document.getElementById('compare-title');
  var CARD_AREA = document.getElementById('card-area');
  var FILTER_BAR = document.querySelector('.filter-bar');

  var compareList = []; // [{slugkey, name, sido}]
  var MAX_COMPARE = 3;

  // RECORDS는 첫 번째 IIFE에서 closure 안에 있어서 접근 불가. window에 노출 필요.
  function getRecord(slugkey) {
    return (window.__TOWN_RECORDS__ || {})[slugkey];
  }

  function renderTray() {
    if (compareList.length === 0) {
      TRAY.classList.remove('show');
      BTN_SHOW.disabled = true;
      return;
    }
    TRAY.classList.add('show');
    BTN_SHOW.disabled = compareList.length < 2;
    TRAY_CHIPS.innerHTML = compareList.map(function(item) {
      return '<span class="compare-chip">' + escHtml(item.name) +
             '<button class="compare-chip-x" data-slugkey="' + escHtml(item.slugkey) + '" aria-label="제거">×</button></span>';
    }).join('');
    BTN_SHOW.textContent = '비교 보기 (' + compareList.length + ') →';
  }

  function escHtml(s) {
    return String(s).replace(/[&<>"']/g, function(c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
  }

  function fmtNum(n) {
    if (n === null || n === undefined || n === '') return '—';
    return Number(n).toLocaleString('ko-KR');
  }

  function fmtEok(man) {
    if (!man) return '—';
    var eok = man / 10000;
    return eok >= 10 ? Math.round(eok) + '억' : (Math.round(eok * 10) / 10) + '억';
  }

  function addToCompare(slugkey, name, sido) {
    if (compareList.find(function(x) { return x.slugkey === slugkey; })) return false;
    if (compareList.length >= MAX_COMPARE) {
      alert('비교는 최대 ' + MAX_COMPARE + '개까지 가능합니다.');
      return false;
    }
    compareList.push({slugkey: slugkey, name: name, sido: sido});
    renderTray();
    updateAddButtons();
    return true;
  }

  function removeFromCompare(slugkey) {
    compareList = compareList.filter(function(x) { return x.slugkey !== slugkey; });
    renderTray();
    updateAddButtons();
  }

  function clearCompare() {
    compareList = [];
    renderTray();
    updateAddButtons();
  }

  function updateAddButtons() {
    var btns = document.querySelectorAll('.compare-add');
    btns.forEach(function(b) {
      var slugkey = b.dataset.slugkey;
      var added = compareList.some(function(x) { return x.slugkey === slugkey; });
      if (added) {
        b.classList.add('added');
        b.textContent = ''; // ::before가 ✓ 표시함, 텍스트는 비움
        b.innerHTML = '추가됨';
      } else {
        b.classList.remove('added');
        b.innerHTML = '+ 비교에 추가';
      }
    });
  }
  window.__updateCompareAdd__ = updateAddButtons;

  // 비교 보기 화면
  function showCompareView() {
    if (compareList.length < 2) return;
    var records = compareList.map(function(item) { return getRecord(item.slugkey); }).filter(Boolean);
    if (records.length < 2) {
      alert('데이터를 불러올 수 없습니다.');
      return;
    }
    TITLE.textContent = records.map(function(r) { return r.name; }).join(' vs ');
    TABLE_WRAP.innerHTML = buildCompareTable(records);
    // 입력 영역 숨기기
    FILTER_BAR.style.display = 'none';
    CARD_AREA.style.display = 'none';
    var dropdown = document.getElementById('search-dropdown');
    if (dropdown) dropdown.hidden = true;
    // 인트로 텍스트도 가린다
    var hero = document.querySelector('.hero');
    if (hero) hero.style.display = 'none';
    VIEW.classList.add('show');
    window.scrollTo({top: 0, behavior: 'smooth'});
  }

  function hideCompareView() {
    FILTER_BAR.style.display = '';
    CARD_AREA.style.display = '';
    var hero = document.querySelector('.hero');
    if (hero) hero.style.display = '';
    VIEW.classList.remove('show');
  }

  function buildCompareTable(records) {
    // 핵심 지표 정의
    var metrics = [
      {label: '아파트 평당가 (중앙값)', get: function(r) {
        var v = (r.sections.real_estate_trade || {}).median_price_per_pyeong_man;
        return {raw: v, display: v ? fmtNum(v) + ' 만원' : '—'};
      }, dir: 'high'},
      {label: '매매 평균 거래액 (중앙값)', get: function(r) {
        var v = (r.sections.real_estate_trade || {}).median_deal_amount_man;
        return {raw: v, display: v ? fmtEok(v) : '—'};
      }, dir: 'high'},
      {label: '월평균 매매 건수', get: function(r) {
        var v = (r.sections.real_estate_trade || {}).monthly_count_avg;
        return {raw: v, display: v ? Math.round(v) + ' 건' : '—'};
      }, dir: 'high'},
      {label: '전세 중앙값', get: function(r) {
        var v = (r.sections.real_estate_rent || {}).median_jeonse_man;
        return {raw: v, display: v ? fmtEok(v) : '—'};
      }, dir: 'high'},
      {label: '매매-전세 비율', get: function(r) {
        var t = r.sections.real_estate_trade || {};
        var rt = r.sections.real_estate_rent || {};
        if (rt.median_jeonse_man && t.median_deal_amount_man) {
          var pct = Math.round(rt.median_jeonse_man / t.median_deal_amount_man * 1000) / 10;
          return {raw: pct, display: pct + ' %'};
        }
        return {raw: null, display: '—'};
      }, dir: 'high'},
      {label: '인구 (주민등록)', get: function(r) {
        var p = r.sections.population || {};
        var v = p.sgg_total || p.gangnam_total;
        return {raw: v, display: v ? fmtNum(v) + ' 명' : '—'};
      }, dir: 'high'},
      {label: '의료기관 합계', get: function(r) {
        var m = r.sections.medical || {};
        var v = m.sgg_count;
        if (!v && m.by_type) {
          v = Object.keys(m.by_type).reduce(function(a, k) { return a + m.by_type[k]; }, 0);
        }
        return {raw: v, display: v ? fmtNum(v) + ' 곳' : '—'};
      }, dir: 'high'},
      {label: '학교 합계', get: function(r) {
        var e = r.sections.education || {};
        var v = e.sgg_count;
        if (!v && e.by_type) {
          v = Object.keys(e.by_type).reduce(function(a, k) { return a + e.by_type[k]; }, 0);
        }
        return {raw: v, display: v ? fmtNum(v) + ' 개' : '—'};
      }, dir: 'high'},
      {label: '평당가 추이 (12개월)', get: function(r) {
        var mb = (r.sections.real_estate_trade || {}).monthly_breakdown || [];
        var data = mb.filter(function(d) { return d.median_price_per_pyeong_man; });
        if (data.length < 3) return {raw: null, display: '데이터 부족'};
        var first = data[0].median_price_per_pyeong_man;
        var last = data[data.length-1].median_price_per_pyeong_man;
        if (!first) return {raw: null, display: '—'};
        var pct = ((last - first) / first) * 100;
        var sign = pct >= 0 ? '+' : '';
        var cls = Math.abs(pct) < 0.5 ? 'flat' : (pct > 0 ? 'up' : 'down');
        return {raw: pct, display: '<span class="compare-trend-cell ' + cls + '">' + sign + pct.toFixed(1) + '%</span>', isHtml: true};
      }, dir: 'high'},
      {label: '월평균 거래량 (12개월)', get: function(r) {
        var mb = (r.sections.real_estate_trade || {}).monthly_breakdown || [];
        if (!mb.length) return {raw: null, display: '데이터 부족'};
        var counts = mb.map(function(d) { return d.count || 0; });
        var avg = counts.reduce(function(a,b){return a+b;}, 0) / counts.length;
        return {raw: avg, display: Math.round(avg) + ' 건'};
      }, dir: 'high'},
      {label: '인구 추이 (5년)', get: function(r) {
        var yearly = (r.sections.population || {}).yearly || [];
        if (yearly.length < 2) return {raw: null, display: '데이터 부족'};
        var first = yearly[0].total;
        var last = yearly[yearly.length-1].total;
        if (!first) return {raw: null, display: '—'};
        var pct = ((last - first) / first) * 100;
        var sign = pct >= 0 ? '+' : '';
        var cls = Math.abs(pct) < 0.5 ? 'flat' : (pct > 0 ? 'up' : 'down');
        // 인구 증감의 색상 의미는 부동산과 다름 — flat 톤으로 통일
        return {raw: pct, display: '<span class="compare-trend-cell flat">' + sign + pct.toFixed(1) + '%</span>', isHtml: true};
      }, dir: 'high'}
    ];

    var html = '<table class="compare-table"><thead><tr>';
    html += '<th>지표</th>';
    records.forEach(function(r) {
      html += '<th class="sgg-head">' + escHtml(r.name) + '<span class="sub">' + escHtml(r.sido_name) + '</span></th>';
    });
    html += '</tr></thead><tbody>';

    metrics.forEach(function(m) {
      var values = records.map(function(r) { return m.get(r); });
      var raws = values.map(function(v) { return v.raw; }).filter(function(v) { return v !== null && v !== undefined; });
      var best = null, worst = null;
      if (raws.length >= 2) {
        if (m.dir === 'high') {
          best = Math.max.apply(null, raws);
          worst = Math.min.apply(null, raws);
        } else {
          best = Math.min.apply(null, raws);
          worst = Math.max.apply(null, raws);
        }
      }
      html += '<tr><td class="metric-label">' + escHtml(m.label) + '</td>';
      values.forEach(function(v) {
        var cls = 'value';
        if (best !== null && v.raw === best && raws.length >= 2 && best !== worst) cls += ' best';
        else if (worst !== null && v.raw === worst && raws.length >= 2 && best !== worst) cls += ' worst';
        // 추세 셀은 isHtml로 들어오므로 escape하지 않음
        var content = v.isHtml ? v.display : escHtml(v.display);
        html += '<td class="' + cls + '">' + content + '</td>';
      });
      html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
  }

  // 이벤트 바인딩
  document.addEventListener('click', function(e) {
    var addBtn = e.target.closest('.compare-add');
    if (addBtn) {
      e.preventDefault();
      e.stopPropagation();
      var slugkey = addBtn.dataset.slugkey;
      var name = addBtn.dataset.name;
      var sido = addBtn.dataset.sido;
      if (compareList.some(function(x) { return x.slugkey === slugkey; })) {
        removeFromCompare(slugkey);
      } else {
        addToCompare(slugkey, name, sido);
      }
      return;
    }
    var xBtn = e.target.closest('.compare-chip-x');
    if (xBtn) {
      e.preventDefault();
      removeFromCompare(xBtn.dataset.slugkey);
      return;
    }
  });

  BTN_SHOW.addEventListener('click', showCompareView);
  BTN_BACK.addEventListener('click', hideCompareView);
  BTN_CLEAR.addEventListener('click', function() {
    if (compareList.length === 0) return;
    if (confirm('비교 목록을 모두 비울까요?')) clearCompare();
  });
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
