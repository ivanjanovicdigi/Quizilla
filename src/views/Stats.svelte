<script lang="ts">
  import TopBar from '../components/TopBar.svelte';
  import StatsPanel from '../components/StatsPanel.svelte';
  import ResultsTomorrow from '../components/ResultsTomorrow.svelte';
  import { scoresHidden } from '../lib/freeze.svelte';
  import { t } from '../lib/i18n.svelte';
</script>

<TopBar title={t('stats.title')} back="#/profile" />

<main class="page stack">
  {#if scoresHidden()}<ResultsTomorrow />{/if}
  <StatsPanel />
</main>
