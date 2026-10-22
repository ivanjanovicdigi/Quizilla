<script module lang="ts">
  import type { RankKey } from '../lib/types';

  /** Rank image in public/badges: Padawan = bronze, Jedi = silver, Master = gold, Grand Master = crown. */
  export function rankImage(rank: RankKey): string {
    return `${import.meta.env.BASE_URL}badges/rank-${rank.replace('_', '-')}.png`;
  }
</script>

<script lang="ts">
  import Icon from './Icon.svelte';
  import { t } from '../lib/i18n.svelte';

  let { rank, size = 22 }: { rank: RankKey | null; size?: number } = $props();
</script>

<span class="rank {rank ?? 'none'}" class:has-img={!!rank}>
  {#if rank}
    <img src={rankImage(rank)} alt="" width={size} height={size} />
  {:else}
    <Icon name="medal" size={14} />
  {/if}
  {rank ? t(`rank.${rank}`) : t('rank.none')}
</span>

<style>
  .rank {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 10px; border-radius: 999px; font-size: .8rem; font-weight: 700;
    background: var(--surface-2); color: var(--muted);
  }
  .has-img { padding-left: 3px; gap: 5px; }
  .rank img { display: block; flex: none; object-fit: contain; }
  .padawan { background: var(--accent-soft); color: var(--accent-strong); }
  .jedi { background: var(--info-soft); color: var(--info); }
  .master, .grand_master { background: var(--gold-soft); color: var(--gold); }
  .grand_master { box-shadow: inset 0 0 0 1.5px var(--gold); }
</style>
