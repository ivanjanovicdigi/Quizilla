<script lang="ts">
  // Tier badge image from public/badges/tier-<n>.svg (placeholders – replace the files with the real badges).
  let { tier, size = 48, locked = false }: { tier: number; size?: number; locked?: boolean } = $props();
  const src = $derived(`${import.meta.env.BASE_URL}badges/tier-${tier}.svg`);
</script>

<img class="tier-badge" class:locked {src} alt="" width={size} height={size} />

<style>
  .tier-badge { flex: none; display: block; object-fit: contain; }
  .locked { filter: grayscale(1); opacity: .45; }
</style>
