/* Q-Lens site.js v3.3
 * - 아티클 progress bar (기존)
 * - 홈 피드 렌더링: featured / rank / authors / series / recent
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
  // 2. 홈 피드 렌더링 (홈에서만)
  // ============================================
  const homeFeed = document.getElementById('qlens-home');
  if (!homeFeed) return;

  Promise.all([
    fetch('/articles/articles.json').then(r => r.json()),
    fetch('/data/series.json').then(r => r.ok ? r.json() : []).catch(() => []),
    fetch('/data/authors.json').then(r => r.ok ? r.json() : []).catch(() => [])
  ]).then(([articles, seriesList, authorsList]) => {
    const sorted = [...articles].sort((a, b) => new Date(b.date) - new Date(a.date));

    renderFeatured(sorted);
    renderRank(sorted);
    renderAuthors(authorsList, sorted);
    renderSeries(seriesList, sorted);
    renderRecent(sorted);
  }).catch(err => {
    console.error('Failed to load home feed:', err);
    const fallback = document.getElementById('home-hero');
    if (fallback) fallback.innerHTML =
      '<p style="color:#6b7280;font-size:0.9rem;">콘텐츠를 불러오는 중입니다.</p>';
  });

  // ========== 섹션 1: 이 주의 콘텐츠 (featured) ==========
  function renderFeatured(articles) {
    const target = document.getElementById('home-hero');
    if (!target) return;

    // featured: true 우선, 없으면 최신
    let hero = articles.find(a => a.featured === true);
    if (!hero) hero = articles[0];
    if (!hero) return;

    const excerpt = hero.excerpt || '';
    target.innerHTML = `
      <a href="/articles/${hero.slug}/" class="hero-weekly">
        <div class="hero-weekly__img">
          <img src="/articles/${hero.slug}/thumb.webp" alt="${escapeHtml(hero.title)}" loading="eager">
        </div>
        <div class="hero-weekly__body">
          <p class="hero-weekly__label">이 주의 콘텐츠</p>
          <h2 class="hero-weekly__title">${escapeHtml(hero.title)}</h2>
          ${excerpt ? `<p class="hero-weekly__excerpt">${escapeHtml(excerpt)}</p>` : ''}
          <p class="hero-weekly__meta">
            <span class="hero-weekly__cat">${escapeHtml(hero.category)}</span>
            · ${escapeHtml(hero.author)} · ${escapeHtml(hero.date)} · ${escapeHtml(hero.read_time)}
          </p>
        </div>
      </a>
    `;
  }

  // ========== 섹션 2: 지금 많이 보는 (최신 5개, 번호 리스트) ==========
  function renderRank(articles) {
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
                <p class="rank-title">${escapeHtml(a.title)}</p>
                <p class="rank-meta">${escapeHtml(a.author)} · ${escapeHtml(a.category)}</p>
              </div>
            </a>
          </li>
        `).join('')}
      </ol>
    `;
  }

  // ========== 섹션 3: 필진 큐레이션 ==========
  function renderAuthors(authors, articles) {
    const target = document.getElementById('home-authors');
    if (!target) return;
    if (!authors.length) { target.style.display = 'none'; return; }

    // 각 필자의 글 개수
    const counts = {};
    articles.forEach(a => {
      counts[a.author] = (counts[a.author] || 0) + 1;
    });

    target.innerHTML = `
      <div class="author-grid">
        ${authors.map(author => `
          <a href="/authors/${author.id}/" class="author-card" style="--author-accent:${author.accent}">
            <div class="author-logo">
              <img src="${author.logo_svg}" alt="${escapeHtml(author.name)} logo" loading="lazy">
            </div>
            <p class="author-name">${escapeHtml(author.name)}</p>
            <p class="author-tagline">${escapeHtml(author.tagline)}</p>
            <p class="author-count">아티클 ${counts[author.name] || 0}편</p>
          </a>
        `).join('')}
      </div>
    `;
  }

  // ========== 섹션 4: 오리지널 시리즈 ==========
  function renderSeries(seriesList, articles) {
    const target = document.getElementById('home-series');
    if (!target) return;
    if (!seriesList.length) { target.style.display = 'none'; return; }

    // 시리즈별 글 개수
    const countBySeries = {};
    articles.forEach(a => {
      if (a.series) countBySeries[a.series] = (countBySeries[a.series] || 0) + 1;
    });

    target.innerHTML = `
      <div class="series-grid">
        ${seriesList.map(s => `
          <a href="/series/${s.id}/" class="series-card" style="--series-accent:${s.accent || '#b5470f'}">
            <div class="series-emoji">${s.cover_emoji || '📚'}</div>
            <p class="series-title">${escapeHtml(s.title)}</p>
            <p class="series-desc">${escapeHtml(s.description || '')}</p>
            <p class="series-meta">아티클 ${countBySeries[s.id] || 0}편 · ${s.status === 'ongoing' ? '연재 중' : '완결'}</p>
          </a>
        `).join('')}
      </div>
    `;
  }

  // ========== 섹션 6: 최신 아티클 ==========
  function renderRecent(articles) {
    const target = document.getElementById('home-recent');
    if (!target) return;

    // featured 제외한 최신 6개
    const recent = articles.filter(a => !a.featured).slice(0, 6);

    target.innerHTML = `
      <div class="recent-grid">
        ${recent.map(a => `
          <a href="/articles/${a.slug}/" class="recent-card">
            <img class="recent-thumb" src="/articles/${a.slug}/thumb.webp" alt="${escapeHtml(a.title)}" loading="lazy">
            <div class="recent-body">
              <p class="recent-cat">${escapeHtml(a.category)}</p>
              <p class="recent-title">${escapeHtml(a.title)}</p>
              <p class="recent-meta">${escapeHtml(a.author)} · ${escapeHtml(a.date)}</p>
            </div>
          </a>
        `).join('')}
      </div>
    `;
  }

  // ========== 유틸 ==========
  function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
})();
