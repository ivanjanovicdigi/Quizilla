<script lang="ts">
  import TopBar from '../components/TopBar.svelte';
  import ClassBoard from '../components/ClassBoard.svelte';
  import StatsPanel from '../components/StatsPanel.svelte';
  import { session } from '../lib/session.svelte';
  import { t } from '../lib/i18n.svelte';

  // Global class leaderboard (ClassBoard). Students also get a "Mine" tab with their own
  // statistics. Opens on "Class" every time.
  let tab = $state<'class' | 'mine'>('class');
</script>

<TopBar title={t('nav.leaderboard')} />

<main class="page stack">
  {#if session.student}
    <div class="segmented">
      <button class:active={tab === 'class'} onclick={() => (tab = 'class')}>{t('lb.tab_class')}</button>
      <button class:active={tab === 'mine'} onclick={() => (tab = 'mine')}>{t('lb.tab_mine')}</button>
    </div>
  {/if}

  {#if tab === 'mine' && session.student}
    <StatsPanel />
  {:else}
    <ClassBoard myClassId={session.student?.class_id ?? null} />
  {/if}
</main>
