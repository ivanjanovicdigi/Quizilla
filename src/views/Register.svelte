<script lang="ts">
  import Logo from '../components/Logo.svelte';
  import { api, ApiError, emailDomain } from '../lib/api';
  import { setGuest, setStudent } from '../lib/session.svelte';
  import { resetGuest } from '../lib/guest';
  import { errorText, i18n, setLang, t } from '../lib/i18n.svelte';

  // Login with the school email only. The student must be in the roster (quiz.roster);
  // name and class come from there. The device remembers the student (session.svelte.ts).
  const TEXT = {
    sk: {
      title: 'Prihlásenie',
      email: 'Školský e-mail',
      submit: 'Prihlásiť sa',
      note: 'Zadaj svoj školský e-mail. Zariadenie si ťa zapamätá, takže nabudúce sa už prihlasovať nemusíš.',
      not_on_roster: 'Tento e-mail nie je v zozname žiakov. Skontroluj ho, prípadne sa obráť na učiteľa.'
    },
    en: {
      title: 'Log in',
      email: 'School email',
      submit: 'Log in',
      note: 'Enter your school email. This device will remember you, so you won’t have to log in next time.',
      not_on_roster: 'This email is not on the student list. Check it or ask your teacher.'
    }
  };
  const L = $derived(TEXT[i18n.lang === 'en' ? 'en' : 'sk']);

  let email = $state('');
  let busy = $state(false);
  let error = $state('');

  function message(code: string): string {
    return code === 'not_on_roster' ? L.not_on_roster : errorText(code, { domain: emailDomain });
  }

  async function submit(ev: SubmitEvent) {
    ev.preventDefault();
    error = '';
    const e = email.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e) || !e.endsWith('@' + emailDomain)) {
      error = message('invalid_email');
      return;
    }
    busy = true;
    try {
      const s = await api.login(e);
      setStudent(s);
      location.hash = '#/';
    } catch (err) {
      error = message(err instanceof ApiError ? err.code : 'server');
    } finally {
      busy = false;
    }
  }

  function tryAsGuest() {
    resetGuest();
    setGuest(true);
    location.hash = '#/';
  }
</script>

<main class="page reg">
  <div class="lang">
    <div class="segmented">
      <button class:active={i18n.lang === 'sk'} onclick={() => setLang('sk')}>Slovensky</button>
      <button class:active={i18n.lang === 'en'} onclick={() => setLang('en')}>English</button>
    </div>
  </div>

  <div class="hero">
    <Logo size={72} />
    <h1>{L.title}</h1>
    <p class="muted">{t('app.tagline')}</p>
  </div>

  <form class="card stack" onsubmit={submit} novalidate>
    <label class="field">
      <span>{L.email}</span>
      <input
        bind:value={email}
        type="email"
        inputmode="email"
        autocomplete="email"
        autocapitalize="off"
        spellcheck="false"
        enterkeyhint="go"
        placeholder={'meno.priezvisko@' + emailDomain} />
    </label>

    {#if error}<div class="error" role="alert">{error}</div>{/if}

    <button class="btn block" type="submit" disabled={busy}>{busy ? t('common.loading') : L.submit}</button>
    <p class="small muted">{L.note}</p>
  </form>

  <section class="guest stack">
    <button class="btn block secondary" type="button" onclick={tryAsGuest}>{t('guest.try')}</button>
    <p class="small muted center">{t('guest.try_info')}</p>
  </section>
</main>

<style>
  .reg { padding-top: calc(16px + env(safe-area-inset-top)); padding-bottom: 32px; }
  .lang { display: flex; justify-content: flex-end; }
  .lang .segmented { width: 220px; }
  .hero { text-align: center; margin: 24px 0 20px; }
  .hero h1 { margin: 12px 0 6px; font-size: 1.6rem; }
  .guest { margin-top: 20px; }
  .guest p { margin: 0; }
</style>
