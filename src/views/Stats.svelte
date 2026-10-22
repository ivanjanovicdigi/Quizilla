<script lang="ts">
  import TopBar from '../components/TopBar.svelte';
  import StatsPanel from '../components/StatsPanel.svelte';
  import { t } from '../lib/i18n.svelte';
</script>

<TopBar title={t('stats.title')} back="#/profile" />

<main class="page stack">
  <StatsPanel />
</main>
