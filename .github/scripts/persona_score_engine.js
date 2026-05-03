/*!
 * persona_score_v3.js
 * 거주지 의사결정 도구 — 페르소나 점수 함수 (브라우저 사이드)
 * 
 * 사용:
 *   const engine = new PersonaScoreEngine(records);  // 한 번만 호출 (그룹별 percentile 사전 계산)
 *   engine.score('seoul/gangnam', '자녀가족', 60);   // 슬라이더 조작 시마다 호출 (가벼움)
 */

const WEIGHTS = {
  '신혼':     { price_value: 25, rent_value: 15, school_density: 5, biz_convenience: 10, medical_access: 10, environment: 20, population_vitality: 10, life_stability: 0 },
  '자녀가족': { price_value: 15, rent_value: 10, school_density: 30, biz_convenience: 5, medical_access: 15, environment: 15, population_vitality: 0, life_stability: 10 },
  '은퇴':     { price_value: 15, rent_value: 0,  school_density: 0,  biz_convenience: 5, medical_access: 35, environment: 20, population_vitality: 0, life_stability: 25 },
  '1인가구':  { price_value: 0,  rent_value: 35, school_density: 0,  biz_convenience: 20, medical_access: 15, environment: 15, population_vitality: 10, life_stability: 0 },
};

const PERSONA_DEFAULT_T = { '신혼': 50, '자녀가족': 60, '은퇴': 40, '1인가구': 70 };
const UNAVAILABLE = new Set(['biz_convenience', 'life_stability']);  // v3.1: population_vitality 활성화
const INVERSE_METRICS = new Set(['price_value', 'rent_value', 'environment']);

const populationGroup = (pop) => {
  if (pop == null) return 'X';
  if (pop >= 300000) return 'A';
  if (pop >= 100000) return 'B';
  return 'C';
};

const groupBonus = (t, group) => {
  const delta = (t - 50) / 50;  // -1 ~ +1
  if (group === 'A') return delta * 15;
  if (group === 'B') return delta * 5;
  if (group === 'C') return -delta * 15;
  return 0;
};

class PersonaScoreEngine {
  constructor(records) {
    this.records = records;
    this._precompute();
  }
  
  _extractMetrics(record) {
    const s = record.sections || {};
    const pop = (s.population || {}).sgg_total || 0;
    const trade = s.real_estate_trade || {};
    const rent = s.real_estate_rent || {};
    const env = s.environment || {};
    const med = s.medical || {};
    const edu = s.education || {};
    
    let pm25 = null;
    const guSt = env.gu_station || env.sigungu_station;
    if (guSt && typeof guSt === 'object' && guSt.pm25 != null) pm25 = guSt.pm25;
    else if (env.seoul_avg && typeof env.seoul_avg === 'object') pm25 = env.seoul_avg.pm25;
    else if (env.sido_avg && typeof env.sido_avg === 'object') pm25 = env.sido_avg.pm25;
    
    // v3.1: 인구 활력 = 20·30·40대 비율 합 (생산연령 핵심)
    let vitality = null;
    const pageAge = s.population_age;
    if (pageAge && pageAge.shares) {
      const sh = pageAge.shares;
      const sum = (sh['20s'] || 0) + (sh['30s'] || 0) + (sh['40s'] || 0);
      if (sum > 0) vitality = sum;
    }
    
    return {
      population: pop,
      price_value: trade.median_price_per_pyeong_man ?? null,
      rent_value: rent.median_jeonse_man ?? null,
      school_density: pop ? (edu.sgg_count || 0) / pop * 10000 : null,
      medical_access: pop ? (med.sgg_count || 0) / pop * 10000 : null,
      environment: pm25,
      population_vitality: vitality,
    };
  }
  
  _precompute() {
    // 1. 모든 record의 metrics 추출
    this.metrics = new Map();  // slug → metrics
    this.groupMap = new Map(); // slug → 'A'/'B'/'C'
    
    for (const r of this.records) {
      const m = this._extractMetrics(r);
      this.metrics.set(r.slug, m);
      this.groupMap.set(r.slug, populationGroup(m.population));
    }
    
    // 2. 그룹별 분포 (정렬된 배열) 사전 계산
    this.groupDist = { A: {}, B: {}, C: {}, X: {} };
    const keys = ['price_value', 'rent_value', 'school_density', 'medical_access', 'environment', 'population_vitality'];
    
    for (const r of this.records) {
      const m = this.metrics.get(r.slug);
      const g = this.groupMap.get(r.slug);
      for (const k of keys) {
        if (m[k] == null) continue;
        if (!this.groupDist[g][k]) this.groupDist[g][k] = [];
        this.groupDist[g][k].push(m[k]);
      }
    }
    for (const g of Object.keys(this.groupDist)) {
      for (const k of Object.keys(this.groupDist[g])) {
        this.groupDist[g][k].sort((a, b) => a - b);
      }
    }
    
    // 3. 각 record의 그룹 내 percentile 사전 계산
    this.percentiles = new Map();  // slug → {key: pct, ...}
    for (const r of this.records) {
      const m = this.metrics.get(r.slug);
      const g = this.groupMap.get(r.slug);
      const p = {};
      for (const k of keys) {
        const sortedVals = this.groupDist[g][k] || [];
        if (m[k] == null || sortedVals.length === 0) {
          p[k] = null;
          continue;
        }
        // binary search for rank (lower bound)
        let lo = 0, hi = sortedVals.length;
        while (lo < hi) {
          const mid = (lo + hi) >>> 1;
          if (sortedVals[mid] < m[k]) lo = mid + 1; else hi = mid;
        }
        let pct = lo / sortedVals.length * 100;
        if (INVERSE_METRICS.has(k)) pct = 100 - pct;
        p[k] = Math.round(pct * 10) / 10;
      }
      this.percentiles.set(r.slug, p);
    }
  }
  
  /**
   * 슬러그 + 페르소나 + 슬라이더 t로 점수 산출
   * @param {string} slug - 'seoul/gangnam'
   * @param {string} persona - '신혼' | '자녀가족' | '은퇴' | '1인가구'
   * @param {number} t - 0~100 (도시·시골 슬라이더)
   * @returns {number|null} 점수 (0~100) 또는 null (데이터 부재)
   */
  score(slug, persona, t) {
    const p = this.percentiles.get(slug);
    if (!p) return null;
    const weights = WEIGHTS[persona];
    let activeTotal = 0, weightedSum = 0;
    
    for (const [k, w] of Object.entries(weights)) {
      if (w === 0 || UNAVAILABLE.has(k)) continue;
      const pct = p[k];
      if (pct == null) continue;
      weightedSum += pct * w;
      activeTotal += w;
    }
    if (activeTotal === 0) return null;
    
    const baseScore = weightedSum / activeTotal;
    const group = this.groupMap.get(slug);
    const bonus = groupBonus(t, group);
    const final = Math.max(0, Math.min(100, baseScore + bonus));
    return Math.round(final * 10) / 10;
  }
  
  /**
   * 슬러그의 지표별 기여도 — UI에서 "왜 이 점수인가" 표시용
   */
  contributions(slug, persona, t) {
    const p = this.percentiles.get(slug);
    if (!p) return [];
    const weights = WEIGHTS[persona];
    let activeTotal = 0;
    for (const [k, w] of Object.entries(weights)) {
      if (w === 0 || UNAVAILABLE.has(k) || p[k] == null) continue;
      activeTotal += w;
    }
    
    const contribs = [];
    for (const [k, w] of Object.entries(weights)) {
      if (w === 0 || UNAVAILABLE.has(k)) continue;
      const pct = p[k];
      if (pct == null) continue;
      const normalizedW = w / activeTotal;
      contribs.push({
        key: k,
        percentile: pct,
        weight: Math.round(normalizedW * 100 * 10) / 10,
        contribution: Math.round(pct * normalizedW * 10) / 10,
      });
    }
    return contribs.sort((a, b) => b.contribution - a.contribution);
  }
  
  /**
   * 페르소나 + 슬라이더 t로 전국 정렬
   */
  ranking(persona, t, limit = 20) {
    const scored = [];
    for (const r of this.records) {
      const s = this.score(r.slug, persona, t);
      if (s == null) continue;
      scored.push({
        slug: r.slug, name: r.name, sido: r.sido_name,
        group: this.groupMap.get(r.slug), score: s,
      });
    }
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit);
  }
}

// 노출 (브라우저 / Node.js 양쪽 호환)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { PersonaScoreEngine, WEIGHTS, PERSONA_DEFAULT_T };
} else {
  window.PersonaScoreEngine = PersonaScoreEngine;
  window.QLENS_PERSONA_DEFAULT_T = PERSONA_DEFAULT_T;
}
