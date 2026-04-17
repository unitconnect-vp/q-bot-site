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
      fetch('/data/authors.json').then(r => r.ok ? r.json() : []).catch(() => []),
      fetch('/data/categories.json').then(r => r.ok ? r.json() : []).catch(() => [])
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
  const categoryList = document.getElementById('qlens-category-list');
  const categoryDetail = document.getElementById('qlens-category-detail');

  if (homeFeed) {
    loadData().then(([articles, seriesArr, authorsArr, categoriesArr]) => {
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
  } else if (categoryList) {
    loadData().then(([articles, _, authorsArr, categoriesArr]) => {
      renderCategoryList(categoriesArr, authorsArr, articles);
    }).catch(handleError);
  } else if (categoryDetail) {
    const categoryId = categoryDetail.dataset.categoryId;
    loadData().then(([articles, _, authorsArr, categoriesArr]) => {
      renderCategoryDetail(categoryId, categoriesArr, authorsArr, articles);
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

    // 글 있는 필자 먼저, 없는 필자는 뒤로
    const sorted = [...authors].sort((a, b) => (counts[b.name] || 0) - (counts[a.name] || 0));

    // 데스크톱 기본 4명, 나머지는 collapse
    // 모바일에서는 CSS로 3명만 보이고 나머지 접힘 처리
    const cardHtml = (author) => `
      <a href="/authors/${author.id}/" class="author-card" style="--author-accent:${author.accent}">
        <div class="author-logo">
          <img src="${author.logo_svg}" alt="${esc(author.name)} logo" loading="lazy">
        </div>
        <p class="author-name">${esc(author.name)}</p>
        <p class="author-tagline">${esc(author.tagline)}</p>
        <p class="author-count">아티클 ${counts[author.name] || 0}편</p>
      </a>
    `;

    const initialCount = 4;  // 데스크톱 기본 노출
    const firstBatch = sorted.slice(0, initialCount);
    const restBatch = sorted.slice(initialCount);

    target.innerHTML = `
      <div class="author-grid" data-author-grid>
        ${firstBatch.map(cardHtml).join('')}
        <div class="author-rest" data-author-rest aria-hidden="true">
          ${restBatch.map(cardHtml).join('')}
        </div>
      </div>
      <div class="section-more">
        <button type="button" class="author-toggle" data-author-toggle aria-expanded="false">
          <span class="author-toggle__label">전체 필진 ${authors.length}명 보기</span>
          <span class="author-toggle__icon" aria-hidden="true">↓</span>
        </button>
      </div>
    `;

    // 토글 동작
    const toggleBtn = target.querySelector('[data-author-toggle]');
    const restWrap = target.querySelector('[data-author-rest]');
    const labelEl = target.querySelector('.author-toggle__label');
    const iconEl = target.querySelector('.author-toggle__icon');
    
    toggleBtn.addEventListener('click', () => {
      const expanded = toggleBtn.getAttribute('aria-expanded') === 'true';
      toggleBtn.setAttribute('aria-expanded', !expanded);
      restWrap.setAttribute('aria-hidden', expanded);
      if (expanded) {
        labelEl.textContent = `전체 필진 ${authors.length}명 보기`;
        iconEl.textContent = '↓';
      } else {
        labelEl.textContent = '접기';
        iconEl.textContent = '↑';
      }
    });
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
      <header class="author-hero" style="--author-accent:${author.accent}">
        <div class="author-hero__logo">
          <img src="${author.logo_svg}" alt="${esc(author.name)} logo">
        </div>
        <div class="author-hero__body">
          <span class="author-hero__label">필진</span>
          <h1 class="author-hero__name">${esc(author.name)}</h1>
          <p class="author-hero__tagline">${esc(author.tagline)}</p>
          <p class="author-hero__bio">${esc(author.bio)}</p>
          <p class="author-hero__cats">${author.categories.map(esc).join(' · ')}</p>
        </div>
      </header>

      <section class="author-articles">
        <h2 class="section-title">${esc(author.name)}가 쓴 아티클 ${myArticles.length}편</h2>
        ${myArticles.length === 0 ? '<p class="empty-state">아직 발행된 아티클이 없습니다.</p>' : `
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
      <header class="series-hero" style="--series-accent:${series.accent || '#b5470f'}">
        <div class="series-hero__emoji">${series.cover_emoji || '📚'}</div>
        <span class="series-hero__label">오리지널 시리즈</span>
        <h1 class="series-hero__title">${esc(series.title)}</h1>
        <p class="series-hero__desc">${esc(series.description || '')}</p>
        <p class="series-hero__meta">아티클 ${myArticles.length}편 · ${series.status === 'ongoing' ? '연재 중' : '완결'} · 시작 ${esc(series.started_at || '')}</p>
      </header>

      <section class="series-articles">
        <h2 class="section-title">연재 순서</h2>
        ${myArticles.length === 0 ? '<p class="empty-state">아직 등록된 아티클이 없습니다.</p>' : `
          <div class="series-list">
            ${myArticles.map((a, i) => `
              <a href="/articles/${a.slug}/" class="series-episode">
                <span class="series-episode__num">${a.series_order || (i + 1)}</span>
                <div class="series-episode__body">
                  <p class="series-episode__cat">${esc(a.category)}</p>
                  <p class="series-episode__title">${esc(a.title)}</p>
                  <p class="series-episode__excerpt">${esc(a.excerpt || '')}</p>
                  <p class="series-episode__meta">${esc(a.author)} · ${esc(a.date)} · ${esc(a.read_time)}</p>
                </div>
              </a>
            `).join('')}
          </div>
        `}
      </section>
    `;
  }

  // ============================================
  // 7. 카테고리 페이지 렌더러
  // ============================================
  function renderCategoryList(categories, authors, articles) {
    const target = document.getElementById('qlens-category-list');
    if (!target) return;
    if (!categories.length) {
      target.innerHTML = '<p class="empty-state">카테고리가 준비 중입니다.</p>';
      return;
    }
    const counts = {};
    articles.forEach(a => { counts[a.category] = (counts[a.category] || 0) + 1; });
    const authorById = {};
    authors.forEach(a => { authorById[a.id] = a; });

    target.innerHTML = `
      <div class="category-grid">
        ${categories.map(c => {
          const author = c.author_ids && c.author_ids[0] ? authorById[c.author_ids[0]] : null;
          const count = counts[c.name] || 0;
          return `
            <a href="/categories/${c.slug}/" class="category-card" ${author ? `style="--cat-accent:${author.accent}"` : ''}>
              <p class="category-card__count">${count}편</p>
              <h3 class="category-card__name">${esc(c.name)}</h3>
              <p class="category-card__desc">${esc(c.description || '')}</p>
              ${author ? `<p class="category-card__author">${esc(author.name)}</p>` : ''}
            </a>
          `;
        }).join('')}
      </div>
    `;
  }

  function renderCategoryDetail(categoryId, categories, authors, articles) {
    const target = document.getElementById('qlens-category-detail');
    if (!target) return;
    const cat = categories.find(c => c.id === categoryId || c.slug === categoryId);
    if (!cat) {
      target.innerHTML = '<p class="empty-state">카테고리를 찾을 수 없습니다.</p>';
      return;
    }
    const author = authors.find(a => cat.author_ids && cat.author_ids.includes(a.id));
    const myArticles = sortByDate(articles.filter(a => a.category === cat.name));

    document.title = `${cat.name} | Q렌즈`;

    target.innerHTML = `
      <header class="category-hero" ${author ? `style="--cat-accent:${author.accent}"` : ''}>
        <span class="category-hero__label">카테고리</span>
        <h1 class="category-hero__title">${esc(cat.name)}</h1>
        <p class="category-hero__desc">${esc(cat.description || '')}</p>
        ${author ? `
          <a href="/authors/${author.id}/" class="category-hero__author">
            <img src="${author.logo_svg}" alt="${esc(author.name)}">
            <span>담당 필진 <strong>${esc(author.name)}</strong></span>
          </a>
        ` : ''}
      </header>
      ${myArticles.length === 0
        ? '<p class="empty-state">아직 이 카테고리의 아티클이 없습니다.</p>'
        : `<div class="recent-grid">
            ${myArticles.map(a => `
              <a href="/articles/${a.slug}/" class="recent-card">
                <img class="recent-thumb" src="/articles/${a.slug}/thumb.webp" alt="${esc(a.title)}" loading="lazy">
                <div class="recent-body">
                  <p class="recent-cat">${esc(a.category)}</p>
                  <p class="recent-title">${esc(a.title)}</p>
                  <p class="recent-meta">${esc(a.author)} · ${esc(a.date)}</p>
                </div>
              </a>
            `).join('')}
          </div>`
      }
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
