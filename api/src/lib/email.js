// 이메일 발송 — Resend (https://resend.com)
// RESEND_API_KEY 미등록 시 콘솔 로그로 동작 (개발 단계). Resend 가입 후 secret 등록하면 자동으로 실제 발송.

export async function sendEmail({ to, subject, html, env }) {
  if (!env.RESEND_API_KEY) {
    console.log('[email-stub]', { to, subject });
    console.log(html);
    return { ok: true, stub: true };
  }
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      // ⚠️ from 도메인은 Resend에서 도메인 인증 후 사용 가능. 인증 전에는 onboarding@resend.dev 사용.
      from: 'Q렌즈 <noreply@q-bot.kr>',
      to,
      subject,
      html
    })
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Resend send failed: ${res.status} ${text}`);
  }
  return res.json();
}

export function emailVerifyTemplate({ nickname, verifyUrl }) {
  return `
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Pretendard Variable', sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #3182f6; margin-top: 0;">Q렌즈 가입 확인</h2>
  <p>안녕하세요 ${escapeHtml(nickname)}님,</p>
  <p>아래 버튼을 눌러 이메일을 확인하시면 가입이 완료됩니다.</p>
  <p style="margin: 24px 0;">
    <a href="${verifyUrl}" style="background: #3182f6; color: #fff; padding: 12px 24px; border-radius: 4px; text-decoration: none; display: inline-block; font-weight: 600;">이메일 확인하기</a>
  </p>
  <p style="color: #666; font-size: 14px;">버튼이 작동하지 않으면 다음 링크를 복사해 브라우저에 붙여넣으세요:</p>
  <p style="color: #3182f6; font-size: 13px; word-break: break-all;">${verifyUrl}</p>
  <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0;">
  <p style="color: #999; font-size: 12px;">본 메일은 발신 전용입니다. 가입을 신청하지 않으셨다면 무시하셔도 됩니다.</p>
</div>
`.trim();
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
