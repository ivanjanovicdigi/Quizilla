<script lang="ts">
  import { renderBlock, renderShort } from '../lib/rich';
  let { text, short = false }: { text: string; short?: boolean } = $props();
  // Safe: renderer escapes all input before adding its own markup.
  const html = $derived(short ? renderShort(text) : renderBlock(text));
</script>

{#if short}
  <span class="rich">{@html html}</span>
{:else}
  <div class="rich">{@html html}</div>
{/if}
