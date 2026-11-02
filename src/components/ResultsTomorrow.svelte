<script lang="ts">
  import Icon from './Icon.svelte';
  import { t } from '../lib/i18n.svelte';

  // Shown instead of scores during the freeze before the final results (lib/freeze.svelte.ts).
</script>

<section class="card tomorrow center stack">
  <span class="cup"><Icon name="trophy" size={40} /></span>
  <h2>{t('freeze.title')}</h2>
  <p class="muted small">{t('freeze.info')}</p>
</section>

<style>
  .tomorrow { padding: 24px 16px; align-items: center; }
  .cup {
    display: inline-flex; align-items: center; justify-content: center;
    width: 72px; height: 72px; border-radius: 50%;
    background: var(--accent-soft); color: var(--gold);
  }
</style>
