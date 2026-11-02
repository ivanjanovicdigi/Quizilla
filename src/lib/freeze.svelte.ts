import { session } from './session.svelte';

// Score freeze before the final results: from 2026-11-02 23:00 Bratislava time (CET = UTC+1)
// nobody but the admin sees points (leaderboard, stats, home, topic, quiz). Answers still count
// until midnight (027 final_cutoff); the winners are announced the next day.
// Client-side only – the server still returns the numbers.
export const SCORES_HIDDEN_FROM = Date.parse('2026-11-02T22:00:00Z');

// Accounts that see the freeze right away (to preview it). SHA-256 of the lower-case email,
// so no address is in the public repo.
const PREVIEW_EMAIL_HASHES = ['ed6325920e79179b618fa63de67cdf270c02673845c9321511b5460f8d4cb95e'];

const clock = $state({ now: Date.now() });
const preview = $state({ email: '', on: false });
if (typeof window !== 'undefined') setInterval(() => (clock.now = Date.now()), 10_000);

async function checkPreview(email: string) {
  preview.email = email;
  preview.on = false;
  if (!email || !crypto?.subtle) return;
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(email));
  const hex = [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
  if (preview.email === email) preview.on = PREVIEW_EMAIL_HASHES.includes(hex);
}

/** True when scores must be hidden for the current user (everyone except the admin). */
export function scoresHidden(): boolean {
  if (session.admin) return false;
  const email = session.student?.email.toLowerCase() ?? '';
  if (email !== preview.email) queueMicrotask(() => checkPreview(email));
  return preview.on || clock.now >= SCORES_HIDDEN_FROM;
}
