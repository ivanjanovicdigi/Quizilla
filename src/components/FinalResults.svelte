<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import Logo from './Logo.svelte';
  import { api, ApiError } from '../lib/api';
  import { errorText, i18n, t } from '../lib/i18n.svelte';
  import type { FinalResults } from '../lib/types';

  // Full-screen presentation of the final results (027_final_results.sql), admin only.
  // Live data, but the server counts only answers before quiz.config 'final_cutoff'.
  // Steps: 0 last 10 answers · 1 podium · 2–4 reveal 3rd/2nd/1st · 5 classes (hidden) · 6 classes count up.
  let { token, onClose, onError }: { token: string; onClose: () => void; onError: (code: string) => void } = $props();

  let data = $state<FinalResults | null>(null);
  let error = $state('');
  let step = $state(0);
  let counting = $state(false); // class bars are counting up
  let crowned = $state(false); // count-up finished → winner shown
  let counts = $state<number[]>([]);

  async function load() {
    error = '';
    try {
      data = await api.adminFinalResults(token);
    } catch (e) {
      const code = e instanceof ApiError ? e.code : 'server';
      if (code === 'not_admin') onError(code);
      else error = errorText(code);
    }
  }

  const locale = $derived(i18n.lang === 'sk' ? 'sk-SK' : 'en-GB');
  // the cutoff is the first moment that no longer counts → show the second before it
  const cutoffText = $derived(
    data
      ? new Date(new Date(data.cutoff).getTime() - 1000).toLocaleString(locale, {
          timeZone: 'Europe/Bratislava', dateStyle: 'medium', timeStyle: 'medium'
        })
      : ''
  );
  const fmt = (n: number) => Math.round(n).toLocaleString(locale);

  const screen = $derived(step === 0 ? 'last' : step <= 4 ? 'podium' : 'classes');
  const shownPlaces = $derived(Math.max(0, Math.min(3, step - 1))); // podium places revealed
  const order = [3, 2, 1];

  // podium slots 1–3 (ties: rank() gives the same place, we show the first 3 rows)
  const winners = $derived([0, 1, 2].map((i) => data?.top[i] ?? null));
  // classes in a fixed alphabetical order, so the order does not give the winner away
  const classes = $derived([...(data?.classes ?? [])].sort((a, b) => a.name.localeCompare(b.name)));
  const maxPoints = $derived(Math.max(1, ...classes.map((c) => c.points)));
  const topPoints = $derived(Math.max(...classes.map((c) => c.points), 0));
  const TEAM_COLORS = ['#22c55e', '#3b82f6', '#a855f7', '#f97316', '#ec4899', '#14b8a6'];

  const title = $derived(
    screen === 'last' ? t('final.last_title') : screen === 'podium' ? t('final.top_title') : t('final.cls_title')
  );
  const sub = $derived(
    t(screen === 'last' ? 'final.last_sub' : screen === 'podium' ? 'final.top_sub' : 'final.cls_sub', { d: cutoffText })
  );

  function splitTime(s: string) {
    const tm = s.split(' ')[1] ?? s;
    const [hms, ms] = tm.split('.');
    return { hms, ms: ms ? ms.slice(0, 3) : '' };
  }

  // ---------- class count-up
  let raf = 0;
  function countUp() {
    cancelAnimationFrame(raf);
    counting = true;
    crowned = false;
    const t0 = performance.now(), dur = 4000;
    const tick = (now: number) => {
      const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3);
      counts = classes.map((c) => c.points * e);
      if (k < 1) { raf = requestAnimationFrame(tick); return; }
      counting = false;
      crowned = true;
      requestAnimationFrame(() => {
        for (const el of document.querySelectorAll('.fr .team.win .tname')) burstAt(el, 300, GOLD);
      });
    };
    raf = requestAnimationFrame(tick);
  }

  function go(s: number) {
    cancelAnimationFrame(raf);
    counting = false;
    crowned = s >= 6;
    counts = classes.map((c) => (s >= 6 ? c.points : 0));
    step = Math.max(0, Math.min(6, s));
  }
  function next() {
    if (!data || step >= 6) return;
    go(step + 1);
    if (step >= 2 && step <= 4) {
      const place = order[step - 2];
      requestAnimationFrame(() =>
        burstAt(document.querySelector(`.fr .p${place} .medal`), place === 1 ? 260 : 90, COLORS[place]));
    }
    if (step === 6) countUp();
  }

  function fullscreen() {
    if (document.fullscreenElement) document.exitFullscreen();
    else root?.requestFullscreen?.();
  }
  function close() {
    if (document.fullscreenElement) document.exitFullscreen();
    onClose();
  }

  function onKey(e: KeyboardEvent) {
    const k = e.key.toLowerCase();
    if (e.key === ' ' || e.key === 'ArrowRight' || e.key === 'Enter' || e.key === 'PageDown') { e.preventDefault(); next(); }
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') go(step - 1);
    else if (e.key === 'Escape' && !document.fullscreenElement) close();
    else if (k === 'f') fullscreen();
    else if (k === '1') go(0);
    else if (k === '2') go(1);
    else if (k === '3') go(5);
  }

  // ---------- confetti
  let root = $state<HTMLElement>();
  let canvas = $state<HTMLCanvasElement>();
  type Part = { x: number; y: number; vx: number; vy: number; w: number; h: number; r: number; vr: number; life: number; c: string };
  let parts: Part[] = [];
  let confettiRaf = 0;
  const GOLD = ['#fbbf24', '#fde68a', '#22c55e', '#ffffff', '#f59e0b'];
  const COLORS: Record<number, string[]> = {
    1: GOLD, 2: ['#e2e8f0', '#94a3b8', '#22c55e', '#ffffff'], 3: ['#f0a46b', '#b45309', '#22c55e', '#ffffff']
  };
  function resize() {
    if (!canvas) return;
    canvas.width = innerWidth * devicePixelRatio;
    canvas.height = innerHeight * devicePixelRatio;
  }
  function burstAt(el: Element | null, n: number, colors: string[]) {
    if (!el) return;
    const r = el.getBoundingClientRect(), d = devicePixelRatio;
    const x0 = (r.left + r.width / 2) * d, y0 = (r.top + r.height / 2) * d;
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2, s = (4 + Math.random() * 10) * d;
      parts.push({ x: x0, y: y0, vx: Math.cos(a) * s, vy: Math.sin(a) * s - 8 * d,
        w: (6 + Math.random() * 8) * d, h: (4 + Math.random() * 6) * d,
        r: Math.random() * 6, vr: (Math.random() - 0.5) * 0.4, life: 160 + Math.random() * 80, c: colors[i % colors.length] });
    }
  }
  function confettiTick() {
    const cx = canvas?.getContext('2d');
    if (cx && canvas) {
      cx.clearRect(0, 0, canvas.width, canvas.height);
      parts = parts.filter((p) => p.life > 0 && p.y < canvas!.height + 50);
      for (const p of parts) {
        p.vy += 0.25 * devicePixelRatio; p.vx *= 0.99; p.x += p.vx; p.y += p.vy; p.r += p.vr; p.life--;
        cx.save(); cx.translate(p.x, p.y); cx.rotate(p.r); cx.globalAlpha = Math.min(1, p.life / 40);
        cx.fillStyle = p.c; cx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h); cx.restore();
      }
    }
    confettiRaf = requestAnimationFrame(confettiTick);
  }

  onMount(() => {
    document.body.style.overflow = 'hidden';
    resize();
    addEventListener('resize', resize);
    confettiTick();
    load();
  });
  onDestroy(() => {
    document.body.style.overflow = '';
    removeEventListener('resize', resize);
    cancelAnimationFrame(raf);
    cancelAnimationFrame(confettiRaf);
  });
</script>

<svelte:window onkeydown={onKey} />

<div class="fr" bind:this={root}>
  <canvas bind:this={canvas}></canvas>

  <div class="tools">
    <button onclick={() => go(step - 1)} title={t('final.back')} aria-label={t('final.back')}>◀</button>
    <button onclick={load} title={t('final.refresh')} aria-label={t('final.refresh')}>↻</button>
    <button onclick={fullscreen} title={t('final.fullscreen')} aria-label={t('final.fullscreen')}>⛶</button>
    <button onclick={close} title={t('final.close')} aria-label={t('final.close')}>✕</button>
  </div>

  <header>
    <div class="brand"><Logo size={64} /><span>Quizilla</span></div>
    <h1>{title}</h1>
    {#if data}<div class="sub">{sub}</div>{/if}
    {#if data && !data.is_final}<div class="preview">{t('final.preview')}</div>{/if}
  </header>

  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div class="stage" onclick={next}>
    {#if error}
      <div class="none">{error}</div>
    {:else if !data}
      <div class="spinner"></div>
    {:else if screen === 'last'}
      <ol class="last">
        {#each data.last as r, i (r.name + r.answered_at)}
          {@const tm = splitTime(r.answered_at)}
          <li style="animation-delay:{(data.last.length - 1 - i) * 0.18}s">
            <span class="n">{i + 1}.</span>
            <span class="time">{tm.hms}{#if tm.ms}<small>.{tm.ms}</small>{/if}</span>
            <span class="lname">{r.name}</span>
            <span class="cls">{r.class}</span>
          </li>
        {:else}
          <li class="none">{t('final.none')}</li>
        {/each}
      </ol>
    {:else if screen === 'podium'}
      <div class="podium">
        {#each [2, 1, 3] as place (place)}
          {@const w = winners[place - 1]}
          {@const first = w ? data.top.findIndex((x) => x.points === w.points) : -1}
          <div class="place p{place}" class:revealed={order.indexOf(place) < shownPlaces}>
            <div class="who">
              <div class="medal">{place}</div>
              <div class="name">{w?.name ?? '—'}</div>
              {#if w}<div class="cls">{w.class}</div>{/if}
              {#if w}<div class="pts">{fmt(w.points)}<small>{t('final.pts')}</small></div>{/if}
            </div>
            <div class="step">
              {#if w && first >= 0 && first < place - 1}{first + 1}<span class="tie">=</span>{:else}{place}{/if}
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="teams">
        {#each classes as c, i (c.name)}
          {@const v = counts[i] ?? 0}
          <div class="team" class:win={crowned && c.points === topPoints} style="--c:{TEAM_COLORS[i % TEAM_COLORS.length]}">
            <div class="tname">{c.name} <span class="trophy">🏆</span></div>
            <div class="track">
              <div class="fill" style="width:{(100 * v) / maxPoints}%"></div>
              <div class="tpts">
                {#if counting || crowned}{fmt(v)}<small>{t('final.pts')}</small>{:else}?{/if}
              </div>
            </div>
            <div class="tmeta">{crowned ? t('final.players', { p: c.players, s: c.students }) : ' '}</div>
          </div>
        {:else}
          <div class="none">{t('final.none')}</div>
        {/each}
      </div>
    {/if}
  </div>

  <div class="dots">
    {#each ['last', 'podium', 'classes'] as s (s)}<i class:on={s === screen}></i>{/each}
  </div>
  <div class="hint">{t('final.hint')}</div>
  <footer></footer>
</div>

<style>
  .fr {
    --gold: #fbbf24; --gold2: #d97706; --silver: #e2e8f0; --silver2: #94a3b8; --bronze: #f0a46b; --bronze2: #b45309;
    --fr-muted: #a9bdb1;
    position: fixed; inset: 0; z-index: 1000; display: flex; flex-direction: column; align-items: center;
    color: #f2f7f4; overflow: hidden; user-select: none;
    background: radial-gradient(ellipse at 50% 0%, #1d4d31 0%, #0f2a1b 35%, #06130c 80%);
    font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  }
  canvas { position: fixed; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 5; }

  .tools { position: fixed; right: 12px; top: 12px; display: flex; gap: 8px; z-index: 10; opacity: .35; transition: opacity .2s; }
  .tools:hover { opacity: 1; }
  .tools button {
    width: 40px; height: 40px; border-radius: 10px; border: 1px solid rgba(255,255,255,.25);
    background: rgba(0,0,0,.35); color: #fff; font-size: 17px; cursor: pointer;
  }

  header { text-align: center; padding: clamp(12px, 3vh, 36px) 16px 0; z-index: 2; }
  .brand { display: inline-flex; align-items: center; gap: 12px; }
  .brand :global(img) { width: clamp(40px, 6.5vh, 72px); height: auto; filter: drop-shadow(0 6px 18px rgba(0,0,0,.5)); }
  .brand span { font-weight: 800; font-size: clamp(24px, 4.5vh, 48px); letter-spacing: .5px; }
  h1 {
    margin: clamp(4px, 1vh, 10px) 0 4px; font-size: clamp(26px, 6vh, 66px); font-weight: 900;
    background: linear-gradient(180deg, #fff3c4, var(--gold) 55%, var(--gold2));
    -webkit-background-clip: text; background-clip: text; color: transparent;
    letter-spacing: 1px; text-transform: uppercase;
  }
  .sub { color: var(--fr-muted); font-size: clamp(13px, 2.2vh, 22px); }
  .preview {
    display: inline-block; margin-top: 8px; padding: 4px 12px; border-radius: 999px; font-size: 13px; font-weight: 700;
    background: rgba(251,191,36,.15); color: var(--gold); border: 1px solid rgba(251,191,36,.4);
  }

  .stage { flex: 1; width: 100%; min-height: 0; display: flex; justify-content: center; z-index: 2; cursor: pointer; }
  .stage > * { animation: fadeUp .5s ease both; }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } }
  .none { align-self: center; text-align: center; color: var(--fr-muted); font-size: 20px; padding: 24px; }
  .spinner { align-self: center; }

  .cls {
    display: inline-block; padding: 3px 12px; border-radius: 999px; white-space: nowrap;
    background: rgba(34,197,94,.18); color: #86efac; font-weight: 700; font-size: clamp(12px, 2vh, 20px);
  }

  /* last 10 */
  .last {
    list-style: none; margin: 0; width: 100%; max-width: 1000px; padding: clamp(8px, 2.5vh, 24px) 16px 48px;
    display: flex; flex-direction: column; justify-content: center; gap: clamp(4px, .9vh, 10px);
  }
  .last li {
    display: grid; grid-template-columns: 2.4em 7.6em 1fr auto; align-items: center; gap: 14px;
    padding: clamp(4px, .9vh, 10px) 18px; border-radius: 12px; font-size: clamp(14px, 2.4vh, 26px);
    background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
    opacity: 0; transform: translateX(-30px); animation: slideIn .5s ease forwards;
  }
  .last li.none { display: block; opacity: 1; transform: none; animation: none; }
  .last li:first-child { background: rgba(251,191,36,.14); border-color: rgba(251,191,36,.5); }
  .last .n { color: var(--fr-muted); font-weight: 800; text-align: right; }
  .last .time { font-weight: 900; color: var(--gold); font-variant-numeric: tabular-nums; white-space: nowrap; }
  .last .time small { font-size: .7em; opacity: .85; }
  .last .lname { font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  @keyframes slideIn { to { opacity: 1; transform: none; } }

  /* podium */
  .podium {
    width: 100%; max-width: 1200px; display: flex; align-items: flex-end; justify-content: center;
    gap: clamp(8px, 2vw, 28px); padding: 0 16px;
  }
  .place { flex: 1 1 0; max-width: 340px; display: flex; flex-direction: column; align-items: center; min-width: 0; }
  .who {
    text-align: center; padding: 0 4px 14px; opacity: 0; transform: translateY(24px) scale(.9); width: 100%;
    transition: opacity .6s ease, transform .6s cubic-bezier(.2,1.4,.4,1);
  }
  .revealed .who { opacity: 1; transform: none; }
  .medal {
    width: clamp(56px, 10vh, 110px); height: clamp(56px, 10vh, 110px); border-radius: 50%;
    display: grid; place-items: center; margin: 0 auto 10px; font-weight: 900;
    font-size: clamp(26px, 5vh, 52px); color: #2b1a02; position: relative;
    box-shadow: 0 8px 24px rgba(0,0,0,.45), inset 0 -6px 0 rgba(0,0,0,.18), inset 0 4px 0 rgba(255,255,255,.45);
  }
  .p1 .medal { background: radial-gradient(circle at 35% 30%, #fff7d1, var(--gold) 50%, var(--gold2)); }
  .p2 .medal { background: radial-gradient(circle at 35% 30%, #ffffff, var(--silver) 50%, var(--silver2)); }
  .p3 .medal { background: radial-gradient(circle at 35% 30%, #ffe2c9, var(--bronze) 50%, var(--bronze2)); }
  .p1 .medal::before { content: '👑'; position: absolute; top: -0.85em; font-size: .8em; }
  .name { font-weight: 800; font-size: clamp(18px, 3.6vh, 40px); line-height: 1.15; overflow-wrap: break-word; }
  .p1 .name { font-size: clamp(22px, 4.6vh, 50px); }
  .who .cls { margin-top: 6px; }
  .pts { margin-top: 8px; font-weight: 900; font-size: clamp(20px, 4vh, 44px); color: var(--gold); font-variant-numeric: tabular-nums; }
  .pts small { font-size: .5em; font-weight: 700; color: var(--fr-muted); margin-left: 4px; }
  .step {
    width: 100%; border-radius: 14px 14px 0 0; display: grid; place-items: start center;
    padding-top: clamp(8px, 2vh, 20px); font-weight: 900; font-size: clamp(44px, 10vh, 120px);
    color: rgba(255,255,255,.92); text-shadow: 0 4px 0 rgba(0,0,0,.2);
    box-shadow: inset 0 6px 0 rgba(255,255,255,.25), 0 -4px 30px rgba(0,0,0,.25);
  }
  .p1 .step { height: 32vh; background: linear-gradient(180deg, #fcd34d, var(--gold2)); }
  .p2 .step { height: 23vh; background: linear-gradient(180deg, #e2e8f0, #64748b); }
  .p3 .step { height: 16vh; background: linear-gradient(180deg, #f6b98a, var(--bronze2)); }
  .tie { font-size: .45em; display: block; opacity: .85; }

  /* classes */
  .teams {
    width: 100%; max-width: 1100px; padding: clamp(10px, 3vh, 30px) 16px 56px;
    display: grid; grid-template-columns: auto 1fr; align-content: center; align-items: center; column-gap: 18px; row-gap: 4px;
  }
  .team { display: contents; }
  .tname {
    font-weight: 900; font-size: clamp(20px, 4.5vh, 48px); text-align: right;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .track {
    position: relative; height: clamp(44px, 10vh, 110px); border-radius: 16px; overflow: hidden;
    background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.12);
  }
  .fill { position: absolute; inset: 0 auto 0 0; border-radius: 16px; background: var(--c); box-shadow: inset 0 6px 0 rgba(255,255,255,.25); }
  .tpts {
    position: absolute; right: 18px; top: 50%; transform: translateY(-50%); font-weight: 900;
    font-size: clamp(22px, 5vh, 54px); font-variant-numeric: tabular-nums; text-shadow: 0 2px 8px rgba(0,0,0,.6);
  }
  .tpts small { font-size: .45em; color: var(--fr-muted); margin-left: 4px; }
  .tmeta { grid-column: 2; color: var(--fr-muted); font-size: clamp(12px, 1.8vh, 18px); margin-bottom: clamp(10px, 3vh, 32px); }
  .trophy { opacity: 0; transition: opacity .5s; }
  .team.win .trophy { opacity: 1; }
  .team.win .tname { color: var(--gold); }
  .team.win .track { border-color: var(--gold); box-shadow: 0 0 0 3px rgba(251,191,36,.35), 0 0 40px rgba(251,191,36,.35); }

  .dots { position: fixed; left: 50%; bottom: 36px; transform: translateX(-50%); display: flex; gap: 8px; z-index: 3; opacity: .6; }
  .dots i { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,.3); }
  .dots i.on { background: var(--gold); }
  .hint {
    position: fixed; left: 0; right: 0; bottom: 14px; text-align: center; z-index: 3;
    color: var(--fr-muted); font-size: 12px; opacity: .5; padding: 0 16px;
  }
  footer { width: 100%; height: 8px; flex: none; z-index: 2; background: linear-gradient(90deg, #15803d, #22c55e, #15803d); }

  @media (max-width: 600px) {
    .name, .p1 .name { font-size: clamp(14px, 4.4vw, 22px); }
    .p1 .step { height: 24vh; } .p2 .step { height: 17vh; } .p3 .step { height: 12vh; }
    .last li { grid-template-columns: 1.6em 6.4em 1fr; gap: 8px; padding: 6px 10px; font-size: 14px; }
    .last li .cls { display: none; }
    .teams { grid-template-columns: 1fr; } .tname { text-align: left; } .tmeta { grid-column: 1; }
    .hint { display: none; }
  }
</style>
