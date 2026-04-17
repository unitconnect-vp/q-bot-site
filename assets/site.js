/* Q-Lens site.js v3.3
 * - 아티클 progress bar
 * - 홈 피드 렌더링: featured / rank / authors / series / recent
 * - 페이지 라우터: /authors/, /authors/{id}/, /series/, /series/{id}/
 */

(function () {
  'use strict';

  // ============================================
  // 1. Progress bar (모든 페이지 공통)
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
  // 2. 데이터 로더
  // ============================================
  function loadData() {
    return Promise.all([
      fetch('/articles/articles.json').then(r => r.json()),
      fetch('/data/series.json').then(r => r.ok ? r.json() : []).catch(() => []),
      fetch('/data/authors.json').then(r => r.ok ? r.json() : []).catch(() => [])
    ]);
  }

  // ============================================
  // 3. 라우터 — 페이지 유형별 렌더링
  // ============================================
  const homeFeed = document.getElementById('qlens-home');
  const authorList = document.getElementById('qlens-author-list');
  const authorDetail = document.getElementById('qlens-author-detail');
  const seriesList = document.getElementById('qlens-series-list');
  const seriesDetail = document.getElementById('qlens-series-detail');

  if (homeFeed) {
    loadData().then(([articles, seriesArr, authorsArr]) => {
      const sorted = sortByDate(articles);
      renderHomeFeatured(sorted);
      renderHomeRank(sorted);
      renderHomeAuthors(authorsArr, sorted);
      renderHomeSeries(seriesArr, sorted);
      renderHomeRecent(sorted);
    }).catch(handleError);
  } else if (authorList) {
    loadData().then(([articles, _, authorsArr]) => {
      renderAuthorList(authorsArr, articles);
    }).catch(handleError);
  } else if (authorDetail) {
    const authorId = authorDetail.dataset.authorId;
    loadData().then(([articles, _, authorsArr]) => {
      renderAuthorDetail(authorId, authorsArr, articles);
    }).catch(handleError);
  } else if (seriesList) {
    loadData().then(([articles, seriesArr]) => {
      renderSeriesList(seriesArr, articles);
    }).catch(handleError);
  } else if (seriesDetail) {
    const seriesId = seriesDetail.dataset.seriesId;
    loadData().then(([articles, seriesArr]) => {
      renderSeriesDetail(seriesId, seriesArr, articles);
    }).catch(handleError);
  }

  function sortByDate(arr) {
    return [...arr].sort((a, b) => new Date(b.date) - new Date(a.date));
  }

  function handleError(err) {
    console.error('Failed to load data:', err);
  }

  // ============================================
  // 4. 홈 피드 렌더러
  // ============================================

  function renderHomeFeatured(articles) {
    const target = document.getElementById('home-hero');
    if (!target) return;
    let hero = articles.find(a => a.featured === true);
    if (!hero) hero = articles[0];
    if (!hero) return;

    const excerpt = hero.excerpt || '';
    target.innerHTML = `
      <a href="/articles/${hero.slug}/" class="hero-weekly">
        <div class="hero-weekly__img">
          <img src="/articles/${hero.slug}/thumb.webp" alt="${esc(hero.title)}" loading="eager">
        </div>
        <div class="hero-weekly__body">
          <p class="hero-weekly__label">이 주의 콘텐츠</p>
          <h2 class="hero-weekly__title">${esc(hero.title)}</h2>
          ${excerpt ? `<p class="hero-weekly__excerpt">${esc(excerpt)}</p>` : ''}
          <p class="hero-weekly__meta">
            <span class="hero-weekly__cat">${esc(hero.category)}</span>
            · ${esc(hero.author)} · ${esc(hero.date)} · ${esc(hero.read_time)}
          </p>
        </div>
      </a>
    `;
  }

  function renderHomeRank(articles) {
    const target = document.getElementById('home-rank');
    if (!target) return;
    const top5 = articles.slice(0, 5);
    target.innerHTML = `
      <ol class="rank-list">
        ${top5.map((a, i) => `
          <li class="rank-item">
            <a href="/articles/${a.slug}/" class="rank-link">
              <span class="rank-num">${i + 1}</span>
              <div class="rank-body">
                <p class="rank-title">${esc(a.title)}</p>
                <p class="rank-meta">${esc(a.author)} · ${esc(a.category)}</p>
              </div>
            </a>
          </li>
        `).join('')}
      </ol>
    `;
  }

  function renderHomeAuthors(authors, articles) {
    const target = document.getElementById('home-authors');
    if (!target) return;
    if (!authors.length) { target.style.display = 'none'; return; }

    const counts = {};
    articles.forEach(a => { counts[a.author] = (counts[a.author] || 0) + 1; });

    target.innerHTML = `
      <div class="author-grid">
        ${authors.map(author => `
          <a href="/authors/${author.id}/" class="author-card" style="--author-accent:${author.accent}">
            <div class="author-logo">
              <img src="${author.logo_svg}" alt="${esc(author.name)} logo" loading="lazy">
            </div>
            <p class="author-name">${esc(author.name)}</p>
            <p class="author-tagline">${esc(author.tagline)}</p>
            <p class="author-count">아티클 ${counts[author.name] || 0}편</p>
          </a>
        `).join('')}
      </div>
    `;
  }

  function renderHomeSeries(seriesList, articles) {
    const target = document.getElementById('home-series');
    if (!target) return;
    if (!seriesList.length) { target.style.display = 'none'; return; }

    const countBy = {};
    articles.forEach(a => {
      if (a.series) countBy[a.series] = (countBy[a.series] || 0) + 1;
    });

    target.innerHTML = `
      <div class="series-grid">
        ${seriesList.map(s => `
          <a href="/series/${s.id}/" class="series-card" style="--series-accent:${s.accent || '#b5470f'}">
            <div class="series-emoji">${s.cover_emoji || '📚'}</div>
            <p class="series-title">${esc(s.title)}</p>
            <p class="series-desc">${esc(s.description || '')}</p>
            <p class="series-meta">아티클 ${countBy[s.id] || 0}편 · ${s.status === 'ongoing' ? '연재 중' : '완결'}</p>
          </a>
        `).join('')}
      </div>
    `;
  }

  function renderHomeRecent(articles) {
    const target = document.getElementById('home-recent');
    if (!target) return;
    const recent = articles.filter(a => !a.featured).slice(0, 6);
    target.innerHTML = `
      <div class="recent-grid">
        ${recent.map(a => `
          <a href="/articles/${a.slug}/" class="recent-card">
            <img class="recent-thumb" src="/articles/${a.slug}/thumb.webp" alt="${esc(a.title)}" loading="lazy">
            <div class="recent-body">
              <p class="recent-cat">${esc(a.category)}</p>
              <p class="recent-title">${esc(a.title)}</p>
              <p class="recent-meta">${esc(a.author)} · ${esc(a.date)}</p>
            </div>
          </a>
        `).join('')}
      </div>
    `;
  }

  // ============================================
  // 5. 필진 페이지 렌더러
  // ============================================

  function renderAuthorList(authors, articles) {
    const target = document.getElementById('qlens-author-list');
    if (!target) return;
    const counts = {};
    articles.forEach(a => { counts[a.author] = (counts[a.author] || 0) + 1; });

    target.innerHTML = `
      <h1 class="page-title">필진</h1>
      <p class="page-subtitle">세 목소리가 전하는 오늘의 인사이트</p>
      <div class="author-list-grid">
        ${authors.map(author => `
          <a href="/authors/${author.id}/" class="author-list-card" style="--author-accent:${author.accent}">
            <div class="author-logo author-logo--lg">
              <img src="${author.logo_svg}" alt="${esc(author.name)} logo" loading="lazy">
            </div>
            <div class="author-list-body">
              <p class="author-name">${esc(author.name)}</p>
              <p class="author-tagline">${esc(author.tagline)}</p>
              <p class="author-bio">${esc(author.bio)}</p>
              <p class="author-cats">담당: ${author.categories.map(esc).join(' · ')}</p>
              <p class="author-count">아티클 ${counts[author.name] || 0}편 →</p>
            </div>
          </a>
        `).join('')}
      </div>
    `;
  }

  function renderAuthorDetail(authorId, authors, articles) {
    const target = document.getElementById('qlens-author-detail');
    if (!target) return;
    const author = authors.find(a => a.id === authorId);
    if (!author) {
      target.innerHTML = '<p style="color:#6b7280;">필자를 찾을 수 없습니다.</p>';
      return;
    }

    const myArticles = sortByDate(articles.filter(a => a.author === author.name));
    document.title = `${author.name} — ${author.tagline} | Q렌즈`;

    target.innerHTML = `
      <header class="author-detail-head" style="--author-accent:${author.accent}">
        <div class="author-detail-logo">
          <img src="${author.logo_svg}" alt="${esc(author.name)} logo">
        </div>
        <h1 class="author-detail-name">${esc(author.name)}</h1>
        <p class="author-detail-tagline">${esc(author.tagline)}</p>
        <p class="author-detail-bio">${esc(author.bio)}</p>
        <p class="author-detail-cats">${author.categories.map(c => `<span>${esc(c)}</span>`).join(' ')}</p>
      </header>

      <section class="author-articles">
        <h2 class="section-title">${esc(author.name)}가 쓴 아티클 (${myArticles.length}편)</h2>
        ${myArticles.length === 0 ? '<p style="color:#6b7280;">아직 발행된 아티클이 없습니다.</p>' : `
          <div class="recent-grid">
            ${myArticles.map(a => `
              <a href="/articles/${a.slug}/" class="recent-card">
                <img class="recent-thumb" src="/articles/${a.slug}/thumb.webp" alt="${esc(a.title)}" loading="lazy">
                <div class="recent-body">
                  <p class="recent-cat">${esc(a.category)}</p>
                  <p class="recent-title">${esc(a.title)}</p>
                  <p class="recent-meta">${esc(a.date)} · ${esc(a.read_time)}</p>
                </div>
              </a>
            `).join('')}
          </div>
        `}
      </section>
    `;
  }

  // ============================================
  // 6. 시리즈 페이지 렌더러
  // ============================================

  function renderSeriesList(seriesArr, articles) {
    const target = document.getElementById('qlens-series-list');
    if (!target) return;
    const countBy = {};
    articles.forEach(a => {
      if (a.series) countBy[a.series] = (countBy[a.series] || 0) + 1;
    });

    target.innerHTML = `
      <h1 class="page-title">오리지널 시리즈</h1>
      <p class="page-subtitle">주제를 따라 길게 읽기</p>
      ${seriesArr.length === 0 ? '<p style="color:#6b7280;">진행 중인 시리즈가 없습니다.</p>' : `
        <div class="series-grid">
          ${seriesArr.map(s => `
            <a href="/series/${s.id}/" class="series-card" style="--series-accent:${s.accent || '#b5470f'}">
              <div class="series-emoji">${s.cover_emoji || '📚'}</div>
              <p class="series-title">${esc(s.title)}</p>
              <p class="series-desc">${esc(s.description || '')}</p>
              <p class="series-meta">아티클 ${countBy[s.id] || 0}편 · ${s.status === 'ongoing' ? '연재 중' : '완결'}</p>
            </a>
          `).join('')}
        </div>
      `}
    `;
  }

  function renderSeriesDetail(seriesId, seriesArr, articles) {
    const target = document.getElementById('qlens-series-detail');
    if (!target) return;
    const series = seriesArr.find(s => s.id === seriesId);
    if (!series) {
      target.innerHTML = '<p style="color:#6b7280;">시리즈를 찾을 수 없습니다.</p>';
      return;
    }

    const myArticles = articles
      .filter(a => a.series === series.id)
      .sort((a, b) => {
        if (a.series_order && b.series_order) return a.series_order - b.series_order;
        return new Date(a.date) - new Date(b.date);
      });

    document.title = `${series.title} | Q렌즈 시리즈`;

    target.innerHTML = `
      <header class="series-detail-head" style="--series-accent:${series.accent || '#b5470f'}">
        <p class="series-detail-label">오리지널 시리즈</p>
        <div class="series-detail-emoji">${series.cover_emoji || '📚'}</div>
        <h1 class="series-detail-title">${esc(series.title)}</h1>
        <p class="series-detail-desc">${esc(series.description || '')}</p>
        <p class="series-detail-meta">아티클 ${myArticles.length}편 · ${series.status === 'ongoing' ? '연재 중' : '완결'} · 시작 ${esc(series.started_at || '')}</p>
      </header>

      <section class="series-articles">
        <h2 class="section-title">연재 순서</h2>
        ${myArticles.length === 0 ? '<p style="color:#6b7280;">아직 등록된 아티클이 없습니다.</p>' : `
          <ol class="series-order-list">
            ${myArticles.map((a, i) => `
              <li class="series-order-item">
                <a href="/articles/${a.slug}/" class="series-order-link">
                  <span class="series-order-num">${a.series_order || (i + 1)}</span>
                  <div class="series-order-body">
                    <p class="series-order-title">${esc(a.title)}</p>
                    <p class="series-order-excerpt">${esc(a.excerpt || '')}</p>
                    <p class="series-order-meta">${esc(a.author)} · ${esc(a.date)} · ${esc(a.read_time)}</p>
                  </div>
                </a>
              </li>
            `).join('')}
          </ol>
        `}
      </section>
    `;
  }

  // ============================================
  // 유틸
  // ============================================
  function esc(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
})();
