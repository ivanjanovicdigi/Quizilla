<script lang="ts">
  let { size = 40 }: { size?: number } = $props();
</script>

<!-- Original mark: rounded green tile with a spiky "Q" -->
<svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
  <rect width="64" height="64" rx="16" fill="#16a34a" />
  <path d="M20 14l4 6M32 10v7M44 14l-4 6" stroke="#bbf7d0" stroke-width="4" stroke-linecap="round" />
  <circle cx="32" cy="36" r="14" fill="none" stroke="#fff" stroke-width="6" />
  <path d="M38 42l9 9" stroke="#fff" stroke-width="6" stroke-linecap="round" />
</svg>
