// Q렌즈 — site.js

// 진행 바
function initProgressBar() {
  const bar = document.querySelector('.ql-progress-bar');
  if (!bar) return;
  window.addEventListener('scroll', () => {
    const doc = document.documentElement;
    const scrolled = doc.scrollTop || document.body.scrollTop;
    const total = doc.scrollHeight - doc.clientHeight;
    bar.style.width = (scrolled / total * 100) + '%';
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initProgressBar();
});
