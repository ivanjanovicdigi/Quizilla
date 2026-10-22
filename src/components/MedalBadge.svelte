<script module lang="ts">
  import type { MedalKey } from '../lib/types';

  /** Topic medal image in public/badges: bronze / silver / gold; topic Grand Master = crown. */
  export function medalImage(medal: MedalKey): string {
    const file = medal === 'grand_master' ? 'rank-grand-master' : `medal-${medal}`;
    return `${import.meta.env.BASE_URL}badges/${file}.png`;
  }
</script>

<script lang="ts">
  import { t } from '../lib/i18n.svelte';

  // No medal yet → a faint grey bronze medal, so every topic shows its medal slot.
  let { medal, size = 44 }: { medal: MedalKey | null | undefined; size?: number } = $props();
</script>

<img
  class="medal"
  class:empty={!medal}
  src={medalImage(medal ?? 'bronze')}
  alt={t(`medal.${medal ?? 'none'}`)}
  title={t(`medal.${medal ?? 'none'}`)}
  width={size}
  height={size} />

<style>
  .medal { display: block; flex: none; object-fit: contain; }
  .empty { filter: grayscale(1); opacity: .25; }
</style>
