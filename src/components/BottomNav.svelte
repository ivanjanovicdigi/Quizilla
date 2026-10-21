<script lang="ts">
  import Icon from './Icon.svelte';
  import { router } from '../lib/router.svelte';
  import { t } from '../lib/i18n.svelte';

  const items = $derived([
    { href: '#/', icon: 'home', label: t('nav.home'), active: ['home', 'topic', 'quiz'].includes(router.route.name) },
    { href: '#/leaderboard', icon: 'trophy', label: t('nav.leaderboard'), active: router.route.name === 'leaderboard' },
    { href: '#/profile', icon: 'user', label: t('nav.profile'), active: router.route.name === 'profile' }
  ]);
</script>

<nav class="bottom">
  {#each items as it (it.href)}
    <a href={it.href} class:active={it.active}>
      <Icon name={it.icon} />
      <span>{it.label}</span>
    </a>
  {/each}
</nav>

<style>
  .bottom {
    position: fixed; left: 0; right: 0; bottom: 0; z-index: 10;
    display: flex; justify-content: center;
    background: var(--surface);
    border-top: 1px solid var(--border);
    padding-bottom: env(safe-area-inset-bottom);
  }
  a {
    flex: 1; max-width: 200px; display: flex; flex-direction: column; align-items: center; gap: 2px;
    padding: 8px 0 10px; color: var(--muted); text-decoration: none; font-size: .75rem; font-weight: 600;
  }
  a.active { color: var(--accent-strong); }
</style>
