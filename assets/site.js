/* Q-Lens site.js v5.0 (2026-04-18)
 * - 홈 피드: featured / ranking / categories / writers / series / recent
 * - 4그룹 팔레트 자동 부여 (g-deep/g-coast/g-marine/g-sunset)
 * - 아티클 progress bar
 * - 라우터: /authors/, /authors/{id}/, /series/, /series/{id}/, /categories/
 */

(function () {
  'use strict';

  // ============================================
  // 1. Progress bar (아티클 페이지)
  // ============================================
  const progressBar = document.querySelector('.ql-progress-bar');
  if (progressBar) {
    window.addEventListener('scroll', () => {
      const h = document.documentElement;
      const scrolled = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
      progressBar.style.width = scrolled + '%';
    }, { passive: true });
  }

  // ============================================
  // 2. 유틸
  // ============================================
  function esc(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
  function formatDate(d) {
    if (!d) return '';
    return String(d).replace(/-/g, '.');
  }
  function sortByDate(arr) {
    return [...arr].sort((a, b) => (b.date || '').localeCompare(a.date || ''));
  }
  // 필자 ID로 그룹 찾기 (authors.json의 group 필드)
  function authorGroup(authorName, authorsArr) {
    if (!authorsArr) return 'deep';
    const match = authorsArr.find(a =>
      a.name === authorName ||
      a.name_kr === authorName ||
      a.id === String(authorName).toLowerCase()
    );
    return (match && match.group) || 'deep';
  }

  // ============================================
  // 3. 데이터 로더
  // ============================================
  function loadData() {
    return Promise.all([
      fetch('/articles/articles.json').then(r => r.json()),
      fetch('/data/series.json').then(r => r.ok ? r.json() : []).catch(() => []),
      fetch('/data/authors.json').then(r => r.ok ? r.json() : []).catch(() => []),
      fetch('/data/categories.json').then(r => r.ok ? r.json() : []).catch(() => [])
    ]);
  }
  function handleError(e) {
    console.error('[Q-Lens] Data load error:', e);
  }

  // ============================================
  // 4. 라우터
  // ============================================
  const homeFeed = document.getElementById('qlens-home');
  const authorList = document.getElementById('qlens-author-list');
  const authorDetail = document.getElementById('qlens-author-detail');
  const seriesList = document.getElementById('qlens-series-list');
  const seriesDetail = document.getElementById('qlens-series-detail');
  const categoryList = document.getElementById('qlens-category-list');
  const categoryDetail = document.getElementById('qlens-category-detail');

  if (homeFeed) {
    loadData().then(([articles, seriesArr, authorsArr, categoriesArr]) => {
      const sorted = sortByDate(articles);
      renderHomeFeatured(sorted, authorsArr);
      renderHomeRanking(sorted, authorsArr);
      renderHomeRecent(sorted, authorsArr);
      renderHomeTools();
      renderHomeWriters(authorsArr, sorted);
      renderHomeSeries(seriesArr, sorted);
    }).catch(handleError);
  } else if (authorList) {
    loadData().then(([articles, _, authorsArr]) => {
      renderAuthorList(authorsArr, articles);
    }).catch(handleError);
  } else if (authorDetail) {
    const id = authorDetail.dataset.authorId;
    loadData().then(([articles, _, authorsArr]) => {
      renderAuthorDetail(id, authorsArr, articles);
    }).catch(handleError);
  } else if (seriesList) {
    loadData().then(([articles, seriesArr]) => {
      renderSeriesList(seriesArr, articles);
    }).catch(handleError);
  } else if (seriesDetail) {
    const id = seriesDetail.dataset.seriesId;
    loadData().then(([articles, seriesArr]) => {
      renderSeriesDetail(id, seriesArr, articles);
    }).catch(handleError);
  } else if (categoryList) {
    loadData().then(([articles, _, authorsArr, categoriesArr]) => {
      renderCategoryList(categoriesArr, articles);
    }).catch(handleError);
  } else if (categoryDetail) {
    const id = categoryDetail.dataset.categoryId;
    loadData().then(([articles, _, authorsArr, categoriesArr]) => {
      renderCategoryDetail(id, categoriesArr, authorsArr, articles);
    }).catch(handleError);
  }

  // ============================================
  // 5. 홈 — 피처드 (이 주의 아티클)
  // ============================================
  function renderHomeFeatured(articles, authorsArr) {
    const host = document.getElementById('home-featured');
    if (!host || articles.length === 0) return;
    const hero = articles.find(a => a.featured) || articles[0];
    const group = authorGroup(hero.author, authorsArr);
    const excerpt = hero.excerpt || '';

    host.innerHTML = `
      <a href="/articles/${esc(hero.slug)}/" class="hero-featured__thumb g-${group}">
        <div class="hero-featured__thumb-accent"></div>
        <img src="/articles/${esc(hero.slug)}/thumb.webp" alt="${esc(hero.title)}" loading="eager">
      </a>
      <div>
        <div class="hero-featured__label">이 주의 아티클</div>
        <a href="/articles/${esc(hero.slug)}/">
          <h2 class="hero-featured__title">${esc(hero.title)}</h2>
        </a>
        ${excerpt ? `<p class="hero-featured__sub">${esc(excerpt)}</p>` : ''}
        <div class="hero-featured__meta">
          <span class="cat">${esc(hero.category)}</span>
          <span class="divider">·</span>
          <span>${esc(hero.author)}</span>
          <span class="divider">·</span>
          <span>${formatDate(hero.date)}</span>
          ${hero.read_time ? `<span class="divider">·</span><span>${esc(hero.read_time)}</span>` : ''}
        </div>
      </div>
    `;
  }

  // ============================================
  // 6. 홈 — 지금 많이 읽는 글 (Ranking)
  // ============================================
  function renderHomeRanking(articles, authorsArr) {
    const host = document.getElementById('home-ranking');
    if (!host) return;
    const top = articles.slice(0, Math.min(6, articles.length));
    host.innerHTML = top.map((a, i) => `
      <a href="/articles/${esc(a.slug)}/" class="rank-item">
        <div class="rank-item__num">${i + 1}</div>
        <div class="rank-item__body">
          <div class="rank-item__title">${esc(a.title)}</div>
          <div class="rank-item__meta">
            <span class="cat">${esc(a.category)}</span>
            ${esc(a.author)}${a.read_time ? ` · ${esc(a.read_time)}` : ''}
          </div>
        </div>
      </a>
    `).join('');
  }

  // ============================================
  // 7. 홈 — 최신 아티클 (카드 그리드)
  // ============================================
  function renderHomeRecent(articles, authorsArr) {
    const host = document.getElementById('home-recent');
    if (!host) return;
    const recent = articles.slice(0, 4);
    host.innerHTML = recent.map(a => {
      const group = authorGroup(a.author, authorsArr);
      return `
        <a href="/articles/${esc(a.slug)}/" class="card">
          <div class="card__thumb g-${group}">
            <img src="/articles/${esc(a.slug)}/thumb.webp" alt="${esc(a.title)}" loading="lazy">
          </div>
          <div class="card__cat">${esc(a.category)}</div>
          <div class="card__title">${esc(a.title)}</div>
          ${a.excerpt ? `<div class="card__excerpt">${esc(a.excerpt)}</div>` : ''}
          <div class="card__meta">${esc(a.author)} · ${formatDate(a.date)}</div>
        </a>
      `;
    }).join('');
  }

  // ============================================
  // 8. 홈 — 필진
  // ============================================
  function renderHomeWriters(authors, articles) {
    const host = document.getElementById('home-writers');
    if (!host || !authors || authors.length === 0) return;
    // 각 필자 최신 글 1개 찾기
    const latestByAuthor = {};
    articles.forEach(a => {
      const key = a.author;
      if (!latestByAuthor[key] || a.date > latestByAuthor[key].date) {
        latestByAuthor[key] = a;
      }
    });
    const show = authors.slice(0, 2);
    host.innerHTML = show.map(w => {
      const latest = latestByAuthor[w.name] || latestByAuthor[w.name_kr];
      return `
        <a href="/authors/${esc(w.id)}/" class="writer g-${esc(w.group || 'deep')}">
          <div class="writer__name">${esc(w.name)}</div>
          <div class="writer__tagline">${esc(w.tagline || (w.categories || []).join(' · '))}</div>
          ${latest ? `<div class="writer__latest">${esc(latest.title)}</div>` : ''}
          <div class="writer__bio">${esc(w.bio || '')}</div>
        </a>
      `;
    }).join('');
  }

  // ============================================
  // 9. 홈 — 시리즈
  // ============================================
  function renderHomeSeries(seriesArr, articles) {
    const host = document.getElementById('home-series');
    if (!host || !seriesArr || seriesArr.length === 0) return;
    const counts = {};
    articles.forEach(a => {
      if (a.series) counts[a.series] = (counts[a.series] || 0) + 1;
    });
    const show = seriesArr.slice(0, 6);
    host.innerHTML = show.map(s => `
      <a href="/series/${esc(s.id)}/" class="series-card">
        <div class="series-card__emoji">${esc(s.emoji || '📰')}</div>
        <div class="series-card__name">${esc(s.name)}</div>
        <div class="series-card__desc">${esc(s.description || '')}</div>
        <div class="series-card__count">아티클 ${counts[s.id] || 0}편</div>
      </a>
    `).join('');
  }

  // ============================================
  // 9.5. 홈 — 계산기 (외부 도구 4개)
  // ============================================
  function renderHomeTools() {
    const host = document.getElementById('home-tools');
    if (!host) return;
    const TOOLS_BASE = 'https://heyqbot.github.io/qlens-tools';
    const tools = [
      { slug: 'salary-calculator',     name: '연봉 실수령액',  desc: '월급에서 떼이는 세금·4대보험을 뺀 실수령액을 계산합니다.' },
      { slug: 'severance-calculator',  name: '퇴직금',         desc: '근속연수와 평균임금으로 세전·세후 퇴직금을 계산합니다.' },
      { slug: 'unemployment-calculator', name: '실업급여',     desc: '고용보험 가입기간과 나이로 지급액·지급일수를 계산합니다.' },
      { slug: 'compound-calculator',   name: '복리 투자',      desc: '매월 적립식 투자의 복리 수익을 시각화합니다.' }
    ];
    host.innerHTML = tools.map(t => `
      <a href="${TOOLS_BASE}/${t.slug}.html" target="_blank" rel="noopener" class="card card--text">
        <div class="card__cat">계산기</div>
        <div class="card__title">${esc(t.name)}</div>
        <div class="card__excerpt">${esc(t.desc)}</div>
        <div class="card__meta">qlens-tools</div>
      </a>
    `).join('');
  }

  // ============================================
  // 10. 필진 목록 페이지
  // ============================================
  function renderAuthorList(authors, articles) {
    const host = document.getElementById('qlens-author-list');
    if (!host || !authors) return;
    const counts = {};
    articles.forEach(a => { counts[a.author] = (counts[a.author] || 0) + 1; });
    host.innerHTML = authors.map(w => `
      <a href="/authors/${esc(w.id)}/" class="writer g-${esc(w.group || 'deep')}">
        <div class="writer__name">${esc(w.name)}</div>
        <div class="writer__tagline">${esc(w.tagline || '')}</div>
        <div class="writer__bio">${esc(w.bio || '')}</div>
        <div class="writer__latest">아티클 ${counts[w.name] || counts[w.name_kr] || 0}편</div>
      </a>
    `).join('');
  }

  // ============================================
  // 11. 필진 상세 페이지
  // ============================================
  function renderAuthorDetail(id, authors, articles) {
    const host = document.getElementById('qlens-author-detail');
    if (!host) return;
    const author = authors.find(a => a.id === id);
    if (!author) { host.innerHTML = '<p>필자를 찾을 수 없습니다.</p>'; return; }
    const myArticles = sortByDate(articles.filter(a => a.author === author.name || a.author === author.name_kr));
    const group = author.group || 'deep';
    host.innerHTML = `
      <div class="author-hero g-${esc(group)}" style="padding:48px 0; border-top:3px solid var(--pv-accent); position:relative;">
        <div style="position:absolute; top:-3px; left:0; width:48px; height:3px; background:#000;"></div>
        <h1 style="font-size:2rem; font-weight:800; letter-spacing:-0.035em; margin-bottom:8px;">${esc(author.name)}</h1>
        <p style="color:#6b7280; font-size:0.9375rem; margin-bottom:16px;">${esc(author.tagline || '')}</p>
        <p style="font-size:1rem; line-height:1.7; color:#0a0a0a; max-width:640px;">${esc(author.bio || '')}</p>
      </div>
      <div class="card-grid" style="margin-top:48px;">
        ${myArticles.map(a => `
          <a href="/articles/${esc(a.slug)}/" class="card">
            <div class="card__thumb g-${esc(group)}">
              <img src="/articles/${esc(a.slug)}/thumb.webp" alt="${esc(a.title)}" loading="lazy">
            </div>
            <div class="card__cat">${esc(a.category)}</div>
            <div class="card__title">${esc(a.title)}</div>
            ${a.excerpt ? `<div class="card__excerpt">${esc(a.excerpt)}</div>` : ''}
            <div class="card__meta">${formatDate(a.date)}</div>
          </a>
        `).join('')}
      </div>
    `;
  }

  // ============================================
  // 12. 시리즈 목록
  // ============================================
  function renderSeriesList(seriesArr, articles) {
    const host = document.getElementById('qlens-series-list');
    if (!host || !seriesArr) return;
    const counts = {};
    articles.forEach(a => { if (a.series) counts[a.series] = (counts[a.series] || 0) + 1; });
    host.innerHTML = `
      <div class="series-grid">
        ${seriesArr.map(s => `
          <a href="/series/${esc(s.id)}/" class="series-card">
            <div class="series-card__emoji">${esc(s.emoji || '📰')}</div>
            <div class="series-card__name">${esc(s.name)}</div>
            <div class="series-card__desc">${esc(s.description || '')}</div>
            <div class="series-card__count">아티클 ${counts[s.id] || 0}편</div>
          </a>
        `).join('')}
      </div>
    `;
  }

  // ============================================
  // 13. 시리즈 상세
  // ============================================
  function renderSeriesDetail(id, seriesArr, articles) {
    const host = document.getElementById('qlens-series-detail');
    if (!host) return;
    const series = seriesArr.find(s => s.id === id);
    if (!series) { host.innerHTML = '<p>시리즈를 찾을 수 없습니다.</p>'; return; }
    const myArticles = articles
      .filter(a => a.series === id)
      .sort((a, b) => (a.series_order || 0) - (b.series_order || 0));
    host.innerHTML = `
      <div style="padding:48px 0; border-top:4px solid #000; position:relative;">
        <div style="position:absolute; top:-4px; left:0; width:48px; height:4px; background:#3182f6;"></div>
        <div style="font-size:2rem; margin-bottom:12px;">${esc(series.emoji || '📰')}</div>
        <h1 style="font-size:2rem; font-weight:800; letter-spacing:-0.035em; margin-bottom:8px;">${esc(series.name)}</h1>
        <p style="color:#6b7280; font-size:1rem; max-width:640px;">${esc(series.description || '')}</p>
      </div>
      <div class="card-grid" style="margin-top:48px;">
        ${myArticles.map(a => `
          <a href="/articles/${esc(a.slug)}/" class="card">
            <div class="card__thumb g-deep">
              <img src="/articles/${esc(a.slug)}/thumb.webp" alt="${esc(a.title)}" loading="lazy">
            </div>
            <div class="card__cat">${a.series_order ? `${a.series_order}부` : esc(a.category)}</div>
            <div class="card__title">${esc(a.title)}</div>
            <div class="card__meta">${esc(a.author)} · ${formatDate(a.date)}</div>
          </a>
        `).join('')}
      </div>
    `;
  }

  // ============================================
  // 14. 카테고리 목록
  // ============================================
  function renderCategoryList(categories, articles) {
    const host = document.getElementById('qlens-category-list');
    if (!host || !categories) return;
    const counts = {};
    articles.forEach(a => { counts[a.category] = (counts[a.category] || 0) + 1; });
    // group별로 묶어 표시
    const groups = { deep: [], coast: [], marine: [], sunset: [] };
    categories.forEach(c => {
      (groups[c.group || 'deep']).push(c);
    });
    const groupLabels = {
      deep: '경제·금융·투자',
      coast: '사회·데이터',
      marine: 'AI·테크',
      sunset: '조직·성장'
    };
    host.innerHTML = Object.keys(groups).filter(g => groups[g].length > 0).map(g => `
      <div class="section" style="border-top:1px solid #e5e7eb; padding:40px 0 32px;">
        <h2 style="font-size:1.25rem; font-weight:800; letter-spacing:-0.03em; color:#0a0a0a; margin-bottom:20px;">${esc(groupLabels[g])}</h2>
        <div class="card-grid">
          ${groups[g].map(c => `
            <a href="/categories/${esc(c.slug)}/" class="card card--text">
              <div class="card__cat">카테고리</div>
              <div class="card__title">${esc(c.name)}</div>
              <div class="card__excerpt">${esc(c.description || '')}</div>
              <div class="card__meta">아티클 ${counts[c.name] || 0}편</div>
            </a>
          `).join('')}
        </div>
      </div>
    `).join('');
  }

  // ============================================
  // 15. 카테고리 상세
  // ============================================
  function renderCategoryDetail(id, categories, authors, articles) {
    const host = document.getElementById('qlens-category-detail');
    if (!host) return;
    const cat = categories.find(c => c.slug === id || c.id === id);
    if (!cat) { host.innerHTML = '<p>카테고리를 찾을 수 없습니다.</p>'; return; }
    const myArticles = sortByDate(articles.filter(a => a.category === cat.name));
    const group = cat.group || 'deep';
    host.innerHTML = `
      <div class="g-${esc(group)}" style="padding:48px 0; border-top:3px solid var(--pv-accent); position:relative;">
        <div style="position:absolute; top:-3px; left:0; width:48px; height:3px; background:#000;"></div>
        <h1 style="font-size:2rem; font-weight:800; letter-spacing:-0.035em; margin-bottom:8px;">${esc(cat.name)}</h1>
        <p style="color:#6b7280; font-size:1rem; max-width:640px;">${esc(cat.description || '')}</p>
      </div>
      <div class="card-grid" style="margin-top:48px;">
        ${myArticles.map(a => {
          const authorGrp = authorGroup(a.author, authors);
          return `
            <a href="/articles/${esc(a.slug)}/" class="card">
              <div class="card__thumb g-${authorGrp}">
                <img src="/articles/${esc(a.slug)}/thumb.webp" alt="${esc(a.title)}" loading="lazy">
              </div>
              <div class="card__cat">${esc(a.category)}</div>
              <div class="card__title">${esc(a.title)}</div>
              ${a.excerpt ? `<div class="card__excerpt">${esc(a.excerpt)}</div>` : ''}
              <div class="card__meta">${esc(a.author)} · ${formatDate(a.date)}</div>
            </a>
          `;
        }).join('')}
      </div>
    `;
  }

})();
