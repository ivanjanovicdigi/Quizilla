<script lang="ts">
  import TopBar from '../components/TopBar.svelte';
  import StatsPanel from '../components/StatsPanel.svelte';
  import ResultsTomorrow from '../components/ResultsTomorrow.svelte';
  import { scoresHidden } from '../lib/freeze.svelte';
  import { session } from '../lib/session.svelte';
  import { t } from '../lib/i18n.svelte';

  // Personal score only: class (team) totals are hidden on purpose (ClassBoard is admin-only now).
  // Guests have no saved score, so they see a short note.
</script>

<TopBar title={t('nav.leaderboard')} />

<main class="page stack">
  {#if scoresHidden()}
    <ResultsTomorrow />
  {:else if session.student}
    <StatsPanel />
  {:else}
    <p class="muted center">{t('lb.guest')}</p>
  {/if}
</main>
