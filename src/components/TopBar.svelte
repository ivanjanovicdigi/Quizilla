<script lang="ts">
  import Icon from './Icon.svelte';
  import { i18n, setLang, t } from '../lib/i18n.svelte';

  let { title = '', back = '' }: { title?: string; back?: string } = $props();
</script>

<header class="topbar">
  <div class="inner">
    {#if back}
      <a class="icon-btn" href={back} aria-label={t('common.back')}><Icon name="back" /></a>
    {/if}
    <h1 class="title">{title}</h1>
    <button
      class="lang"
      onclick={() => setLang(i18n.lang === 'sk' ? 'en' : 'sk')}
      aria-label="Language">
      <span class:active={i18n.lang === 'sk'}>SK</span>
      <span class:active={i18n.lang === 'en'}>EN</span>
    </button>
  </div>
</header>

<style>
  .topbar {
    position: sticky; top: 0; z-index: 10;
    background: color-mix(in srgb, var(--bg) 88%, transparent);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--border);
    padding-top: env(safe-area-inset-top);
  }
  .inner { max-width: 640px; margin: 0 auto; height: 56px; padding: 0 12px 0 16px; display: flex; align-items: center; gap: 8px; }
  .title { flex: 1; font-size: 1.1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .icon-btn { display: grid; place-items: center; width: 40px; height: 40px; margin-left: -8px; border-radius: 10px; color: var(--text); }
  .lang { display: flex; gap: 2px; padding: 3px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); cursor: pointer; }
  .lang span { padding: 2px 8px; border-radius: 7px; font-size: .8rem; font-weight: 700; color: var(--muted); }
  .lang span.active { background: var(--accent); color: var(--on-accent); }
</style>
