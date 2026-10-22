<script lang="ts">
  import TopBar from '../components/TopBar.svelte';
  import Logo from '../components/Logo.svelte';
  import Icon from '../components/Icon.svelte';
  import { session, setStudent } from '../lib/session.svelte';
  import { i18n, setLang, t } from '../lib/i18n.svelte';

  function logout() {
    if (confirm(t('profile.logout.confirm'))) {
      setStudent(null);
      location.hash = '#/';
    }
  }
</script>

<TopBar title={t('profile.title')} />

<main class="page stack">
  {#if session.student}
    <section class="card who">
      <Logo size={48} />
      <div>
        <h2>{session.student.name}</h2>
        <div class="muted small">{session.student.email}</div>
        <div class="pill ok cls">{t('home.class', { name: session.student.class_name })}</div>
      </div>
    </section>
    <p class="small muted">{t('profile.class_note')}</p>

    <a class="card tappable stats-link" href="#/stats">
      <span class="ico"><Icon name="chart" /></span>
      <span class="grow">
        <strong>{t('stats.open')}</strong>
        <span class="muted small">{t('stats.open_info')}</span>
      </span>
      <Icon name="chevron" size={18} />
    </a>

    <section class="card stack">
      <h3>{t('profile.language')}</h3>
      <div class="segmented">
        <button class:active={i18n.lang === 'sk'} onclick={() => setLang('sk')}>Slovensky</button>
        <button class:active={i18n.lang === 'en'} onclick={() => setLang('en')}>English</button>
      </div>
    </section>

    <button class="btn danger block" onclick={logout}>{t('profile.logout')}</button>
    <p class="small muted center">Quizilla v{__APP_VERSION__}</p>
  {/if}
</main>

<style>
  .who { display: flex; gap: 14px; align-items: center; }
  .who h2 { margin-bottom: 2px; }
  .cls { margin-top: 8px; }
  .stats-link { display: flex !important; align-items: center; gap: 12px; text-decoration: none; color: inherit; }
  .stats-link .grow { flex: 1; display: flex; flex-direction: column; }
  .stats-link .ico {
    width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center;
    background: var(--accent-soft); color: var(--accent-strong); flex: none;
  }
</style>
