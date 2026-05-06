/**
 * Q렌즈 SNS 공유 helper
 * 의존성: 없음 (vanilla JS)
 *
 * 사용:
 *   QLensShare.toX(text);                   // X(Twitter) intent
 *   QLensShare.toThreads(text);             // Threads intent
 *   QLensShare.copy(text, {                 // 클립보드 복사 (Instagram용)
 *     onSuccess: msg => showToast(msg),
 *     onFail:    msg => showToast(msg)
 *   });
 *
 * 인스타그램 한계:
 *   - Instagram은 텍스트 share intent를 제공하지 않으므로 클립보드 복사로 대체.
 *   - 사용자가 Instagram 앱을 열어 직접 붙여넣어야 함.
 */
(function () {
  'use strict';

  function toX(text) {
    var url = 'https://twitter.com/intent/tweet?text=' + encodeURIComponent(text);
    window.open(url, '_blank', 'noopener,noreferrer');
  }

  function toThreads(text) {
    var url = 'https://www.threads.net/intent/post?text=' + encodeURIComponent(text);
    window.open(url, '_blank', 'noopener,noreferrer');
  }

  function copy(text, opts) {
    opts = opts || {};
    var onSuccess = opts.onSuccess || function () {};
    var onFail = opts.onFail || function () {};
    var successMsg = opts.successMsg || '결과를 복사했습니다. 인스타그램 앱에 붙여넣어 공유하세요.';
    var failMsg = opts.failMsg || '복사에 실패했습니다';

    if (!navigator.clipboard || !navigator.clipboard.writeText) {
      onFail('복사 기능을 사용할 수 없습니다');
      return;
    }
    navigator.clipboard.writeText(text).then(
      function () { onSuccess(successMsg); },
      function () { onFail(failMsg); }
    );
  }

  window.QLensShare = { toX: toX, toThreads: toThreads, copy: copy };
})();
