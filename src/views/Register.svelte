<script lang="ts">
  import { onMount } from 'svelte';
  import Logo from '../components/Logo.svelte';
  import { api, ApiError, emailDomain } from '../lib/api';
  import { setStudent } from '../lib/session.svelte';
  import { errorText, i18n, setLang, t } from '../lib/i18n.svelte';
  import type { ClassInfo } from '../lib/types';

  let classes = $state<ClassInfo[]>([]);
  let name = $state('');
  let email = $state('');
  let classId = $state<number | ''>('');
  let busy = $state(false);
  let error = $state('');
  let loadError = $state('');

  async function loadClasses() {
    loadError = '';
    try {
      classes = await api.listClasses();
    } catch (e) {
      loadError = errorText(e instanceof ApiError ? e.code : 'server');
    }
  }
  onMount(loadClasses);

  function validate(): string {
    if (name.trim().length < 2) return errorText('invalid_name');
    const e = email.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e) || !e.endsWith('@' + emailDomain))
      return errorText('invalid_email', { domain: emailDomain });
    if (classId === '') return errorText('invalid_class');
    return '';
  }

  async function submit(ev: SubmitEvent) {
    ev.preventDefault();
    error = validate();
    if (error) return;
    busy = true;
    try {
      const s = await api.register(email.trim(), name.trim(), Number(classId));
      setStudent(s);
      location.hash = '#/';
    } catch (e) {
      error = errorText(e instanceof ApiError ? e.code : 'server', { domain: emailDomain });
    } finally {
      busy = false;
    }
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
    <h1>{t('reg.title')}</h1>
    <p class="muted">{t('app.tagline')}</p>
  </div>

  <form class="card stack" onsubmit={submit} novalidate>
    <label class="field">
      <span>{t('reg.name')}</span>
      <input bind:value={name} autocomplete="name" placeholder={t('reg.name.ph')} maxlength="80" />
    </label>
    <label class="field">
      <span>{t('reg.email')}</span>
      <input
        bind:value={email}
        type="email"
        inputmode="email"
        autocomplete="email"
        autocapitalize="off"
        spellcheck="false"
        placeholder={'meno.priezvisko@' + emailDomain} />
    </label>
    <label class="field">
      <span>{t('reg.class')}</span>
      <select bind:value={classId}>
        <option value="" disabled>{t('reg.class.ph')}</option>
        {#each classes as c (c.id)}
          <option value={c.id}>{c.name}</option>
        {/each}
      </select>
    </label>

    {#if loadError}
      <div class="error">{loadError} <button type="button" class="btn small secondary" onclick={loadClasses}>{t('common.retry')}</button></div>
    {/if}
    {#if error}<div class="error" role="alert">{error}</div>{/if}

    <button class="btn block" type="submit" disabled={busy}>{busy ? t('common.loading') : t('reg.submit')}</button>
    <p class="small muted">{t('reg.note')}</p>
    <p class="small muted">{t('reg.again')}</p>
  </form>
</main>

<style>
  .reg { padding-top: calc(16px + env(safe-area-inset-top)); padding-bottom: 32px; }
  .lang { display: flex; justify-content: flex-end; }
  .lang .segmented { width: 220px; }
  .hero { text-align: center; margin: 24px 0 20px; }
  .hero h1 { margin: 12px 0 6px; font-size: 1.6rem; }
</style>
